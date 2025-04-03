from ScanConfiguration import ScanConfiguration
from ErrorHandler import exit_with_error, try_generate_error_message
from ColourHandler import INFO_PREFIX_COLOUR, ERROR_PREFIX_COLOUR, RESET_STYLE
from Constants import FILE_TYPE, FILE_LOCATION

def parse_all_results(scan_configuration: ScanConfiguration, returned_values):
    total_return_code = 0
    messages = []
    for target, returned_value in returned_values.items():
        total_return_code += abs(returned_value[0])
        messages=try_generate_error_message(return_code=returned_value[0], message=returned_value[1], target=target)

    if scan_configuration.generated_output_files:
        messages.append(f"{INFO_PREFIX_COLOUR}Output files:{RESET_STYLE}")
        for generated_file in scan_configuration.generated_output_files:
            messages.append(f"  - {INFO_PREFIX_COLOUR}{generated_file[FILE_TYPE]}{RESET_STYLE}: {generated_file[FILE_LOCATION]}")


    print()      
    print(f"{ERROR_PREFIX_COLOUR if total_return_code != 0 else INFO_PREFIX_COLOUR}Analysis completed:{RESET_STYLE}")
    if scan_configuration.fail_build and total_return_code != 0:
        exit_with_error(messages, return_value=total_return_code, scan_configuration=scan_configuration)
    else:
        print(messages)