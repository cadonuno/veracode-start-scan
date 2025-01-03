import os
from Constants import PACKAGER_OUTPUT
from CliCaller import call_subprocess
from ScanConfiguration import ScanConfiguration

def package_application(scan_source: str, scan_configuration: ScanConfiguration) -> str:
    call_subprocess("Veracode Packager", scan_configuration, True, [scan_configuration.veracode_cli_location, "package", "-das", scan_source, "--output", PACKAGER_OUTPUT])
    return os.path.join(scan_configuration.base_cli_directory, PACKAGER_OUTPUT)

def get_policy_file_name(scan_configuration: ScanConfiguration) -> str:
    policy_name = scan_configuration.policy_name.replace("+","%2B")
    call_subprocess("Getting Policy File", scan_configuration, True, [scan_configuration.veracode_cli_location, "policy", "get", policy_name])
    return policy_name