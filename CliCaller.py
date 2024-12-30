import subprocess
import os
from ErrorHandler import exit_with_error
from ScanConfiguration import ScanConfiguration

def check_wrapper(scan_configuration: ScanConfiguration):
    errors = []

    if not os.path.isfile("./VeracodeJavaAPI.jar"):
        errors.append("ERROR: Veracode API wrapper (VeracodeJavaAPI.jar) not found in local directory")

    if errors:
        exit_with_error(errors, len(errors)*-1, scan_configuration)

def call_subprocess(scan_configuration: ScanConfiguration, fail_on_error: bool, commands : list[str]):
    # TODO: stream CLI results in real time
    try:
        environment = os.environ.copy()
        environment["VERACODE_API_KEY_ID"] = scan_configuration.vid
        environment["VERACODE_API_KEY_SECRET"] = scan_configuration.vkey
        results = subprocess.check_output(args=commands, cwd=os.path.dirname(os.path.realpath(__file__)), env=environment)
        print(results)
    except subprocess.CalledProcessError as calledProcessError:
        if fail_on_error:
            exit_with_error(calledProcessError.output, calledProcessError.returncode, scan_configuration)
        else:
            print(calledProcessError.output)
    