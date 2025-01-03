from ScanConfiguration import ScanConfiguration
from CliCaller import call_subprocess

def start_platform_scan(scan_configuration: ScanConfiguration):
    scan_command = ["java", "-jar", scan_configuration.veracode_wrapper_location, "-appname", scan_configuration.application, "-vid", scan_configuration.vid, "-vkey", scan_configuration.vkey, "-action", 
                  "uploadandscan", "-createprofile", "true", "-createsandbox", "true", "-filepath", scan_configuration.source, "-version", scan_configuration.version]
    if (scan_configuration.sandbox_name):
        scan_command.append("-sandboxname")
        scan_command.append(scan_configuration.sandbox_name)
    
    if (scan_configuration.scan_timeout):
        scan_command.append("-scantimeout")
        scan_command.append(scan_configuration.scan_timeout)

    call_subprocess(f"{"Sandbox" if scan_configuration.sandbox_name else "Policy"} Scan:", scan_configuration, scan_configuration.fail_build, scan_command)
    
    