from django import forms
from django.forms import ModelForm, Form

from core.models import Record, Group
from core.widgets import RemoveGroupMembers


class RecordUpdateForm(ModelForm):
    class Meta:
        model = Record
        fields = "__all__"
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"})}


class GroupUpdateForm(ModelForm):
    class Meta:
        model = Group
        fields = "__all__"
        widgets = {"contacts": RemoveGroupMembers()}


class AddGroupMemberForm(Form):
    new_member_id = forms.CharField()


class AddMultipleGroupMembersForm(Form):
    members = forms.MultipleChoiceField(
        choices=Record.objects.all().values_list("id", "first_name"),
        widget=forms.CheckboxSelectMultiple
    )

    groups = forms.MultipleChoiceField(
        choices=Group.objects.all().values_list("id", "name"),
        widget=forms.SelectMultiple
    )
