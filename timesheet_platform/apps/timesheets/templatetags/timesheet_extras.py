from decimal import Decimal

from django import template


register = template.Library()


@register.filter
def get_item(mapping, key):
    return mapping.get(key, [])


@register.filter
def get_item_total(mapping, key):
    total = Decimal("0.00")
    for entry in mapping.get(key, []):
        total += entry.duration
    return total
