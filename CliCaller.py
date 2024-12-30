import subprocess
import os
from ErrorHandler import exit_with_error
from ScanConfiguration import ScanConfiguration

def call_subprocess(scan_configuration: ScanConfiguration, *commands : str):
    try:
        environment = os.environ.copy()
        environment["VERACODE_API_KEY_ID"] = scan_configuration.vid
        environment["VERACODE_API_KEY_ID"] = scan_configuration.vkey
        results = subprocess.check_output(commands)
        print(results)
    except subprocess.CalledProcessError as calledProcessError:
        exit_with_error(calledProcessError.output, calledProcessError.returncode, scan_configuration)
    