from ScanConfiguration import ScanConfiguration
from VeracodeApi import create_business_unit, create_team, create_application, create_collection, update_collection, update_application
from CliCaller import call_subprocess

def pre_scan_actions(scan_configuration: ScanConfiguration):
    new_team_list = []
    for team in scan_configuration.team_list:
        new_team = team
        if not team.guid:
            new_team.guid = create_team(new_team.name, scan_configuration)
        new_team_list.append(new_team)

    scan_configuration.team_list = new_team_list
    
    if not scan_configuration.business_unit_guid:
        scan_configuration.business_unit_guid = create_business_unit(scan_configuration)

    if not scan_configuration.application_guid:
        scan_configuration.application_guid = create_application(scan_configuration)
    else:
        update_application(scan_configuration)


    if not scan_configuration.collection_guid:
        scan_configuration.collection_guid = create_collection(scan_configuration)
    else:
        update_collection(scan_configuration)

    return scan_configuration
