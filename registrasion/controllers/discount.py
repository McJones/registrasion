import itertools

from conditions import ConditionController
from registration import models as rego

from django.db.models import Sum


class DiscountAndQuantity(object):
    def __init__(self, discount, clause, quantity):
        self.discount = discount
        self.clause = clause
        self.quantity = quantity

    def __repr__(self):
        return "(discount=%s, clause=%s, quantity=%d)" % (
            self.discount, self.clause, self.quantity,
        )


def available_discounts(user, categories, products):
    ''' Returns all discounts available to this user for the given categories
    and products. The discounts also list the available quantity for this user,
    not including products that are pending purchase. '''

    # discounts that match provided categories
    category_discounts = rego.DiscountForCategory.objects.filter(
        category__in=categories
    )
    # discounts that match provided products
    product_discounts = rego.DiscountForProduct.objects.filter(
        product__in=products
    )
    # discounts that match categories for provided products
    product_category_discounts = rego.DiscountForCategory.objects.filter(
        category__in=(product.category for product in products)
    )
    # (Not relevant: discounts that match products in provided categories)

    product_discounts = product_discounts.select_related(
        "product",
        "product__category",
    )

    all_category_discounts = category_discounts | product_category_discounts
    all_category_discounts = all_category_discounts.select_related(
        "category",
    )

    # The set of all potential discounts
    potential_discounts = set(itertools.chain(
        product_discounts,
        all_category_discounts,
    ))

    discounts = []

    # Markers so that we don't need to evaluate given conditions more than once
    accepted_discounts = set()
    failed_discounts = set()

    for discount in potential_discounts:
        real_discount = rego.DiscountBase.objects.get_subclass(
            pk=discount.discount.pk,
        )
        cond = ConditionController.for_condition(real_discount)

        # Count the past uses of the given discount item.
        # If this user has exceeded the limit for the clause, this clause
        # is not available any more.
        past_uses = rego.DiscountItem.objects.filter(
            cart__user=user,
            cart__active=False,  # Only past carts count
            cart__released=False,  # You can reuse refunded discounts
            discount=real_discount,
        )
        agg = past_uses.aggregate(Sum("quantity"))
        past_use_count = agg["quantity__sum"]
        if past_use_count is None:
            past_use_count = 0

        if past_use_count >= discount.quantity:
            # This clause has exceeded its use count
            pass
        elif real_discount not in failed_discounts:
            # This clause is still available
            if real_discount in accepted_discounts or cond.is_met(user):
                # This clause is valid for this user
                discounts.append(DiscountAndQuantity(
                    discount=real_discount,
                    clause=discount,
                    quantity=discount.quantity - past_use_count,
                ))
                accepted_discounts.add(real_discount)
            else:
                # This clause is not valid for this user
                failed_discounts.add(real_discount)
    return discounts
