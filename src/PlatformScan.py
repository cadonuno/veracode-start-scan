from ScanConfiguration import ScanConfiguration
from CliCaller import call_subprocess
from ErrorHandler import exit_with_error, try_generate_error_message

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

    scan_type_prefix = f"{'Sandbox' if scan_configuration.sandbox_name else 'Policy'} Scan"
    returned_value = call_subprocess(f"{scan_type_prefix}", scan_configuration=scan_configuration, fail_on_error=False, commands=scan_command)
    errors = try_generate_error_message(return_code=returned_value[0], error_message=returned_value[1], target=scan_type_prefix)
    if scan_configuration.fail_build and returned_value[0] != 0:
        exit_with_error(errors, return_value=returned_value[0], scanConfiguration=scan_configuration)
    else:
        print(errors)
