from django import forms
from django.db.models import CharField, Value
from django.db.models.functions import Concat
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
