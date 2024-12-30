from Constants import PACKAGER_OUTPUT
from CliCaller import call_subprocess
from ScanConfiguration import ScanConfiguration
from VeracodeApi import get_application_policy_name

def package_application(scan_source: str, scan_configuration: ScanConfiguration) -> str:
    call_subprocess(scan_configuration, True, [scan_configuration.veracode_cli_location, "package", "-das", scan_source, "--output", PACKAGER_OUTPUT])
    return PACKAGER_OUTPUT

def get_policy_file_name(scan_configuration: ScanConfiguration) -> str:
    policy_name = get_application_policy_name(scan_configuration.application_guid, scan_configuration).replace("+","%2B")
    call_subprocess(scan_configuration, True, [scan_configuration.veracode_cli_location, "policy", "get", policy_name])
    return policy_name