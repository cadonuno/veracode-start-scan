import os
from Constants import PACKAGER_OUTPUT
from CliCaller import call_subprocess
from ScanConfiguration import ScanConfiguration

def package_application(scan_source: str, scan_configuration: ScanConfiguration) -> str:
    package_commands = [scan_configuration.veracode_cli_location, "package", "--source", scan_source, "--output", PACKAGER_OUTPUT, "--trust"]
    if scan_configuration.verbose:
        package_commands.append("-d")
    call_subprocess("Veracode Packager", scan_configuration, True, package_commands)
    artifacts_directory = os.path.join(scan_configuration.base_cli_directory, PACKAGER_OUTPUT)
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