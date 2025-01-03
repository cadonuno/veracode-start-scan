import sys
from collections.abc import Iterable

def exit_with_error(message: any, return_value: int, scanConfiguration):
    if isinstance(message, Iterable) and not isinstance(message, str):
        for line in message:
            print(line.replace("\n", ""))
    else:
        print(message)
    sys.exit(0 if scanConfiguration.override_failure else return_value)
