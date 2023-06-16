from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Form

from core.models import (
    Record,
    Group,
    Emails,
    LoadKronosEventsTask,
    LoadKronosParticipantsTask,
    KronosEvent,
    TemporaryContact,
)
from core.utils import ConflictResolutionMethods
from core.widgets import RemoveGroupMembers
from ckeditor.widgets import CKEditorWidget


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
        widget=forms.CheckboxSelectMultiple,
    )

    groups = forms.MultipleChoiceField(widget=forms.SelectMultiple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].choices = tuple(Group.objects.values_list("id", "name"))
        self.fields["members"].choices = tuple(
            Record.objects.all().values_list("id", "first_name")
        )


class SendEmailForm(Form):
    members = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
    )
    groups = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
    )
    title = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "id": "title"})
    )
    content = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Emails
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["members"].choices = tuple(
            Record.objects.all().values_list("id", "first_name")
        )
        self.fields["groups"].choices = tuple(
            Group.objects.all().values_list("id", "name")
        )


class KronosEventsImportForm(Form):
    def clean(self):
        running_tasks = LoadKronosEventsTask.objects.filter(
            status__in=LoadKronosEventsTask.TASK_STATUS_PENDING_VALUES
        )
        if len(running_tasks) > 0:
            print("Task already running")
            raise ValidationError("Task already running")

        return super().clean()


class KronosParticipantsImportForm(Form):
    events = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["events"].choices = tuple(
            KronosEvent.objects.annotate().values_list("id", "title")
        )

    def clean(self):
        running_tasks = LoadKronosParticipantsTask.objects.filter(
            status__in=LoadKronosParticipantsTask.TASK_STATUS_PENDING_VALUES
        )
        if len(running_tasks) > 0:
            print("Task already running")
            raise ValidationError("Task already running")

        return super().clean()


class ResolveConflictForm(Form):
    incoming_contact = forms.ChoiceField(
        widget=forms.RadioSelect,
    )
    method = forms.ChoiceField(
        widget=forms.RadioSelect, choices=ConflictResolutionMethods.choices
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["incoming_contact"].choices = tuple(
            TemporaryContact.objects.annotate().values_list("id", "last_name")
        )


class ResolveAllConflictsForm(Form):
    method = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=ConflictResolutionMethods.choices,
        required=True,
    )
