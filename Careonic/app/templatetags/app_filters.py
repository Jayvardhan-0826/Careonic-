from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    if hasattr(field, 'as_widget'):  # ✅ Only works if it's a field
        return field.as_widget(attrs={"class": f"{field.field.widget.attrs.get('class', '')} {css_class}".strip()})
    return field   # if it's a string, return as is
