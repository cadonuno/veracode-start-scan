import os
import threading

from pathlib import Path
from ScanConfiguration import ScanConfiguration
from CliCaller import call_subprocess, get_absolute_file_path
from ScanConfiguration import ScanConfiguration
from VeracodeCli import get_policy_file_name
from ParallelScanHandler import parse_all_results
from VeracodeApi import expire_srcclr_token
from AgentScanner import run_agent_sca
from Constants import FILE_TYPE, FILE_LOCATION

def run_pipeline_scan_thread(returned_values, scan_target, scan_configuration : ScanConfiguration, policy_file_name, results_json, results_txt):
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
    if scan_configuration.include:
        commands.append("--include")
        commands.append(scan_configuration.include)
    returned_values[scan_target] = call_subprocess(process_id=f"Scanning {scan_target}", scan_configuration=scan_configuration, fail_on_error=False, commands=commands)
    scan_configuration.generated_output_files.append({ FILE_TYPE: f"Pipeline scan results JSON for {scan_target}", FILE_LOCATION: results_json})
    scan_configuration.generated_output_files.append({ FILE_TYPE: f"Pipeline scan results TXT for {scan_target}", FILE_LOCATION: results_txt})

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
        if scan_configuration.srcclr_token:
            expire_srcclr_token(scan_configuration)

    parse_all_results(scan_configuration, returned_values)