import sys

from registration import forms
from registration import models as rego
from registration.controllers import discount
from registration.controllers.cart import CartController
from registration.controllers.credit_note import CreditNoteController
from registration.controllers.invoice import InvoiceController
from registration.controllers.product import ProductController
from registration.exceptions import CartValidationError

from collections import namedtuple

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render


GuidedRegistrationSection = namedtuple(
    "GuidedRegistrationSection",
    (
        "title",
        "discounts",
        "description",
        "form",
    )
)
GuidedRegistrationSection.__new__.__defaults__ = (
    (None,) * len(GuidedRegistrationSection._fields)
)


def get_form(name):
    dot = name.rindex(".")
    mod_name, form_name = name[:dot], name[dot + 1:]
    __import__(mod_name)
    return getattr(sys.modules[mod_name], form_name)


@login_required
def guided_registration(request, page_id=0):
    ''' Goes through the registration process in order,
    making sure user sees all valid categories.

    WORK IN PROGRESS: the finalised version of this view will allow
    grouping of categories into a specific page. Currently, it just goes
    through each category one by one
    '''

    SESSION_KEY = "guided_registration_categories"
    ASK_FOR_PROFILE = 777  # Magic number. Meh.

    next_step = redirect("guided_registration")

    sections = []

    attendee = rego.Attendee.get_instance(request.user)

    if attendee.completed_registration:
        return render(
            request,
            "registration/guided_registration_complete.html",
            {},
        )

    # Step 1: Fill in a badge and collect a voucher code
    try:
        profile = attendee.attendeeprofilebase
    except ObjectDoesNotExist:
        profile = None

    # Figure out if we need to show the profile form and the voucher form
    show_profile_and_voucher = False
    if SESSION_KEY not in request.session:
        if not profile:
            show_profile_and_voucher = True
    else:
        if request.session[SESSION_KEY] == ASK_FOR_PROFILE:
            show_profile_and_voucher = True

    if show_profile_and_voucher:
        # Keep asking for the profile until everything passes.
        request.session[SESSION_KEY] = ASK_FOR_PROFILE

        voucher_form, voucher_handled = handle_voucher(request, "voucher")
        profile_form, profile_handled = handle_profile(request, "profile")

        voucher_section = GuidedRegistrationSection(
            title="Voucher Code",
            form=voucher_form,
        )

        profile_section = GuidedRegistrationSection(
            title="Profile and Personal Information",
            form=profile_form,
        )

        title = "Attendee information"
        current_step = 1
        sections.append(voucher_section)
        sections.append(profile_section)
    else:
        # We're selling products

        starting = attendee.guided_categories_complete.count() == 0

        # Get the next category
        cats = rego.Category.objects
        if SESSION_KEY in request.session:
            _cats = request.session[SESSION_KEY]
            cats = cats.filter(id__in=_cats)
        else:
            cats = cats.exclude(
                id__in=attendee.guided_categories_complete.all(),
            )

        cats = cats.order_by("order")

        request.session[SESSION_KEY] = []

        if starting:
            # Only display the first Category
            title = "Select ticket type"
            current_step = 2
            cats = [cats[0]]
        else:
            # Set title appropriately for remaining categories
            current_step = 3
            title = "Additional items"

        all_products = rego.Product.objects.filter(
            category__in=cats,
        ).select_related("category")

        available_products = set(ProductController.available_products(
            request.user,
            products=all_products,
        ))

        if len(available_products) == 0:
            # We've filled in every category
            attendee.completed_registration = True
            attendee.save()
            return next_step

        for category in cats:
            products = [
                i for i in available_products
                if i.category == category
            ]

            prefix = "category_" + str(category.id)
            p = handle_products(request, category, products, prefix)
            products_form, discounts, products_handled = p

            section = GuidedRegistrationSection(
                title=category.name,
                description=category.description,
                discounts=discounts,
                form=products_form,
            )

            if products:
                # This product category has items to show.
                sections.append(section)
                # Add this to the list of things to show if the form errors.
                request.session[SESSION_KEY].append(category.id)

                if request.method == "POST" and not products_form.errors:
                    # This is only saved if we pass each form with no errors,
                    # and if the form actually has products.
                    attendee.guided_categories_complete.add(category)

    if sections and request.method == "POST":
        for section in sections:
            if section.form.errors:
                break
        else:
            attendee.save()
            if SESSION_KEY in request.session:
                del request.session[SESSION_KEY]
            # We've successfully processed everything
            return next_step

    data = {
        "current_step": current_step,
        "sections": sections,
        "title": title,
        "total_steps": 3,
    }
    return render(request, "registration/guided_registration.html", data)


@login_required
def edit_profile(request):
    form, handled = handle_profile(request, "profile")

    if handled and not form.errors:
        messages.success(
            request,
            "Your attendee profile was updated.",
        )
        return redirect("dashboard")

    data = {
        "form": form,
    }
    return render(request, "registration/profile_form.html", data)


