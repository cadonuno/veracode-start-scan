import argparse
import os
import urllib.parse
from pathlib import Path
from datetime import datetime
from Constants import ALLOWED_CRITICALITIES, ALLOWED_DELETE_INCOMPLETE_SCAN, SBOM_TYPES, SCAN_TYPES, SCA_URL_MAP
from VeracodeApi import get_application, get_application_by_guid, get_collection_id, get_business_unit_id, get_team_ids, get_workspace_id
from veracode_api_py.apihelper import get_region_for_api_credential
from ErrorHandler import exit_with_error
from ColourHandler import ERROR_PREFIX_COLOUR, RESET_STYLE, INFO_PREFIX_COLOUR, WARNING_MESSAGE_COLOUR

class Team:
    name: str
    guid: str
    legacy_id : str

    def __init__(self, name, scan_configuration):
        self.name = name
        self.guid, self.legacy_id = get_team_ids(name, scan_configuration)

class CustomField:
    name : str
    value : str
    error : str

    def __init__(self, input_argument):
        split_field = input_argument.split(":")
        if not split_field or len(split_field) != 2:
            self.name = None
            self.value = input_argument
            self.error = f"Invalid custom field definition: '{input_argument}'"
        else:
            self.name = split_field[0]
            self.value = split_field[1]
            self.error = None

