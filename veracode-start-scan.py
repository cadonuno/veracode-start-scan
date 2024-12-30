from ScanConfiguration import ScanConfiguration
from PipelineScan import start_pipeline_scan
from PlatformScan import start_platform_scan
from VeracodeCli import package_application
from PreScan import pre_scan_actions
from CliCaller import check_wrapper

def main():    
    scan_configuration = ScanConfiguration()
    check_wrapper(scan_configuration)

    scan_configuration = pre_scan_actions(scan_configuration)

    if scan_configuration.scan_type == 'folder':
        scan_configuration.source = package_application(scan_configuration.source, scan_configuration)

    if scan_configuration.pipeline_scan:
        start_pipeline_scan(scan_configuration)
    else:
        start_platform_scan(scan_configuration)

if __name__ == '__main__':
    main()
    