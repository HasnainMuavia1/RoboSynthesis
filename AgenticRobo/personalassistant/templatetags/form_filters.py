from django import template

register = template.Library()

@register.filter(name='attr')
def set_attr(field, attr_string):
    """
    Add attributes to form fields
    Usage: {{ field|attr:"placeholder:Enter text here,class:custom-class" }}
    """
    attrs = {}
    pairs = attr_string.split(',')
    
    for pair in pairs:
        if ':' in pair:
            key, value = pair.split(':', 1)
            attrs[key.strip()] = value.strip()
    
    return field.as_widget(attrs=attrs)
