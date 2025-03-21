import time
from Constants import TIMEOUT_WAIT, SCAN_IN_PROGRESS_ERROR
from datetime import datetime, timedelta
from ScanConfiguration import ScanConfiguration
from CliCaller import call_subprocess, save_sbom_file
from ErrorHandler import exit_with_error, try_generate_error_message
from VeracodeApi import get_upload_sbom

def has_failed_due_to_concurrent_scan(return_message):
    return return_message and SCAN_IN_PROGRESS_ERROR in return_message

def run_scan(scan_configuration, scan_command, timeout, start_time=None):
    scan_type_prefix = f"{'Sandbox' if scan_configuration.sandbox_name else 'Policy'} Scan"
    returned_value = call_subprocess(f"{scan_type_prefix}", scan_configuration=scan_configuration, fail_on_error=False, commands=scan_command)
    
    return_code = returned_value[0]
    return_message = returned_value[1]

    if return_code != 0 and scan_configuration.wait_for_timeout and has_failed_due_to_concurrent_scan(return_message):
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
        
    errors = try_generate_error_message(return_code=return_code, error_message=return_message, target=scan_type_prefix)

    if scan_configuration.sbom_type:
        save_sbom_file(get_upload_sbom(scan_configuration), scan_configuration)

    if scan_configuration.fail_build and return_code != 0:
        exit_with_error(errors, return_value=return_code, scan_configuration=scan_configuration)
    else:
        print(errors)

def start_platform_scan(scan_configuration: ScanConfiguration):
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

    if scan_configuration.delete_incomplete_scan:
        scan_command.append("-action")
        scan_command.append("uploadandscan")
        scan_command.append("-appname")
        scan_command.append(scan_configuration.application)
        scan_command.append("-deleteincompletescan")
        scan_command.append(scan_configuration.delete_incomplete_scan)
        scan_command.append("-createprofile")
        scan_command.append("false")
    else:
        scan_command.append("-action")
        scan_command.append("uploadandscanbyappid")
        scan_command.append("-appid")
        scan_command.append(scan_configuration.application_legacy_id)

    if scan_configuration.include:
        scan_command.append("-include")
        scan_command.append(scan_configuration.include)

    run_scan(scan_configuration, scan_command, timedelta(minutes=scan_configuration.wait_for_timeout) if scan_configuration.wait_for_timeout else timedelta(minutes=0))
