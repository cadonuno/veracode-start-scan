from veracode_api_py.identity import BusinessUnits, Teams
from veracode_api_py.collections import Collections
from veracode_api_py.applications import Applications
from veracode_api_py.policy import Policies
from veracode_api_py.sca import Workspaces, SCAApplications
from veracode_api_py.policy import Policies
from ErrorHandler import exit_with_error
import pandas as pd

def parse_custom_field(custom_field):
    return {
        "name": custom_field.name,
        "value": custom_field.value
    }

def try_to_run_and_return(input_parameter, function_to_run, scan_configuration):
    try:
        return function_to_run(input_parameter)
    except Exception as e:
        exit_with_error(e, -1, scan_configuration)

def get_business_unit_id(business_unit_name: str, scan_configuration):
    return try_to_run_and_return(business_unit_name, inner_get_business_unit_id, scan_configuration)

def inner_get_business_unit_id(business_unit_name: str):
    matches = BusinessUnits().get_all()
    if not matches or len(matches) == 0:
        return None
    for match in matches:
        if match["bu_name"] == business_unit_name.strip():
            return match["bu_id"]
    return None

def get_application_by_guid(application_guid: str, scan_configuration):
    return try_to_run_and_return(application_guid, inner_get_application_by_guid, scan_configuration)

def inner_get_application_by_guid(application_guid: str):
    return Applications().get(application_guid)

def get_application(application_name: str, scan_configuration):
    return try_to_run_and_return(application_name, inner_get_application, scan_configuration)

def inner_get_application(application_name: str):
    matches = Applications().get_by_name(application_name)
    if not matches or len(matches) == 0:
        return None
    for match in matches:
        if match["profile"]["name"] == application_name.strip():
            return match
    return None


def get_application_policy_name(application_guid: str, scan_configuration):
    return try_to_run_and_return(application_guid, inner_get_application_policy_name, scan_configuration)

def inner_get_application_policy_name(application_guid):
    match = Applications().get(application_guid)
    if not match or len(match) == 0:
        return None
    policy_guid = match["_links"]["policy"]["href"].split("/policies/")[1]
    match = Policies().get(policy_guid)
    if not match or len(match) == 0:
        return None
    return match["name"]

def get_collection_id(collection_name: str, scan_configuration):
    return try_to_run_and_return(collection_name, inner_get_collection_id, scan_configuration)

def inner_get_collection_id(collection_name: str):
    matches = Collections().get_by_name(collection_name)
    if not matches or len(matches) == 0:
        return None
    for match in matches:
        if match["name"] == collection_name.strip():
            return match["guid"]
    return None

def get_team_ids(team_name: str, scan_configuration):
    return try_to_run_and_return(team_name, inner_get_team_ids, scan_configuration)

def inner_get_team_ids(team_name):
    matches = Teams().get_all()
    if not matches or len(matches) == 0:
        return None, None
    for match in matches:
        if match["team_name"] == team_name.strip():
            return match["team_id"], match["team_legacy_id"]
    return None, None

def create_team(team_name: str, scan_configuration):
    return try_to_run_and_return(team_name, inner_create_team, scan_configuration)

def inner_create_team(team_name: str):
    team = Teams().create(team_name)
    return team['team_id'], team["team_legacy_id"]

def create_business_unit(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_create_business_unit, scan_configuration)

def inner_create_business_unit(scan_configuration):
    business_unit = BusinessUnits().create(scan_configuration.business_unit, list(map(lambda team: team.guid, scan_configuration.team_list)))
    return business_unit["bu_id"]

def get_workspace_id(workspace_name: str, scan_configuration):
    return try_to_run_and_return(workspace_name, inner_get_workspace_id, scan_configuration)

def inner_get_workspace_id(workspace_name: str):
    matches = Workspaces().get_by_name(workspace_name)
    if not matches or len(matches) == 0:
        return None
    for match in matches:
        if match["name"] == workspace_name.strip():
            return match["id"]
    return None

def create_application(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_create_application, scan_configuration)

