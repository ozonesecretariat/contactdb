from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Value
from django.db.models.functions import Concat
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
    def __init__(self, *args, **kwargs):
        main_contact_choices = kwargs.pop("main_contact_choices", [])
        super().__init__(*args, **kwargs)

        if main_contact_choices:
            self.fields["main_contact"].choices = main_contact_choices

        self.fields[
            "phones"
        ].help_text = "To add multiple phone numbers, use a comma as a separator."
        self.fields[
            "mobiles"
        ].help_text = "To add multiple mobiles numbers, use a comma as a separator."
        self.fields[
            "faxes"
        ].help_text = "To add multiple fax numbers, use a comma as a separator."
        self.fields[
            "emails"
        ].help_text = "To add multiple emails, use a comma as a separator."
        self.fields[
            "email_ccs"
        ].help_text = "To add multiple cc emails, use a comma as a separator."

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
        ).exists()
        if running_tasks:
            raise ValidationError("Task already running")

        return super().clean()


class KronosParticipantsImportForm(Form):
    events = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["events"].choices = tuple(
            KronosEvent.objects.values_list("id", "title")
        )

    def clean(self):
        running_tasks = LoadKronosParticipantsTask.objects.filter(
            status__in=LoadKronosParticipantsTask.TASK_STATUS_PENDING_VALUES
        )
        if len(running_tasks) > 0:
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
            TemporaryContact.objects.values_list("id", "last_name")
        )


class ResolveAllConflictsForm(Form):
    method = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=ConflictResolutionMethods.choices,
        required=True,
    )


class MergeContactsFirstStepForm(Form):
    contacts = forms.MultipleChoiceField(
        widget=forms.SelectMultiple,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contacts"].choices = tuple(
            Record.objects.annotate(
                name=Concat("first_name", Value(" "), "last_name")
            ).values_list("id", "name")
        )


class MergeContactsSecondStepForm(Form):
    contact = forms.ChoiceField(
        widget=forms.RadioSelect,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("choices", [])
        super().__init__(*args, **kwargs)
        self.fields["contact"].choices = choices
