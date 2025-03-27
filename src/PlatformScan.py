import time
import threading
import os
from Constants import TIMEOUT_WAIT, SCAN_IN_PROGRESS_ERROR
from datetime import datetime, timedelta
from ScanConfiguration import ScanConfiguration
from CliCaller import call_subprocess, save_sbom_file, get_absolute_file_path
from VeracodeApi import expire_srcclr_token, get_upload_sbom
from AgentScanner import run_agent_sca
from ParallelScanHandler import parse_all_results

def has_failed_due_to_concurrent_scan(return_message):
    return return_message and SCAN_IN_PROGRESS_ERROR in return_message

def run_scan(scan_configuration : ScanConfiguration, scan_command, timeout, start_time=None):
    scan_type_prefix = f"{'Sandbox' if scan_configuration.sandbox_name else 'Policy'} Scan"
    returned_value = call_subprocess(f"{scan_type_prefix}", scan_configuration=scan_configuration, fail_on_error=False, commands=scan_command)
    
    if returned_value[0] and scan_configuration.wait_for_timeout and has_failed_due_to_concurrent_scan(returned_value[1]):
        if not start_time:
            start_time = datetime.now()
            time_since = timedelta(seconds=0)
        else:
            time_since = datetime.now() - start_time
        if timeout > time_since:
            print(f"{scan_type_prefix} already running, retrying in {TIMEOUT_WAIT} seconds.")
            time.sleep(TIMEOUT_WAIT)
            print(f" - Retrying now.")
            return run_scan(scan_configuration, scan_command, timeout, start_time)
        else:
            print(f"ERROR: {scan_type_prefix} still running after {scan_configuration.wait_for_timeout} minutes.")

    return returned_value

def start_platform_scan(scan_configuration: ScanConfiguration):
    returned_values = {}
    threads = []
    base_results_location = get_absolute_file_path(scan_configuration.base_cli_directory, "scan_results")

    thread = threading.Thread(target=start_platform_scan_inner, args=(scan_configuration, returned_values,))
    thread.start()
    threads.append(thread)

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

    if scan_configuration.sbom_type:
        save_sbom_file(get_upload_sbom(scan_configuration), scan_configuration)

    parse_all_results(scan_configuration, returned_values)

def start_platform_scan_inner(scan_configuration: ScanConfiguration, returned_values):
    scan_command = ["java", "-jar", scan_configuration.veracode_wrapper_location, "-vid", scan_configuration.vid, "-vkey", scan_configuration.vkey, 
                    "-createsandbox", "true", "-filepath", scan_configuration.source, "-version", scan_configuration.version]
    if (scan_configuration.sandbox_name):
        scan_command.append("-sandboxname")
        scan_command.append(scan_configuration.sandbox_name)
    
    if (scan_configuration.scan_timeout):
        scan_command.append("-scantimeout")
        scan_command.append(scan_configuration.scan_timeout)
    
    if scan_configuration.verbose:
        scan_command.append("-debug")

    if scan_configuration.delete_incomplete_scan or scan_configuration.exclude or scan_configuration.scan_all_non_fatal_top_level_modules:
        scan_command.append("-action")
        scan_command.append("uploadandscan")
        scan_command.append("-appname")
        scan_command.append(scan_configuration.application)
        scan_command.append("-createprofile")
        scan_command.append("false")
        if scan_configuration.delete_incomplete_scan:   
            scan_command.append("-deleteincompletescan")
            scan_command.append(scan_configuration.delete_incomplete_scan)
        if scan_configuration.exclude:
            scan_command.append("-exclude")
            scan_command.append(scan_configuration.exclude)
        if scan_configuration.scan_all_non_fatal_top_level_modules:
            scan_command.append("-scanallnonfataltoplevelmodules")
            scan_command.append("true")
    else:
        scan_command.append("-action")
        scan_command.append("uploadandscanbyappid")
        scan_command.append("-appid")
        scan_command.append(scan_configuration.application_legacy_id)

    if scan_configuration.include:
        scan_command.append("-include")
        scan_command.append(scan_configuration.include)

    scan_result = run_scan(scan_configuration, scan_command, timedelta(minutes=scan_configuration.wait_for_timeout) if scan_configuration.wait_for_timeout else timedelta(minutes=0))
    returned_values[f"{"Sandbox" if scan_configuration.sandbox_name else "Policy"} Scan"] = scan_result