from auditlog.cid import get_cid
from auditlog.diff import model_instance_diff
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_str


def _bulk_audit(objs, action, get_changes, request=None):
    if not objs:
        return None

    actor = request.user if request else None
    cid = get_cid()

    model = objs[0]._meta.model
    content_type = ContentType.objects.get_for_model(model)

    return LogEntry.objects.bulk_create(
        [
            LogEntry(
                actor=actor,
                cid=cid,
                action=action,
                content_type=content_type,
                object_repr=smart_str(obj),
                object_pk=obj.pk,
                object_id=obj.id,
                changes=get_changes(obj),
            )
            for obj in objs
        ],
        batch_size=1000,
        ignore_conflicts=True,
    )


def bulk_audit_create(objs, request=None):
    return _bulk_audit(
        objs,
        LogEntry.Action.CREATE,
        lambda obj: model_instance_diff(None, obj),
        request=request,
    )


def bulk_audit_update(objs, changes, request=None):
    return _bulk_audit(
        objs,
        LogEntry.Action.UPDATE,
        lambda obj: changes,
        request=request,
    )
