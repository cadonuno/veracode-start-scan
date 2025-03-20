from ScanConfiguration import ScanConfiguration
from PipelineScan import start_pipeline_scan
from PlatformScan import start_platform_scan
from VeracodeCli import package_application
from PreScan import pre_scan_actions
from ErrorHandler import exit_with_error
import os

def main():
    old_veracode_api_key_id = os.environ.get('veracode_api_key_id', "")
    old_veracode_api_key_secret = os.environ.get('veracode_api_key_secret', "")
    old_http_proxy = os.environ.get('http_proxy', "") 
    old_http_proxy_caps = os.environ.get('HTTP_PROXY', "")
    old_https_proxy = os.environ.get('https_proxy', "")
    old_https_proxy_caps = os.environ.get('HTTPS_PROXY', "")
    try:
        scan_configuration = ScanConfiguration()

        if scan_configuration.scan_type == 'folder':
            scan_configuration.source = package_application(scan_configuration.source, scan_configuration)

        if not os.path.isdir(scan_configuration.source) or not os.listdir(scan_configuration.source):
            exit_with_error(f"Packaging failed - no files generated at {scan_configuration.source}", -1, scan_configuration)


        scan_configuration = pre_scan_actions(scan_configuration)
        if scan_configuration.pipeline_scan:
            start_pipeline_scan(scan_configuration)
        else:
            start_platform_scan(scan_configuration)
    finally:
        os.environ['veracode_api_key_id'] = old_veracode_api_key_id
        os.environ['veracode_api_key_secret'] = old_veracode_api_key_secret
        os.environ['http_proxy'] = old_http_proxy
        os.environ['HTTP_PROXY'] = old_http_proxy_caps
        os.environ['https_proxy'] = old_https_proxy
        os.environ['HTTPS_PROXY'] = old_https_proxy_caps

if __name__ == '__main__':
    main()
    