import os
import threading

from pathlib import Path
from ScanConfiguration import ScanConfiguration
from VeracodeCli import call_subprocess
from ScanConfiguration import ScanConfiguration
from VeracodeCli import get_policy_file_name
from ErrorHandler import exit_with_error
from colored import Fore, Style
from VeracodeApi import expire_srcclr_token, link_sca_project

ERROR_PREFIX_COLOUR = Fore.rgb('136', '0', '21')

def run_pipeline_scan_thread(returned_values, scan_target, scan_configuration, policy_file_name, results_json, results_txt):
    commands = [scan_configuration.veracode_cli_location, "static", "scan", 
                                            os.path.join(scan_configuration.source, scan_target), 
                                            "--project-name", scan_configuration.application,
                                            "--app-id", scan_configuration.application_guid,
                                            "--policy-file", f"{policy_file_name}", 
                                            "--results-file", results_json,
                                            "--summary-output", results_txt,
                                            "--project-name", scan_configuration.application]
    if scan_configuration.verbose:
        commands.append("--verbose")
    returned_values[scan_target] = call_subprocess(process_id=f"Scanning {scan_target}", scan_configuration=scan_configuration, fail_on_error=False, commands=commands)

def run_agent_sca_inner(results_file, scan_configuration):
    commands=["srcclr", "scan", scan_configuration.srcclr_to_scan, "--recursive", "--allow-dirty"]
    if scan_configuration.verbose:
        commands.append("--debug")
    return call_subprocess(process_id="Running SCA Scan", scan_configuration=scan_configuration, fail_on_error=False, 
                            commands=commands,
                            additional_env=[{"name": "SRCCLR_API_URL", "value": scan_configuration.srcclr_api_url},
                                            {"name": "SRCCLR_API_TOKEN", "value": scan_configuration.srcclr_token}],
                            results_file=results_file,
                            shell=True,
                            return_line_filter=["Full Report Details", "https://"])


def start_all_pipeline_scans(scan_configuration, policy_file_name, returned_values, threads, base_results_location):
    Path(base_results_location).mkdir(parents=True, exist_ok=True)
    for scan_target in os.listdir(get_absolute_file_path(scan_configuration.base_cli_directory, scan_configuration.source)):
        folder_to_save = os.path.join(base_results_location, scan_target.replace(".", ""))
        Path(folder_to_save).mkdir(parents=True, exist_ok=True)
        thread = threading.Thread(target=run_pipeline_scan_thread, args=(returned_values, scan_target, scan_configuration, 
                                                                         policy_file_name, os.path.join(folder_to_save, "results.json"), 
                                                                         os.path.join(folder_to_save, "results.txt"),))
        thread.start()
        threads.append(thread)

def run_agent_sca(returned_values, results_file, scan_configuration):
    sca_results = run_agent_sca_inner(results_file, scan_configuration)
    if scan_configuration.link_project and sca_results[2]:
        link_sca_project(sca_results[2], scan_configuration)
    returned_values["SCA Scan"] = sca_results

def start_pipeline_scan(scan_configuration: ScanConfiguration):
    policy_file_name = get_policy_file_name(scan_configuration)
    returned_values = {}
    threads = []
    base_results_location = get_absolute_file_path(scan_configuration.base_cli_directory, "scan_results")
    start_all_pipeline_scans(scan_configuration, policy_file_name, returned_values, threads, base_results_location)
    
    try:
        if scan_configuration.srcclr_token:
            thread = threading.Thread(target=run_agent_sca, args=(returned_values, os.path.join(base_results_location, "sca_results.txt"), scan_configuration,))
            thread.start()
            threads.append(thread)
        
        
        for thread in threads:
            thread.join()
    finally:
        expire_srcclr_token(scan_configuration)

    total_return_code = 0
    errors = []
    for target, returned_value in returned_values.items():
        return_code = returned_value[0]
        error_message = returned_value[1]
        if return_code != 0:
            total_return_code += abs(return_code)
            errors.append(f"{ERROR_PREFIX_COLOUR}Failed scan for {target}:{Style.reset} {error_message}.")
    if scan_configuration.fail_build and total_return_code != 0:
        exit_with_error(errors, return_value=total_return_code, scanConfiguration=scan_configuration)
    else:
        print(errors)

def get_absolute_file_path(base_directory, file_name):
    return os.path.join(base_directory, file_name)