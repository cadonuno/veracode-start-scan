from ScanConfiguration import ScanConfiguration
from CliCaller import call_subprocess
from ScanConfiguration import ScanConfiguration
import os

def start_pipeline_scan(scan_configuration: ScanConfiguration):
    for scan_target in os.listdir(scan_configuration.source):
        call_subprocess(scan_configuration, "./veracode", "static", "scan", scan_target, "--policy_file", f"{scan_configuration.policy_name}.json")