def handle_profile(request, prefix):
    ''' Returns a profile form instance, and a boolean which is true if the
    form was handled. '''
    attendee = rego.Attendee.get_instance(request.user)

    try:
        profile = attendee.attendeeprofilebase
        profile = rego.AttendeeProfileBase.objects.get_subclass(pk=profile.id)
    except ObjectDoesNotExist:
        profile = None

    ProfileForm = get_form(settings.ATTENDEE_PROFILE_FORM)

    # Load a pre-entered name from the speaker's profile,
    # if they have one.
    try:
        speaker_profile = request.user.speaker_profile
        speaker_name = speaker_profile.name
    except ObjectDoesNotExist:
        speaker_name = None

    name_field = ProfileForm.Meta.model.name_field()
    initial = {}
    if profile is None and name_field is not None:
        initial[name_field] = speaker_name

    form = ProfileForm(
        request.POST or None,
        initial=initial,
        instance=profile,
        prefix=prefix
    )

    handled = True if request.POST else False

    if request.POST and form.is_valid():
        form.instance.attendee = attendee
        form.save()

    return form, handled


@login_required
def product_category(request, category_id):
    ''' Registration selections form for a specific category of items.
    '''

    PRODUCTS_FORM_PREFIX = "products"
    VOUCHERS_FORM_PREFIX = "vouchers"

    # Handle the voucher form *before* listing products.
    # Products can change as vouchers are entered.
    v = handle_voucher(request, VOUCHERS_FORM_PREFIX)
    voucher_form, voucher_handled = v

    category_id = int(category_id)  # Routing is [0-9]+
    category = rego.Category.objects.get(pk=category_id)

    products = ProductController.available_products(
        request.user,
        category=category,
    )

    if not products:
        messages.warning(
            request,
            "There are no products available from category: " + category.name,
        )
        return redirect("dashboard")

    p = handle_products(request, category, products, PRODUCTS_FORM_PREFIX)
    products_form, discounts, products_handled = p

    if request.POST and not voucher_handled and not products_form.errors:
        # Only return to the dashboard if we didn't add a voucher code
        # and if there's no errors in the products form
        messages.success(
            request,
            "Your reservations have been updated.",
        )
        return redirect("dashboard")

    data = {
        "category": category,
        "discounts": discounts,
        "form": products_form,
        "voucher_form": voucher_form,
    }

    return render(request, "registration/product_category.html", data)


def handle_products(request, category, products, prefix):
    ''' Handles a products list form in the given request. Returns the
    form instance, the discounts applicable to this form, and whether the
    contents were handled. '''

    current_cart = CartController.for_user(request.user)

    ProductsForm = forms.ProductsForm(category, products)

    # Create initial data for each of products in category
    items = rego.ProductItem.objects.filter(
        product__in=products,
        cart=current_cart.cart,
    ).select_related("product")
    quantities = []
    seen = set()

    for item in items:
        quantities.append((item.product, item.quantity))
        seen.add(item.product)

    zeros = set(products) - seen
    for product in zeros:
        quantities.append((product, 0))

    products_form = ProductsForm(
        request.POST or None,
        product_quantities=quantities,
        prefix=prefix,
    )

    if request.method == "POST" and products_form.is_valid():
        if products_form.has_changed():
            set_quantities_from_products_form(products_form, current_cart)

        # If category is required, the user must have at least one
        # in an active+valid cart
        if category.required:
            carts = rego.Cart.objects.filter(user=request.user)
            items = rego.ProductItem.objects.filter(
                product__category=category,
                cart=carts,
            )
            if len(items) == 0:
                products_form.add_error(
                    None,
                    "You must have at least one item from this category",
                )
    handled = False if products_form.errors else True

    discounts = discount.available_discounts(request.user, [], products)

    return products_form, discounts, handled


def set_quantities_from_products_form(products_form, current_cart):

    quantities = list(products_form.product_quantities())

    pks = [i[0] for i in quantities]
    products = rego.Product.objects.filter(
        id__in=pks,
    ).select_related("category")

    product_quantities = [
        (products.get(pk=i[0]), i[1]) for i in quantities
    ]
    field_names = dict(
        (i[0][0], i[1][2]) for i in zip(product_quantities, quantities)
    )

    try:
        current_cart.set_quantities(product_quantities)
    except CartValidationError as ve:
        for ve_field in ve.error_list:
            product, message = ve_field.message
            if product in field_names:
                field = field_names[product]
            elif isinstance(product, rego.Product):
                continue
            else:
                field = None
            products_form.add_error(field, message)


