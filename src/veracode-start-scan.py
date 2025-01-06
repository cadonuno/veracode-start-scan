from ScanConfiguration import ScanConfiguration
from PipelineScan import start_pipeline_scan
from PlatformScan import start_platform_scan
from VeracodeCli import package_application
from PreScan import pre_scan_actions
import os

def main():
    old_veracode_api_key_id = os.environ.get('veracode_api_key_id', "")
    old_veracode_api_key_secret = os.environ.get('veracode_api_key_secret', "")    
    try:
        scan_configuration = ScanConfiguration()

        scan_configuration = pre_scan_actions(scan_configuration)

        if scan_configuration.scan_type == 'folder':
            scan_configuration.source = package_application(scan_configuration.source, scan_configuration)

        if scan_configuration.pipeline_scan:
            start_pipeline_scan(scan_configuration)
        else:
            start_platform_scan(scan_configuration)
    finally:
        os.environ['veracode_api_key_id'] = old_veracode_api_key_id
        os.environ['veracode_api_key_secret'] = old_veracode_api_key_secret

if __name__ == '__main__':
    main()
    