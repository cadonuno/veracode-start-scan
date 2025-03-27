import sys
from collections.abc import Iterable
from ColourHandler import RESET_STYLE, WARNING_MESSAGE_COLOUR, ERROR_PREFIX_COLOUR, INFO_PREFIX_COLOUR

def exit_with_error(message: any, return_value: int, scan_configuration):
    if isinstance(message, Iterable) and not isinstance(message, str):
        for line in message:
            print(line.replace("\n", ""))
    else:
        print(message)
    sys.exit(0 if scan_configuration.override_failure else return_value)

def show_warning(message):
    print(f"{WARNING_MESSAGE_COLOUR}WARNING: {RESET_STYLE}{WARNING_MESSAGE_COLOUR}{message}{RESET_STYLE}")

def try_generate_error_message(return_code, message, target, messages=[]):
    if return_code != 0:        
        messages.append(f"{ERROR_PREFIX_COLOUR}Failed scan for {target}:{RESET_STYLE} {message}.")
    else:
        messages.append(f"{INFO_PREFIX_COLOUR}Successfull scan for {target}:{RESET_STYLE} {message}.")
    return messages