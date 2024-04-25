import logging
import warnings

from django_rq import get_scheduler

logger = logging.getLogger(__name__)


def cron(cron_string, *args, **kwargs):
    """Simple decorator to make registering cron jobs easier.

    Sets a default unique ID, to avoid duplicate jobs.

    See https://github.com/rq/rq-scheduler#cron-jobs for more details
    """

    def decorator(function):
        kwargs_copy = {"id": f"{function.__module__}.{function.__name__}", **kwargs}
        scheduler = get_scheduler()
        with warnings.catch_warnings():
            # Ignore misleading warning, see upstream issue for details:
            #   https://github.com/josiahcarlson/parse-crontab/issues/43
            warnings.simplefilter("ignore", FutureWarning)
            scheduler.cron(cron_string, function, *args, **kwargs_copy)
        return function

    return decorator


def clear_scheduler():
    scheduler = get_scheduler()
    for job in scheduler.get_jobs():
        logger.debug("Clearing job: %r", job.id)
        job.delete()
