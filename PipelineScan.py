from ScanConfiguration import ScanConfiguration
from CliCaller import call_subprocess
from ScanConfiguration import ScanConfiguration
from VeracodeCli import get_policy_file_name
import os

def start_pipeline_scan(scan_configuration: ScanConfiguration):
    policy_file_name = get_policy_file_name(scan_configuration)
    #TODO: do this in parallel
    for scan_target in os.listdir(scan_configuration.source):
        call_subprocess(scan_configuration, scan_configuration.fail_build, [scan_configuration.veracode_cli_location, "static", "scan", os.path.join(scan_configuration.source, scan_target), "--policy-file", f"{policy_file_name}"])