class ScanConfiguration:
    application : str = None
    description : str = None
    application_tags : str = None
    business_criticality : str = None
    team_list : list[Team] = []
    application_custom_fields : list[CustomField] = []
    git_repo_url : str = None

    collection : str = None
    collection_description : str = None
    collection_tags : str = None
    collection_custom_fields : list[CustomField] = []

    business_unit : str = None
    business_owner : str = None
    business_owner_email : str = None

    scan_type : str = None

    source : str = None
    pipeline_scan : bool = False
    workspace_name : str = None
    sandbox_name : str = None
    fail_build : bool = False
    vid : str = None
    vkey : str = None
    scan_timeout : int = 0
    veracode_cli_location : str = None
    veracode_wrapper_location : str = None
    include : str = None
    exclude : str = None
    scan_all_non_fatal_top_level_modules : bool = False

    application_guid : str = None
    application_legacy_id : str = None
    collection_guid : str = None
    business_unit_guid : str = None
    workspace_guid : str = None
    project_guid : str = None
    sbom_type : str = None
    generated_output_files : list = []

    srcclr_token : str = None
    sca_agent_name : str = None
    policy_name : str = None
    srcclr_api_url : str = None
    agent_id : str = None
    srcclr_to_scan : str = None
    base_cli_directory : str = None
    link_project : bool = False
    verbose : bool = False
    wait_for_timeout : int = 0
    delete_incomplete_scan : int = 0

    proxy_url : str = None
    proxy_port : str = None
    proxy_username : str = None
    proxy_password : str = None

    require_application : bool = False
    skip_application_update : bool = False
    require_collection : bool = False
    skip_collection_update : bool = False
    require_teams : bool = False
    require_business_unit : bool = False
    cleanup_before_start : bool = False
    cleanup_before_exit : bool = False
    has_generated_files : bool = False
    fallback_sandbox : str = None

    def hide_value(self, value):
        return "*" * len(value)

    def append_error(self, errors, field_value, field_name, error_message, mask_value=False):
        errors.append(f"{ERROR_PREFIX_COLOUR}INPUT ERROR:{RESET_STYLE} '{(self.hide_value(field_value) if mask_value else field_value)}' is not a valid value for the {WARNING_MESSAGE_COLOUR}'{field_name}'{RESET_STYLE} parameter - {INFO_PREFIX_COLOUR}{error_message}{RESET_STYLE}")
        return errors

    def validate_field(self, errors, field_value, field_name, error_message, check_function, mask_value=False):
        if field_value and check_function(field_value):
            errors = self.append_error(errors, field_value, field_name, error_message, mask_value)

        return errors

    def validate_list(self, errors, list_to_check, parameter_name, test_funtion, field_value_function, error_function):
        if not list_to_check:
            return errors
        for field_to_check in list_to_check:
            if field_to_check and test_funtion(field_to_check):
                errors = self.append_error(errors, field_value_function(field_to_check), parameter_name, error_function(field_to_check))

        return errors
    
    def validate_field_size(self,errors, field_value, field_name, message_field_name, field_max_size):
        return self.validate_field(errors, field_value, field_name, f"{message_field_name} cannot be longer than {field_max_size} characters", lambda value: len(value) > field_max_size)

    def has_git_folder(self, directory):
        return os.path.isdir(os.path.join(directory, ".git"))

    def get_git_root(self, scan_source):
        current_directory = scan_source
        while current_directory and not self.has_git_folder(current_directory):
            current_directory = Path(current_directory).parent.absolute()
        return current_directory if current_directory else scan_source

    def set_proxy_environment(self, proxy_url: str, proxy_port: str, proxy_username: str, proxy_password: str):
        proxy_url = proxy_url.strip().lower()
        proxy_port = proxy_port.strip().lower()

        protocol = "https" if proxy_url.startswith("https:") else "http"
        proxy_url = proxy_url.replace("https://", "").replace("http://", "")

        proxy_to_use = f"{proxy_url}:{proxy_port}"
        if proxy_username:
            auth_in_url = f"{urllib.parse.quote(proxy_username, safe='')}"
            if proxy_password:
                auth_in_url = f"{auth_in_url}:{urllib.parse.quote(proxy_password, safe='')}"

            proxy_to_use = f"{auth_in_url}@{proxy_to_use}"

        proxy_to_use = f"{protocol}://{proxy_to_use}"
        os.environ['http_proxy'] = proxy_to_use 
        os.environ['HTTP_PROXY'] = proxy_to_use
        os.environ['https_proxy'] = proxy_to_use
        os.environ['HTTPS_PROXY'] = proxy_to_use

    def validate_input(self):        
        errors = []
        errors = self.validate_field_size(errors, self.application, "-a/--application", "Application name", 256)
        application = None
        if self.application:
            self.application = self.application.strip()
            application = get_application(self.application, self)
        elif self.application_guid:
            application = get_application_by_guid(self.application_guid, self)
            if application:
                self.application = application["profile"]["name"]
            else:
                self.append_error(errors, self.application_guid, "-ai/--application_guid", "No application found for GUID")
        else:
            errors.append(f"ERROR: either '-a/--application' (Application Name) or '-ai/--application_guid' (Application GUID) are required to run a scan")

        errors = self.validate_field(errors, self.delete_incomplete_scan, "-del/--delete_incomplete_scan", "Delete Incomplete Scan must be one of these values: 0, 1, 2", lambda delete_incomplete_scan: not delete_incomplete_scan in ALLOWED_DELETE_INCOMPLETE_SCAN)
        if self.pipeline_scan:
            if self.delete_incomplete_scan:
                self.append_error(errors, self.delete_incomplete_scan, "-del/--delete_incomplete_scan", "Pipeline scans do not support (or require) --delete_incomplete_scan")
            if self.exclude:
                self.append_error(errors, self.wait_for_timeout, "-e/--exclude", "Pipeline scans do not support --exclude")
            if self.scan_all_non_fatal_top_level_modules:
                self.append_error(errors, self.scan_all_non_fatal_top_level_modules, "-sanftlm/--scan_all_non_fatal_top_level_modules", "Pipeline scans do not support --scan_all_non_fatal_top_level_modulesclude")
        if self.wait_for_timeout:
            if self.pipeline_scan:
                self.append_error(errors, self.wait_for_timeout, "-wt/--wait_for_timeout", "Pipeline scans do not support (or require) --wait_for_timeout")
            if self.delete_incomplete_scan:
                self.append_error(errors, self.wait_for_timeout, "-wt/--wait_for_timeout", "--delete_incomplete_scan and --wait_for_timeout are mutually exclusive")

        if self.scan_all_non_fatal_top_level_modules and self.exclude:
            self.append_error(errors, self.scan_all_non_fatal_top_level_modules, "-sanftlm/--scan_all_non_fatal_top_level_modules", "-e/--exclude and -sanftlm/--scan_all_non_fatal_top_level_modules are mutually exclusive")

        if application:
            self.application_guid = application["guid"]
            self.application_legacy_id = str(application["id"])

        if not self.application_guid and self.require_application:
            self.append_error(errors, self.application, "-a/--application", "Application does not exist and is required (--require_application was used).")

        errors = self.validate_field_size(errors, self.description, "-desc/--description", "Description", 4000)   
        errors = self.validate_field_size(errors, self.application_tags, "-at/--application_tags", "Application Tags", 512)

        self.business_criticality = self.business_criticality.strip().upper()
        errors = self.validate_field(errors, self.business_criticality, "-bc/--business_criticality", "Business Criticality must be one of these values: Very High, High, Medium, Low, Very Low", lambda business_criticality: not business_criticality in ALLOWED_CRITICALITIES)
        self.business_criticality = self.business_criticality.replace(" ", "_")

        errors = self.validate_list(errors, self.application_custom_fields, "-ac/--application_custom_field", lambda custom_field: custom_field.error, lambda custom_field: custom_field.value, lambda custom_field: custom_field.error)
        errors = self.validate_field_size(errors, self.git_repo_url, "-url/--git_repo_url", "Git Repo URL", 512)

        errors = self.validate_field_size(errors, self.collection, "-c/--collection", "Collection name", 256)
        if self.collection:
            self.collection_guid = get_collection_id(self.collection, self)

        if not self.collection_guid and self.require_collection:
            self.append_error(errors, self.application, "-c/--collection", "Collection does not exist and is required (--require_collection was used).")

        errors = self.validate_field_size(errors, self.collection_description, "-cd/--collection_description", "Collection Description", 4000)
        errors = self.validate_field_size(errors, self.collection_tags, "-ct/--collection_tags", "Collection Tags", 512)
        errors = self.validate_list(errors, self.collection_custom_fields, "-cc/--collection_custom_field", lambda custom_field: custom_field.error, lambda custom_field: custom_field.value, lambda custom_field: custom_field.error)
        if not self.collection:
            errors = self.validate_field(errors, self.collection_description, "-cd/--collection_description", "Collection Description requires a collection", lambda collection_description: bool(collection_description))
            errors = self.validate_field(errors, self.collection_tags, "-ct/--collection_tags", "Collection Tags require a collection", lambda collection_tags: bool(collection_tags))
            errors = self.validate_field(errors, self.collection_custom_fields, "-cc/--collection_custom_field", "Collection Custom Field requires a collection", lambda collection_custom_fields: bool(collection_custom_fields))

        if self.business_unit:
            self.business_unit_guid = get_business_unit_id(self.business_unit, self)
            if self.require_business_unit and not self.business_unit_guid:
                self.append_error(errors, self.business_unit, "-bu/--business_unit", "Business unit does not exist and is required (--require_business_unit was used).")

        errors = self.validate_field_size(errors, self.business_owner, "-bo/--business_owner", "Business Owner name", 128)
        errors = self.validate_field_size(errors, self.business_owner_email, "-boe/--business_owner_email", "Business Owner E-mail", 256)

        errors = self.validate_list(errors, self.team_list, "-t/--team", lambda team: len(team.name) > 256, lambda team: team.name, lambda _: "Team name cannot be longer than 256 characters")
        if self.require_teams:
            self.validate_list(errors, self.team_list, "-t/--team", lambda team: not team.guid, lambda team: team.name, lambda _: "Team does not exist and is required (--require_teams was used).")
        
        self.scan_type = self.scan_type.replace(" ", "").lower() if self.scan_type else ""
        errors = self.validate_field(errors, self.scan_type, "-st/--scan_type", "Type must be one of these values: folder, artifact", lambda scan_type: not scan_type in SCAN_TYPES)
        if self.scan_type == 'artifact':
            errors = self.validate_field(errors, self.ignore_artifacts, "-ia/--ignore_artifact", "Ignore Artifact is only available for --scan_type 'folder'", lambda collection_description: bool(collection_description))

        errors = self.validate_field(errors, self.source, "-s/--source", f"File not found {self.source}", lambda source: not os.path.exists(source))
        if self.scan_type and self.scan_type == "artifact":
            if self.cleanup_before_start:
                errors = self.append_error(errors, self.cleanup_before_start, "-cbs/--cleanup_before_start", "Clearing the build output directory before running a build is only available for --scan_type 'folder'")
            if self.cleanup_before_exit:
                errors = self.append_error(errors, self.cleanup_before_exit, "-cbe/--cleanup_before_exit", "Clearing the build output directory after running a scan is only available for --scan_type 'folder'")

        if self.pipeline_scan and self.sandbox_name:
            errors = self.append_error(errors, self.sandbox_name, "-sn/--sandbox_name", "Pipeline scan does not support a sandbox name")            
        
        errors = self.validate_field_size(errors, self.sandbox_name, "-sn/--sandbox_name", "Sandbox name", 256)

        if self.pipeline_scan and self.version:
            errors = self.append_error(errors, self.version, "-v/--version", "Pipeline scan does not support a scan name")
        if not self.pipeline_scan and not self.version:
            errors = self.append_error(errors, self.version, "-v/--version", "Scan name is required for Policy and Sandbox scans")

        errors = self.validate_field_size(errors, self.workspace_name, "-wn/--workspace_name", "Workspace Name", 512)
        if self.workspace_name:
            self.workspace_guid = get_workspace_id(self.workspace_name, self)
            now = datetime.now()
            self.sca_agent_name = f"{now.year}{now.month}{now.day}{now.hour}{now.minute}{now.second}{now.microsecond}"
            self.srcclr_api_url = SCA_URL_MAP[get_region_for_api_credential(self.vid)]
        self.sbom_type = self.sbom_type.replace(" ", "").upper() if self.sbom_type else ""
        errors = self.validate_field(errors, self.sbom_type, "-sbom/--sbom_type", "SBOM Type must be one of these values: CYCLONEDX, SPDX", lambda sbom_type: not sbom_type in SBOM_TYPES)
        if self.sbom_type and not self.scan_timeout and not self.workspace_name:
            errors = self.append_error(errors, self.sbom_type, "-sbom/--sbom_type", "For fetching an SBOM --scan_timeout or --workspace_name needs to be set")

        errors = self.validate_field_size(errors, self.version, "-v/--version", "Scan name", 256)

        errors = self.validate_field(errors, self.veracode_cli_location, "-cli/--veracode_cli_location", "Invalid or not found Veracode CLI Location", lambda veracode_cli: not os.path.isfile(veracode_cli))
        errors = self.validate_field(errors, self.veracode_wrapper_location, "-wra/--veracode_wrapper_location", "Invalid or not found Veracode Java API Wrapper", lambda wrapper: not os.path.isfile(wrapper))

        if self.workspace_name:
            self.srcclr_to_scan = self.get_git_root(self.source)

        self.base_cli_directory = os.path.join(os.path.realpath(__file__), self.source)
        if not os.path.isdir(self.base_cli_directory):
            self.base_cli_directory = os.path.dirname(self.base_cli_directory)

        if not self.proxy_url:
            errors = self.validate_field(errors, self.proxy_port, "-pport/--proxy_port", "To use proxy, a URL must be set", lambda port: bool(port))
            errors = self.validate_field(errors, self.proxy_username, "-puser/--proxy_username", "To use proxy, a URL must be set", lambda username: bool(username))
            errors = self.validate_field(errors, self.proxy_password, "-ppass/--proxy_password", "To use proxy, a URL must be set", lambda password: bool(password), mask_value=True)
        else:
            if not self.proxy_port:            
                errors = self.append_error(errors, "''", "-pport/--proxy_port", "To use proxy, a port must be set")
            if self.proxy_password and not self.proxy_username:
                errors = self.append_error(errors, "''", "-ppass/--proxy_password", "A proxy password requires a proxy username (-puser/--proxy_username)", mask_value=True)

        if errors:
            exit_with_error(errors, len(errors)*-1, self)
        if self.proxy_url:
            self.set_proxy_environment(self.proxy_url, self.proxy_port, self.proxy_username, self.proxy_password)
        if self.wait_for_timeout:
            self.wait_for_timeout = int(self.wait_for_timeout)

    def parse_custom_field_list(self, custom_field_list):
        return list(map(lambda custom_field: CustomField(custom_field), custom_field_list)) if custom_field_list else []

    def parse_team_list(self, team_list):
        return list(map(lambda team_name: Team(team_name, self), team_list)) if team_list else []

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="This script starts a scan in Veracode."
        )

        #Application Parameters:
        parser.add_argument(
            "-ai",
            "--application_guid",
            help="GUID of the application to scan.",
            required=False
        )
        parser.add_argument(
            "-a",
            "--application",
            help="Name of the application to scan, replaces --application_guid and will create an application if it doesn't exist.",
            required=False
        )
        parser.add_argument(
            "-ra",
            "--require_application",
            help="(optional) Pass this flag to fail the build if the application does not exist - used to avoid creating new applications",
            required=False,
            action=argparse.BooleanOptionalAction,
        )
        parser.add_argument(
            "-sau",
            "--skip_application_update",
            help="(optional) Pass this flag to skip the application update - does nothing if the application does NOT exist.",
            required=False,
            action=argparse.BooleanOptionalAction,
        )
        parser.add_argument(
            "-desc",
            "--description",
            help="(optional) Description of the application - if the application already exists, it WILL be updated.",
            required=False
        )
        parser.add_argument(
            "-at",
            "--application_tags",
            help="(optional) Tags to be added to the application - if the application already exists, it WILL be updated",
            required=False
        )
        parser.add_argument(
            "-bc",
            "--business_criticality",
            help="Business criticality of the application - if the application already exists, it WILL be updated.",
            required=True
        )
        parser.add_argument(
            "-ac",
            "--application_custom_field",
            help="(optional) Colon(:)-separated key-value pairs for the custom fields to set for the APPLICATION PROFILE, takes 0 or more. I.e.: A Field:Some Value.",
            action="append",
            required=False
        )
        parser.add_argument(
            "-url",
            "--git_repo_url",
            help="(optional) URL of the git repository scanned.",
            required=False
        )
        parser.add_argument(
            "-ka",
            "--key_alias",
            help="(optional) If using CMKs, sets the key alias to use for this application - if the application already exists, will NOT be updated.",
            required=False
        )

        #Collection Parameters:
        parser.add_argument(
            "-c",
            "--collection",
            help="(optional) Name of the collection to assign to the application - will be created if none are found.",
            required=False
        )
        parser.add_argument(
            "-rc",
            "--require_collection",
            help="(optional) Pass this flag to fail the build if the collection does not exist - used to avoid creating new collections.",
            required=False,
            action=argparse.BooleanOptionalAction,
        )
        parser.add_argument(
            "-scu",
            "--skip_collection_update",
            help="(optional) Pass this flag to skip the collection update - does nothing if the collection does NOT exist.",
            required=False,
            action=argparse.BooleanOptionalAction,
        )
        parser.add_argument(
            "-cd",
            "--collection_description",
            help="(optional) Description of the collection - if the collection already exists, it WILL be updated.",
            required=False
        )
        parser.add_argument(
            "-ct",
            "--collection_tags",
            help="(optional) Tags to be added to the collection - if the collection already exists, it WILL be updated",
            required=False
        )
        parser.add_argument(
            "-cc",
            "--collection_custom_field",
            help="(optional) Colon(:)-separated key-value pairs for the custom fields to set for the COLLECTION, takes 0 or more. I.e.: A Field:Some Value.",
            action="append",
            required=False
        )

        #Both:
        parser.add_argument(
            "-t",
            "--team",
            help="Teams to assign to the application, takes 1 or more - if a team does not exist, it will be created and if the application/collection exists, it WILL be updated.",
            action="append",
            required=True
        )
        parser.add_argument(
            "-rt",
            "--require_teams",
            help="(optional) Pass this flag to fail the build if any teams do not exist - used to avoid creating new teams.",
            required=False,
            action=argparse.BooleanOptionalAction,
        )
        parser.add_argument(
            "-b",
            "--business_unit",
            help="(optional) Name of the Business unit to assign to the application AND collection - if the BU does not exist, it will be created and if the application/collection exists, it WILL be updated.",
            required=False
        )
        parser.add_argument(
            "-rbu",
            "--require_business_unit",
            help="(optional) Pass this flag to fail the build if the business unit does not exist - used to avoid creating new business units.",
            required=False,
            action=argparse.BooleanOptionalAction,
        )
        parser.add_argument(
            "-bo",
            "--business_owner",
            help="(optional) Name of the business owner - if the application/collection exists, it WILL be updated.",
            required=False
        )
        parser.add_argument(
            "-boe",
            "--business_owner_email",
            help="(optional) E-mail of the business owner - if the application/collection exists, it WILL be updated.",
            required=False
        )

        #Scan parameters
        parser.add_argument(
            "-st",
            "--scan_type",
            help="Type of scan, either 'folder' or 'artifact'.",
            required=True
        )
        parser.add_argument(
            "-s",
            "--source",
            help="Source for the scan. For 'folder', will call the Veracode packager on it, otherwise, will send it directly to the scanner.",
            required=True
        )
        parser.add_argument(
            "-cbs",
            "--cleanup_before_start",
            help="(optional) Pass this flag to clear the build output directory before calling a build. Only available for --scan_type 'folder'.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-ps",
            "--pipeline_scan",
            help="(optional) Pass this flag to run a pipeline scan. If set, will fetch the policy assigned to the application profile (if one exists) before proceeding - does NOT support a Sandbox name.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-wn",
            "--workspace_name",
            help="(optional) Name of the workspace to use for Agent-based SCA scans - If empty and using the Pipeline Scanner, SCA results will not be generated.",
            required=False
        )
        parser.add_argument(
            "-sbom",
            "--sbom_type",
            help="(optional) Set the type of SBOM to fetch for the project after the scan - if using Policy/Sandbox scan, requires a scan_timeout.",
            required=False,
        )
        parser.add_argument(
            "-lp",
            "--link_project",
            help="(optional) Pass this flag to link the agent SCA project to the Application profile (requires a workspace name).",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-sn",
            "--sandbox_name",
            help="(optional) Name of the sandbox to use for the scan, leave empty to run a Policy Scan.",
            required=False
        )
        parser.add_argument(
            "-v",
            "--version",
            help="Name of the scan/version - has to be unique for each application/sandbox combo and does NOT support pipeline scans - mandatory if not using -ps/--pipeline_scan.",
            required=False
        )
        parser.add_argument(
            "-del",
            "--delete_incomplete_scan",
            help="(optional) Sets a value for the -deleteincompletescan parameter for the upload and scan action (not supported, or needed, for the pipeline scan).",
            required=False
        )
        parser.add_argument(
            "-wt",
            "--wait_for_timeout",
            help="(optional) Sets a timeout (in minutes) to wait for the previous scan to complete before trying to start a new scan (not supported or needed for the pipeline scan, or if using --delete_incomplete_scan).",
            required=False
        )
        parser.add_argument(
            "-vid",
            "--veracode_api_key_id",
            help="Veracode API key ID to use - a non-human/API account is recommended.",
            required=True
        )

        parser.add_argument(
            "-vkey",
            "--veracode_api_key_secret",
            help="Veracode API key secret to use - a non-human/API account is recommended.",
            required=True
        )
        parser.add_argument(
            "-purl",
            "--proxy_url",
            help="(Optional) URL of proxy server to use.",
            required=False
        )
        parser.add_argument(
            "-pport",
            "--proxy_port",
            help="(Optional) Port of proxy server to use.",
            required=False
        )
        parser.add_argument(
            "-puser",
            "--proxy_username",
            help="(Optional) Username to use to authenticate to proxy.",
            required=False
        )
        parser.add_argument(
            "-ppass",
            "--proxy_password",
            help="(Optional) Password to use to authenticate to proxy.",
            required=False
        )
        parser.add_argument(
            "-sct",
            "--scan_timeout",
            help="(optional) Scan timeout (in minutes). If empty or 0, will not wait for Sandbox/Policy scans to complete.",
            required=False
        )
        parser.add_argument(
            "-f",
            "--fail_build",
            help="(optional) Pass this flag to fail the build if application fails policy evaluation.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-o",
            "--override_failure",
            help="(optional) Pass this flag to return a 0 on error. This can be used to avoid breaking a pipeline.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-cli",
            "--veracode_cli_location",
            help="Location of the Veracode CLI installation.",
            required=True
        )
        parser.add_argument(
            "-wra",
            "--veracode_wrapper_location",
            help="Location of the Veracode API Wrapper jar.",
            required=True
        )
        parser.add_argument(
            "-i",
            "--include",
            help="(optional) Case-sensitive, comma-separated list of module name patterns that represent the names of modules to scan as top-level modules. The * wildcard matches 0 or more characters. The ? wildcard matches exactly one character.",
            required=False
        )
        parser.add_argument(
            "-e",
            "--exclude",
            help="(optional) Case-sensitive, comma-separated list of module name patterns that represent the names of modules NOT to scan as top-level modules. The * wildcard matches 0 or more characters. The ? wildcard matches exactly one character.",
            required=False
        )
        parser.add_argument(
            "-sanftlm",
            "--scan_all_non_fatal_top_level_modules",
            help="(optional) Pass this flag to continue scanning even if there are fatal errors in some (but not all) modules.",
            required=False,
            action=argparse.BooleanOptionalAction
        )

        parser.add_argument(
            "-ia",
            "--ignore_artifact",
            help="(optional) Artifacts not to scan, takes 0 or more - use to not try scanning specific artifacts generated by the Veracode Packager, only works with --scan_type 'folder'.",
            action="append",
            required=False
        )
        parser.add_argument(
            "-cbe",
            "--cleanup_before_exit",
            help="(optional) Pass this flag to delete the scanned files on exit - does nothing for --scan_type 'artifact'.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-d",
            "--debug",
            help="(optional) Pass this flag to output verbose logging.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-fs",
            "--fallback_sandbox",
            help="(optional) Sandbox name to fallback to if packaged application is bigger than 200MB (pipeline scan limit).",
            required=False
        )

        args = parser.parse_args()

        os.environ['veracode_api_key_id'] = args.veracode_api_key_id
        os.environ['VERACODE_API_KEY_ID'] = args.veracode_api_key_id
        os.environ['veracode_api_key_secret'] = args.veracode_api_key_secret
        os.environ['VERACODE_API_KEY_SECRET'] = args.veracode_api_key_secret
        self.application = args.application
        self.application_guid = args.application_guid
        self.description = args.description
        self.application_tags = args.application_tags
        self.business_criticality = args.business_criticality
        self.team_list = self.parse_team_list(args.team)
        self.application_custom_fields = self.parse_custom_field_list(args.application_custom_field)
        self.collection = args.collection
        self.collection_description = args.collection_description
        self.collection_tags = args.collection_tags
        self.collection_custom_fields = self.parse_custom_field_list(args.collection_custom_field)
        self.business_unit = args.business_unit
        self.business_owner = args.business_owner
        self.business_owner_email = args.business_owner_email
        self.scan_type = args.scan_type
        self.source = args.source
        self.pipeline_scan = args.pipeline_scan
        self.workspace_name = args.workspace_name
        self.sbom_type = args.sbom_type
        self.sandbox_name = args.sandbox_name
        self.version = args.version
        self.fail_build = args.fail_build        
        self.override_failure = args.override_failure
        self.vid = args.veracode_api_key_id
        self.vkey = args.veracode_api_key_secret        
        self.scan_timeout = args.scan_timeout
        self.veracode_cli_location = args.veracode_cli_location
        self.veracode_wrapper_location = args.veracode_wrapper_location
        self.include = args.include
        self.exclude = args.exclude
        self.scan_all_non_fatal_top_level_modules = args.scan_all_non_fatal_top_level_modules
        self.git_repo_url = args.git_repo_url
        self.ignore_artifacts = args.ignore_artifact
        self.key_alias = args.key_alias
        self.link_project = args.link_project
        self.verbose = args.debug
        self.delete_incomplete_scan = args.delete_incomplete_scan
        self.wait_for_timeout = args.wait_for_timeout
        self.proxy_url = args.proxy_url
        self.proxy_port = args.proxy_port
        self.proxy_username = args.proxy_username
        self.proxy_password = args.proxy_password
        self.require_application = args.require_application
        self.skip_application_update = args.skip_application_update
        self.require_collection = args.require_collection
        self.skip_collection_update = args.skip_collection_update
        self.require_business_unit = args.require_business_unit
        self.require_teams = args.require_teams
        self.cleanup_before_start = args.cleanup_before_start
        self.cleanup_before_exit = args.cleanup_before_exit
        self.fallback_sandbox = args.fallback_sandbox

        self.validate_input()