def handle_voucher(request, prefix):
    ''' Handles a voucher form in the given request. Returns the voucher
    form instance, and whether the voucher code was handled. '''

    voucher_form = forms.VoucherForm(request.POST or None, prefix=prefix)
    current_cart = CartController.for_user(request.user)

    if (voucher_form.is_valid() and
            voucher_form.cleaned_data["voucher"].strip()):

        voucher = voucher_form.cleaned_data["voucher"]
        voucher = rego.Voucher.normalise_code(voucher)

        if len(current_cart.cart.vouchers.filter(code=voucher)) > 0:
            # This voucher has already been applied to this cart.
            # Do not apply code
            handled = False
        else:
            try:
                current_cart.apply_voucher(voucher)
            except Exception as e:
                voucher_form.add_error("voucher", e)
            handled = True
    else:
        handled = False

    return (voucher_form, handled)


@login_required
def checkout(request):
    ''' Runs checkout for the current cart of items, ideally generating an
    invoice. '''

    current_cart = CartController.for_user(request.user)

    if "fix_errors" in request.GET and request.GET["fix_errors"] == "true":
        current_cart.fix_simple_errors()

    try:
        current_invoice = InvoiceController.for_cart(current_cart.cart)
    except ValidationError as ve:
        return checkout_errors(request, ve)

    return redirect("invoice", current_invoice.invoice.id)


def checkout_errors(request, errors):

    error_list = []
    for error in errors.error_list:
        if isinstance(error, tuple):
            error = error[1]
        error_list.append(error)

    data = {
        "error_list": error_list,
    }

    return render(request, "registration/checkout_errors.html", data)


def invoice_access(request, access_code):
    ''' Redirects to the first unpaid invoice for the attendee that matches
    the given access code, if any. '''

    invoices = rego.Invoice.objects.filter(
        user__attendee__access_code=access_code,
        status=rego.Invoice.STATUS_UNPAID,
    ).order_by("issue_time")

    if not invoices:
        raise Http404()

    invoice = invoices[0]

    return redirect("invoice", invoice.id, access_code)


def invoice(request, invoice_id, access_code=None):
    ''' Displays an invoice for a given invoice id.
    This view is not authenticated, but it will only allow access to either:
    the user the invoice belongs to; staff; or a request made with the correct
    access code.
    '''

    invoice_id = int(invoice_id)
    inv = rego.Invoice.objects.get(pk=invoice_id)

    current_invoice = InvoiceController(inv)

    if not current_invoice.can_view(
            user=request.user,
            access_code=access_code,
            ):
        raise Http404()

    data = {
        "invoice": current_invoice.invoice,
    }

    return render(request, "registration/invoice.html", data)


@login_required
def manual_payment(request, invoice_id):
    ''' Allows staff to make manual payments or refunds on an invoice.'''

    FORM_PREFIX = "manual_payment"

    if not request.user.is_staff:
        raise Http404()

    invoice_id = int(invoice_id)
    inv = get_object_or_404(rego.Invoice, pk=invoice_id)
    current_invoice = InvoiceController(inv)

    form = forms.ManualPaymentForm(
        request.POST or None,
        prefix=FORM_PREFIX,
    )

    if request.POST and form.is_valid():
        form.instance.invoice = inv
        form.save()
        current_invoice.update_status()
        form = forms.ManualPaymentForm(prefix=FORM_PREFIX)

    data = {
        "invoice": inv,
        "form": form,
    }

    return render(request, "registration/manual_payment.html", data)


@login_required
def refund(request, invoice_id):
    ''' Allows staff to refund payments against an invoice and request a
    credit note.'''

    if not request.user.is_staff:
        raise Http404()

    invoice_id = int(invoice_id)
    inv = get_object_or_404(rego.Invoice, pk=invoice_id)
    current_invoice = InvoiceController(inv)

    try:
        current_invoice.refund()
        messages.success(request, "This invoice has been refunded.")
    except ValidationError as ve:
        messages.error(request, ve)

    return redirect("invoice", invoice_id)


def credit_note(request, note_id, access_code=None):
    ''' Displays an credit note for a given id.
    This view can only be seen by staff.
    '''

    if not request.user.is_staff:
        raise Http404()

    note_id = int(note_id)
    note = rego.CreditNote.objects.get(pk=note_id)

    current_note = CreditNoteController(note)

    apply_form = forms.ApplyCreditNoteForm(
        note.invoice.user,
        request.POST or None,
        prefix="apply_note"
    )

    refund_form = forms.ManualCreditNoteRefundForm(
        request.POST or None,
        prefix="refund_note"
    )

    if request.POST and apply_form.is_valid():
        inv_id = apply_form.cleaned_data["invoice"]
        invoice = rego.Invoice.objects.get(pk=inv_id)
        current_note.apply_to_invoice(invoice)
        messages.success(request,
            "Applied credit note %d to invoice." % note_id
        )
        return redirect("invoice", invoice.id)

    elif request.POST and refund_form.is_valid():
        refund_form.instance.entered_by = request.user
        refund_form.instance.parent = note
        refund_form.save()
        messages.success(request,
            "Applied manual refund to credit note."
        )
        return redirect("invoice", invoice.id)

    data = {
        "credit_note": current_note.credit_note,
        "apply_form": apply_form,
        "refund_form": refund_form,
    }

    return render(request, "registration/credit_note.html", data)
