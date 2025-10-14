from .settings import *  # noqa

TESTING = True
KRONOS_USERNAME = ""
KRONOS_PASSWORD = ""

RQ_QUEUES = {
    "default": {
        **RQ_QUEUES["default"],  # noqa:F405
        "ASYNC": False,
    }
}

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: False,
}
