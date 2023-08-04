import os

import pytest
from django.core import mail
from django.urls import reverse
from django.utils.html import strip_tags

from core.models import SendMailTask

pytestmark = [pytest.mark.django_db]


def test_create_send_mail_task(
    login_user_can_send_mail, first_organization, contact, other_contact, mocker
):
    client, user = login_user_can_send_mail
    mocker.patch.object(SendMailTask, "run")

    first_organization.save()
    contact.save()
    other_contact.save()

    subject = "Test send mail task"
    content = "Content sample"

    response = client.post(
        reverse("emails-page"),
        {
            "members": [contact.pk, other_contact.pk],
            "subject": subject,
            "content": content,
            "send_personalised_emails": False,
        },
        follow=False,
    )

    assert response.status_code == 302
    SendMailTask.run.assert_called_once()
    assert SendMailTask.objects.count() == 1


def test_send_email(first_organization, contact, other_contact, email):
    first_organization.save()
    contact.save()
    other_contact.save()
    email.save()
    email.recipients.set([contact, other_contact])

    task = SendMailTask(email=email)

    task.run(is_async=False)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == email.subject
    assert mail.outbox[0].body == strip_tags(email.content)
    assert mail.outbox[0].to == contact.emails + other_contact.emails


def test_send_personalised_emails(
    first_organization, contact, other_contact, email, email_tag_first_name
):
    first_organization.save()
    contact.save()
    other_contact.save()
    email.subject += str(email_tag_first_name)
    email.send_personalised_emails = True
    email.save()
    email.recipients.set([contact, other_contact])
    email_tag_first_name.save()

    task = SendMailTask(email=email)

    task.run(is_async=False)

    assert len(mail.outbox) == 2
    assert mail.outbox[0].subject == email.subject.replace(
        str(email_tag_first_name), getattr(contact, email_tag_first_name.field_name)
    )
    assert mail.outbox[0].body == strip_tags(email.content)
    assert mail.outbox[0].to == contact.emails
    assert mail.outbox[1].subject == email.subject.replace(
        str(email_tag_first_name),
        getattr(other_contact, email_tag_first_name.field_name),
    )
    assert mail.outbox[1].body == strip_tags(email.content)
    assert mail.outbox[1].to == other_contact.emails


def test_send_email_with_attachments(
    first_organization, contact, other_contact, email, email_file
):
    first_organization.save()
    contact.save()
    other_contact.save()

    email.recipients.set([contact, other_contact])

    task = SendMailTask(email=email)

    task.run(is_async=False)

    print(mail.outbox[0].attachments)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == email.subject
    assert mail.outbox[0].body == strip_tags(email.content)
    assert mail.outbox[0].to == contact.emails + other_contact.emails

    assert len(mail.outbox[0].attachments) == 1
    assert mail.outbox[0].attachments[0] == (
        os.path.basename(email_file.file.name),
        email_file.file.read().decode("utf-8"),
        "text/plain",
    )
