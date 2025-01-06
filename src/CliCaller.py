import subprocess
import os
import io

from colored import Fore, Style
from ErrorHandler import exit_with_error
from ScanConfiguration import ScanConfiguration

PROCESS_ID_COLOUR = Fore.rgb('112', '146', '190')

def handle_error(fail_on_error, error_message, return_code, scan_configuration):
    if return_code and return_code != 0 and fail_on_error:
        exit_with_error(error_message, return_code, scan_configuration)
    return return_code, error_message

def call_subprocess(process_id, scan_configuration: ScanConfiguration, fail_on_error: bool, commands : list[str],
                    additional_env=[], results_file=None, shell=False):
    try:
        environment = os.environ.copy()
        environment["VERACODE_API_KEY_ID"] = scan_configuration.vid
        environment["VERACODE_API_KEY_SECRET"] = scan_configuration.vkey
        for additional_environment_variable in additional_env:
            environment[additional_environment_variable["name"]] = additional_environment_variable["value"]
        process = subprocess.Popen(args=commands, cwd=scan_configuration.base_cli_directory, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        last_line = ''
        if results_file:
            with open(results_file, 'w') as output_file:
                last_line = handle_output(process_id, process, output_file)
        else:
            last_line = handle_output(process_id, process, None)
        process.wait()
        return handle_error(fail_on_error, last_line, process.returncode, scan_configuration)
    except subprocess.CalledProcessError as calledProcessError:
        return handle_error(fail_on_error, calledProcessError.output, calledProcessError.returncode, scan_configuration)

def handle_output(process_id, process, output_file):
    last_line = ""
    for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
        last_line = line.strip() if line.strip() else last_line
        print(f"{PROCESS_ID_COLOUR}{process_id}:{Style.reset} {line}", end='')
        if output_file:
            print(line, file=output_file, end='')
    return last_line
    