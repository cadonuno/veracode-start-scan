import sys

def exit_with_error(message: any, return_value: int, scanConfiguration):
    print(message)
    sys.exit(0 if scanConfiguration.override_failure else return_value)
