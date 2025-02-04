import sys
from collections.abc import Iterable
from colored import Fore, Style

WARNING_COLOUR=Fore.rgb(212, 105, 32)
WARNING_MESSAGE_COLOUR=Fore.rgb(255, 127, 39)

ERROR_PREFIX_COLOUR = Fore.rgb('136', '0', '21')

def exit_with_error(message: any, return_value: int, scanConfiguration):
    if isinstance(message, Iterable) and not isinstance(message, str):
        for line in message:
            print(line.replace("\n", ""))
    else:
        print(message)
    sys.exit(0 if scanConfiguration.override_failure else return_value)

def show_warning(message):
    print(f"{WARNING_COLOUR}WARNING: {Style.reset}{WARNING_MESSAGE_COLOUR}{message}{Style.reset}")

def try_generate_error_message(return_code, error_message, target, errors=[]):
    if return_code != 0:        
        errors.append(f"{ERROR_PREFIX_COLOUR}Failed scan for {target}:{Style.reset} {error_message}.")
    return errors