def inner_create_application(scan_configuration):
    application = Applications().create(app_name=scan_configuration.application, business_criticality=scan_configuration.business_criticality, 
                                        description=scan_configuration.description, git_repo_url=scan_configuration.git_repo_url,
                                        business_unit=scan_configuration.business_unit_guid, teams=list(map(lambda team: team.guid, scan_configuration.team_list)),
                                        custom_fields=list(map(lambda custom_field: parse_custom_field(custom_field), scan_configuration.application_custom_fields)), 
                                        bus_owner_name=scan_configuration.business_owner, bus_owner_email=scan_configuration.business_owner_email,
                                        custom_kms_alias=scan_configuration.key_alias)
    return application

def update_application(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_update_application, scan_configuration)

def inner_update_application(scan_configuration):
    application = Applications().update(guid=scan_configuration.application_guid, app_name=scan_configuration.application,business_criticality=scan_configuration.business_criticality, 
                                        description=scan_configuration.description, git_repo_url=scan_configuration.git_repo_url,
                                        business_unit=scan_configuration.business_unit_guid, teams=list(map(lambda team: team.guid, scan_configuration.team_list)),
                                        custom_fields=list(map(lambda custom_field: parse_custom_field(custom_field), scan_configuration.application_custom_fields)), 
                                        bus_owner_name=scan_configuration.business_owner, bus_owner_email=scan_configuration.business_owner_email)
    return application["guid"]

def create_collection(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_create_collection, scan_configuration)

def inner_create_collection(scan_configuration):
    collection = Collections().create(name=scan_configuration.collection, description=scan_configuration.collection_description,
                                    business_unit_guid=scan_configuration.business_unit_guid, 
                                    custom_fields=list(map(lambda custom_field: parse_custom_field(custom_field), scan_configuration.collection_custom_fields)),
                                    assets=[scan_configuration.application_guid])
    return collection["guid"]

def update_collection(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_update_collection, scan_configuration)

def inner_update_collection(scan_configuration):
    collection = Collections().update(guid=scan_configuration.collection_guid, name=scan_configuration.collection, description=scan_configuration.collection_description,
                                    business_unit_guid=scan_configuration.business_unit_guid, 
                                    custom_fields=list(map(lambda custom_field: parse_custom_field(custom_field), scan_configuration.collection_custom_fields)),
                                    assets=[scan_configuration.application_guid])
    return collection["guid"]

def create_workspace(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_create_workspace, scan_configuration)

def inner_create_workspace(scan_configuration):
    workspace = Workspaces().create(name=scan_configuration.workspace_name)
    return workspace

def create_sca_token(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_create_sca_token, scan_configuration)

def inner_create_sca_token(scan_configuration):
    agent = Workspaces().create_agent(scan_configuration.workspace_guid, scan_configuration.sca_agent_name)
    return agent["token"]["access_token"], agent["id"]

def add_teams_to_workspace(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_add_teams_to_workspace, scan_configuration)

def inner_add_teams_to_workspace(scan_configuration):
    for team in scan_configuration.team_list:
        Workspaces().add_team(scan_configuration.workspace_guid, team.legacy_id)
    return True

def expire_srcclr_token(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_expire_srcclr_token, scan_configuration)

def inner_expire_srcclr_token(scan_configuration):
    Workspaces().delete_agent(scan_configuration.workspace_guid, scan_configuration.agent_id)
    return True

def link_sca_project(sca_results_message, scan_configuration):
    return try_to_run_and_return({"scan_id": sca_results_message, "scan_configuration": scan_configuration}, inner_link_sca_project, scan_configuration)

def inner_link_sca_project(linking_information):
    scan_id = linking_information["scan_id"]
    scan_configuration = linking_information["scan_configuration"]
    workspace_id = scan_configuration.workspace_guid
    scan = Workspaces().get_scan(scan_id)
    project_id = get_project_id_for_scan_date(workspace_id, scan["date"])
    if project_id:
        SCAApplications().link_project(scan_configuration.application_guid, project_id)

def get_project_id_for_scan_date(workspace_id, scan_date):
    projects = Workspaces().get_projects(workspace_id)
    if projects:
        for project in projects:
            if are_equal_datetimes(project["last_scan_date"], scan_date):
                return project["id"]
    return ""

def are_equal_datetimes(first_datetime, second_datetime):
    first_datetime = pd.to_datetime(first_datetime)
    second_datetime = pd.to_datetime(second_datetime)
    return first_datetime == second_datetime