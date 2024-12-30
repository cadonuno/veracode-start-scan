from ScanConfiguration import ScanConfiguration
import sys

def exit_with_error(message: str, return_value: int, scanConfiguration: ScanConfiguration):
    print(message)
    sys.exit(0 if scanConfiguration.override_failure else return_value)
