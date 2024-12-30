from Constants import PACKAGER_OUTPUT
from CliCaller import call_subprocess
from ScanConfiguration import ScanConfiguration

def package_application(scan_source: str, scanConfiguration: ScanConfiguration) -> str:
    call_subprocess(scanConfiguration, "./veracode", "package", "-das", scan_source, "--output", PACKAGER_OUTPUT)
    return PACKAGER_OUTPUT