from veracode_api_py.identity import BusinessUnits, Teams
from veracode_api_py.collections import Collections
from veracode_api_py.applications import Applications
from veracode_api_py.policy import Policies
from ErrorHandler import exit_with_error

def parse_custom_field(custom_field):
    return {
        "name": custom_field.name,
        "value": custom_field.value
    }

def try_to_run_and_return(input_parameter: str, function_to_run, scan_configuration):
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

def get_application_id(application_name: str, scan_configuration):
    return try_to_run_and_return(application_name, inner_get_application_id, scan_configuration)

def inner_get_application_id(application_name: str):
    matches = Applications().get_by_name(application_name)
    if not matches or len(matches) == 0:
        return None
    for match in matches:
        if match["profile"]["name"] == application_name.strip():
            return match["guid"]
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

def get_team_id(team_name: str, scan_configuration):
    return try_to_run_and_return(team_name, inner_get_team_id, scan_configuration)

def inner_get_team_id(team_name):
    matches = Teams().get_all()
    if not matches or len(matches) == 0:
        return None
    for match in matches:
        if match["team_name"] == team_name.strip():
            return match["team_id"]
    return None

def create_team(team_name: str, scan_configuration):
    return try_to_run_and_return(team_name, inner_create_team, scan_configuration)

def inner_create_team(team_name: str):
    team = Teams().create(team_name)
    return team['team_id']

def create_business_unit(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_create_business_unit, scan_configuration)

def inner_create_business_unit(scan_configuration):
    business_unit = BusinessUnits().create(scan_configuration.business_unit, list(map(lambda team: team.guid, scan_configuration.team_list)))
    return business_unit["bu_id"]

def create_application(scan_configuration):
    return try_to_run_and_return(scan_configuration, inner_create_application, scan_configuration)

def inner_create_application(scan_configuration):
    application = Applications().create(app_name=scan_configuration.application, business_criticality=scan_configuration.business_criticality, 
                                        description=scan_configuration.description, git_repo_url=scan_configuration.git_repo_url,
                                        business_unit=scan_configuration.business_unit_guid, teams=list(map(lambda team: team.guid, scan_configuration.team_list)),
                                        custom_fields=list(map(lambda custom_field: parse_custom_field(custom_field), scan_configuration.application_custom_fields)), 
                                        bus_owner_name=scan_configuration.business_owner, bus_owner_email=scan_configuration.business_owner_email)
    return application["guid"]

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