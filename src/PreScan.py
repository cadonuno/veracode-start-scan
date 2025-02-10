from ScanConfiguration import ScanConfiguration
from VeracodeApi import create_business_unit, create_team, create_application, create_collection, update_collection, update_application, create_workspace, create_sca_token, get_application_policy_name, add_teams_to_workspace

def pre_scan_actions(scan_configuration: ScanConfiguration):
    new_team_list = []
    if scan_configuration.team_list:
        for team in scan_configuration.team_list:
            new_team = team
            if not team.guid:
                new_team.guid, new_team.legacy_id = create_team(new_team.name, scan_configuration)
            new_team_list.append(new_team)

        scan_configuration.team_list = new_team_list
    
    if scan_configuration.business_unit and not scan_configuration.business_unit_guid:
        scan_configuration.business_unit_guid = create_business_unit(scan_configuration)

    if not scan_configuration.application_guid:
        application = create_application(scan_configuration)
        scan_configuration.application_guid = application["guid"]
        scan_configuration.application_legacy_id = str(application["id"])
    else:
        update_application(scan_configuration)

    if scan_configuration.pipeline_scan:
        scan_configuration.policy_name = get_application_policy_name(scan_configuration.application_guid, scan_configuration)

    if scan_configuration.collection:
        if not scan_configuration.collection_guid:
            scan_configuration.collection_guid = create_collection(scan_configuration)
        else:
            update_collection(scan_configuration)

    if scan_configuration.workspace_name:
        if not scan_configuration.workspace_guid:
            scan_configuration.workspace_guid = create_workspace(scan_configuration)
        add_teams_to_workspace(scan_configuration)
        scan_configuration.srcclr_token, scan_configuration.agent_id = create_sca_token(scan_configuration)

    return scan_configuration
