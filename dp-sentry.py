import dotenv
import sys
import os

from sentry_sdk import init, capture_message

DSN = "http://51a19d45937344e494576f995bce8da1@10.4.32.167:9000/6"

dotenv.load_dotenv(verbose=True)
init(dsn=DSN, debug=True, shutdown_timeout=10)

capture_message("Hello World")  # Will create an event.

raise ValueError()  # Will also create an event.
