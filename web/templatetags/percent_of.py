from django import template

register = template.Library()


@register.filter()
def percent_of(amount, total):
    try:
        return '{:.1f}%'.format(amount / total * 100)
    except ZeroDivisionError:
        return None
