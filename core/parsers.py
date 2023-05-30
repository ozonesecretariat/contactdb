import logging
from datetime import datetime

from django.utils.timezone import make_aware

from core.models import KronosEvent


class KronosEventsParser:
    def __init__(self, task=None):
        self.task = task

    def parse_event_list(self, event_list):
        count_created = 0
        count_updated = 0
        for event_dict in event_list:
            try:
                try:
                    self.task.log(
                        logging.INFO, f"Saving event: {event_dict.get('title')}"
                    )
                except:
                    pass

                d = {
                    "event_id": event_dict.get("eventId"),
                    "title": event_dict.get("title"),
                    "code": event_dict.get("code"),
                    "start_date": make_aware(
                        datetime.strptime(
                            event_dict.get("startDate"), "%Y-%m-%dT%H:%M:%SZ"
                        )
                    ),
                    "end_date": make_aware(
                        datetime.strptime(
                            event_dict.get("endDate"), "%Y-%m-%dT%H:%M:%SZ"
                        )
                    ),
                    "venue_country": event_dict.get("venueCountry"),
                    "venue_city": event_dict.get("venueCity"),
                    "dates": event_dict.get("dates"),
                }
                created, attr_changes = self.save_event(d)

                if created:
                    count_created += 1
                    try:
                        self.task.log(
                            logging.INFO, f"New event added: {event_dict.get('title')}"
                        )
                    except:
                        pass
                elif attr_changes:
                    count_updated += 1
                    try:
                        print(attr_changes)
                        self.task.log(
                            logging.INFO, f"Event updated: {event_dict.get('title')}"
                        )
                    except:
                        pass

            except Exception as e:
                print(e)
                try:
                    self.task.log(
                        logging.WARN, f"Failed to save event: {event_dict.get('title')}"
                    )
                except:
                    pass
        return count_created, count_updated

    @staticmethod
    def save_event(event_dict):
        old_event = KronosEvent.objects.filter(
            event_id=event_dict.get("event_id")
        ).first()
        new_event, created = KronosEvent.objects.update_or_create(
            event_id=event_dict["event_id"],
            defaults=dict(event_dict),
        )

        attr_changes = {}
        for attr, value in [(k, v) for (k, v) in event_dict.items()]:
            old_value = getattr(old_event, str(attr), None)
            if str(value) != str(old_value):
                attr_changes.update({attr: (old_value, value)})
        return created, attr_changes
