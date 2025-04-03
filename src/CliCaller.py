import subprocess
import os
import io
import json

from ColourHandler import INFO_PREFIX_COLOUR, RESET_STYLE
from ErrorHandler import exit_with_error
from ScanConfiguration import ScanConfiguration
from Constants import FILE_TYPE, FILE_LOCATION


def handle_error(fail_on_error, error_message, return_code, scan_id, scan_configuration):
    if return_code and return_code != 0 and fail_on_error:
        exit_with_error(error_message, return_code, scan_configuration)
    return return_code, error_message, scan_id

def call_subprocess(process_id, scan_configuration: ScanConfiguration, fail_on_error: bool, commands : list[str],
                    additional_env=[], results_file=None, shell=False, return_line_filter=[]):
    try:
        environment = os.environ.copy()
        environment["VERACODE_API_KEY_ID"] = scan_configuration.vid
        environment["VERACODE_API_KEY_SECRET"] = scan_configuration.vkey
        for additional_environment_variable in additional_env:
            environment[additional_environment_variable["name"]] = additional_environment_variable["value"]
        process = subprocess.Popen(args=commands, cwd=scan_configuration.base_cli_directory, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        last_line = ''
        scan_id = ''
        if results_file:
            with open(results_file, 'w') as output_file:
                last_line, scan_id = handle_output(process_id, process, output_file, return_line_filter)
        else:
            last_line, scan_id = handle_output(process_id, process, None, return_line_filter)
        process.wait()
        return handle_error(fail_on_error, last_line, process.returncode, scan_id, scan_configuration)
    except subprocess.CalledProcessError as calledProcessError:
        return handle_error(fail_on_error, calledProcessError.output, calledProcessError.returncode, '', scan_configuration)

def handle_output(process_id, process, output_file, return_line_filter):
    last_line = ""
    scan_id = ""
    for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
        if return_line_filter:
            last_line = last_line if last_line else all_match(line, return_line_filter)
        else:
            last_line = line.strip() if line.strip() else last_line
        print(f"{INFO_PREFIX_COLOUR}{process_id}:{RESET_STYLE} {line}", end='')
        if output_file:
            print(line, file=output_file, end='')
        if line.startswith("Scan ID"):
            scan_id = line.split(" ")[-1].strip()
    return last_line, scan_id
    
def all_match(line, return_line_filter):
    for filter in return_line_filter:
        if not filter in line:
            return ""

    return line

def save_sbom_file(sbom_json, scan_configuration):
    sbom_location = os.path.join(get_absolute_file_path(scan_configuration.base_cli_directory, "scan_results"), f"{scan_configuration.application}-SBOM-{scan_configuration.sbom_type}.json")
    with open(sbom_location, 'w') as output_file:
        output_file.write(json.dumps(sbom_json, indent=2))
    scan_configuration.generated_output_files.append({ FILE_TYPE: f"{scan_configuration.sbom_type} SBOM", FILE_LOCATION: sbom_location})

    print(f"{INFO_PREFIX_COLOUR}Veracode SBOM:{RESET_STYLE} {scan_configuration.sbom_type} SBOM saved to: {sbom_location}")

def get_absolute_file_path(base_directory, file_name):
    return os.path.join(base_directory, file_name)