import os
import shutil
from Constants import PACKAGER_OUTPUT
from CliCaller import call_subprocess
from ScanConfiguration import ScanConfiguration
from ErrorHandler import exit_with_error

def clear_directory(directory, scan_configuration):
    if not os.path.exists(directory):
        return
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except OSError as e:
            exit_with_error(f'Failed to delete file {file_path}. Reason: {e}', -5, scan_configuration)

def package_application(scan_source: str, scan_configuration: ScanConfiguration) -> str:
    artifacts_directory = os.path.join(scan_configuration.base_cli_directory, PACKAGER_OUTPUT, scan_configuration.application)
    
    if scan_configuration.cleanup_before_start:
        clear_directory(artifacts_directory, scan_configuration)

    package_commands = [scan_configuration.veracode_cli_location, "package", "--source", scan_source, "--output", artifacts_directory, "--trust"]
    if scan_configuration.verbose:
        package_commands.append("-d")
    call_subprocess("Veracode Packager", scan_configuration, True, package_commands)    
    if scan_configuration.ignore_artifacts:
        for ignore_artifact in scan_configuration.ignore_artifacts:
            ignore_path = os.path.join(artifacts_directory, ignore_artifact)
            if os.path.exists(ignore_path):
                os.remove(ignore_path)
    return artifacts_directory

def get_policy_file_name(scan_configuration: ScanConfiguration) -> str:
    policy_name = scan_configuration.policy_name.replace("+","%2B")
    call_subprocess("Getting Policy File", scan_configuration, True, [scan_configuration.veracode_cli_location, "policy", "get", policy_name])
    return policy_name