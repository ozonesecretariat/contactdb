from django.forms.widgets import SelectMultiple


class RemoveGroupMembers(SelectMultiple):
    template_name = "widgets/remove_members.html"

    def optgroups(self, name, value, attrs=None):
        groups = super().optgroups(name, value, attrs)
        new_groups = []
        for group in groups:
            item = (
                group[0],
                [option for option in group[1] if option["selected"] is True],
                group[2],
            )
            if len(item[1]) > 0:
                print(item)
                new_groups.append(item)

        return new_groups
