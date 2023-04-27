from django import template

register = template.Library()


@register.filter(name="add_classes")
def add_classes(value, arg):
    default_classes = value.field.widget.attrs.get("class", "")
    classes = []
    args = arg.split(" ")
    for a in args:
        classes.append(a)
    classes_string = default_classes + " ".join(classes)
    return value.as_widget(
        attrs={"class": classes_string, "placeholder": "Placeholder"}
    )
