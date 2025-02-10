import argparse
import os
from pathlib import Path
from datetime import datetime
from Constants import ALLOWED_CRITICALITIES, ALLOWED_DELETE_INCOMPLETE_SCAN, SCAN_TYPES, SCA_URL_MAP
from VeracodeApi import get_application, get_application_by_guid, get_collection_id, get_business_unit_id, get_team_ids, get_workspace_id
from veracode_api_py.apihelper import get_region_for_api_credential
from ErrorHandler import exit_with_error, show_warning

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
    business_criticality : str = None
    team_list : list[Team] = []
    application_custom_fields : list[CustomField] = []
    git_repo_url : str = None

    collection : str = None
    collection_description : str = None
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

    application_guid : str = None
    application_legacy_id : str = None
    collection_guid : str = None
    business_unit_guid : str = None
    workspace_guid : str = None
    srcclr_token : str = None
    sca_agent_name : str = None
    policy_name : str = None
    srcclr_api_url : str = None
    agent_id : str = None
    srcclr_to_scan : str = None
    base_cli_directory : str = None
    link_project : bool = False
    verbose : bool = False
    delete_incomplete_scan : int = 0

    def append_error(self, errors, field_value, field_name, error_message):
        errors.append(f"ERROR: '{field_value}' is not a valid value for the '{field_name}' parameter - {error_message}")
        return errors

    def validate_field(self, errors, field_value, field_name, error_message, check_function):
        if field_value and check_function(field_value):
            errors = self.append_error(errors, field_value, field_name, error_message)

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

    def validate_input(self):
        os.environ['veracode_api_key_id'] = self.vid
        os.environ['veracode_api_key_secret'] = self.vkey
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
            
        if application:
            self.application_guid = application["guid"]
            self.application_legacy_id = str(application["id"])
            
        if self.application_guid and self.key_alias:
            show_warning("Application already exists, key alias will be IGNORED")

        errors = self.validate_field_size(errors, self.description, "-desc/--description", "Description", 4000)   

        self.business_criticality = self.business_criticality.strip().upper()
        errors = self.validate_field(errors, self.business_criticality, "-bc/--business_criticality", "Business Criticality must be one of these values: Very High, High, Medium, Low, Very Low", lambda business_criticality: not business_criticality in ALLOWED_CRITICALITIES)
        self.business_criticality = self.business_criticality.replace(" ", "_")

        errors = self.validate_list(errors, self.application_custom_fields, "-ac/--application_custom_field", lambda custom_field: custom_field.error, lambda custom_field: custom_field.value, lambda custom_field: custom_field.error)
        errors = self.validate_field_size(errors, self.git_repo_url, "-url/--git_repo_url", "Git Repo URL", 512)

        errors = self.validate_field_size(errors, self.collection, "-c/--collection", "Collection name", 256)
        if self.collection:
            self.collection_guid = get_collection_id(self.collection, self)
        errors = self.validate_field_size(errors, self.collection_description, "-cd/--collection_description", "Collection Description", 4000)
        errors = self.validate_list(errors, self.collection_custom_fields, "-cc/--collection_custom_field", lambda custom_field: custom_field.error, lambda custom_field: custom_field.value, lambda custom_field: custom_field.error)
        if not self.collection:
            errors = self.validate_field(errors, self.collection_description, "-cd/--collection_description", "Collection Description requires a collection", lambda collection_description: bool(collection_description))
            errors = self.validate_field(errors, self.collection_custom_fields, "-cc/--collection_custom_field", "Collection Custom Field requires a collection", lambda collection_custom_fields: bool(collection_custom_fields))


        if self.business_unit:
            self.business_unit_guid = get_business_unit_id(self.business_unit, self)
        errors = self.validate_field_size(errors, self.business_owner, "-bo/--business_owner", "Business Owner name", 128)
        errors = self.validate_field_size(errors, self.business_owner_email, "-boe/--business_owner_email", "Business Owner E-mail", 256)

        errors = self.validate_list(errors, self.team_list, "-t/--team", lambda team: len(team.name) > 256, lambda team: team.name, lambda _: "Team name cannot be longer than 256 characters")
        
        self.scan_type = self.scan_type.replace(" ", "").lower() if self.scan_type else ""
        errors = self.validate_field(errors, self.scan_type, "-st/--scan_type", "Type must be one of these values: folder, artifact", lambda scan_type: not scan_type in SCAN_TYPES)
        if self.scan_type == 'artifact':
            errors = self.validate_field(errors, self.ignore_artifact, "-ia/--ignore_artifact", "Ignore Artifact is only available for --scan_type 'folder'", lambda collection_description: bool(collection_description))

        errors = self.validate_field(errors, self.source, "-s/--source", f"File not found {self.source}", lambda source: not os.path.exists(source))
        if self.pipeline_scan and self.sandbox_name:
            errors = self.append_error(errors, self.sandbox_name, "-sn/--sandbox_name", "Pipeline scan does not support a sandbox name")
        
        errors = self.validate_field_size(errors, self.sandbox_name, "-sn/--sandbox_name", "Sandbox name", 256)

        if self.pipeline_scan and self.version:
            errors = self.append_error(errors, self.version, "-v/--version", "Pipeline scan does not support a scan name")
        if not self.pipeline_scan and self.workspace_name:
            errors = self.append_error(errors, self.workspace_name, "-wn/--workspace_name", "Agent-based SCA is only supported when running pipeline scans. *Requires the SCA Agent to be installed")
        if not self.pipeline_scan and not self.version:
            errors = self.append_error(errors, self.version, "-v/--version", "Scan name is required for Policy and Sandbox scans")

        errors = self.validate_field_size(errors, self.workspace_name, "-wn/--workspace_name", "Workspace Name", 512)
        if self.workspace_name:
            self.workspace_guid = get_workspace_id(self.workspace_name, self)
            now = datetime.now()
            self.sca_agent_name = f"{now.year}{now.month}{now.day}{now.hour}{now.minute}{now.second}{now.microsecond}"
            self.srcclr_api_url = SCA_URL_MAP[get_region_for_api_credential(self.vid)]

        errors = self.validate_field_size(errors, self.version, "-v/--version", "Scan name", 256)

        errors = self.validate_field(errors, self.veracode_cli_location, "-cli/--veracode_cli_location", "Invalid or not found Veracode CLI Location", lambda veracode_cli: not os.path.isfile(veracode_cli))
        errors = self.validate_field(errors, self.veracode_wrapper_location, "-wra/--veracode_wrapper_location", "Invalid or not found Veracode Java API Wrapper", lambda wrapper: not os.path.isfile(wrapper))

        if self.workspace_name:
            self.srcclr_to_scan = self.get_git_root(self.source)

        self.base_cli_directory = os.path.join(os.path.realpath(__file__), self.source)
        if not os.path.isdir(self.base_cli_directory):
            self.base_cli_directory = os.path.dirname(self.base_cli_directory)

        if errors:
            exit_with_error(errors, len(errors)*-1, self)

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
            "-desc",
            "--description",
            help="(optional) Description of the application - if the application already exists, it WILL be updated.",
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
            "-cd",
            "--collection_description",
            help="(optional) Description of the collection - if the collection already exists, it WILL be updated.",
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
            "-b",
            "--business_unit",
            help="(optional) Name of the Business unit to assign to the application AND collection - if the BU does not exist, it will be created and if the application/collection exists, it WILL be updated.",
            required=False
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
            "-ps",
            "--pipeline_scan",
            help="(optional) Set to run a pipeline scan. If set, will fetch the policy assigned to the application profile (if one exists) before proceeding - does NOT support a Sandbox name.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-wn",
            "--workspace_name",
            help="(optional) Name of the workspace to use for Agent-based SCA scans. Only used if -ps is true - If empty, SCA will not be run alongside the Pipeline Scan.",
            required=False
        )
        parser.add_argument(
            "-lp",
            "--link_project",
            help="(optional) Set to link the agent SCA project to the Application profile (requires a workspace name).",
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
            "-sct",
            "--scan_timeout",
            help="(optional) Scan timeout (in minutes). If empty or 0, will not wait for Sandbox/Policy scans to complete.",
            required=False
        )
        parser.add_argument(
            "-f",
            "--fail_build",
            help="(optional) Set to fail the build if application fails policy evaluation.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-o",
            "--override_failure",
            help="(optional) Set to return a 0 on error. This can be used to avoid breaking a pipeline.",
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
            "-ia",
            "--ignore_artifact",
            help="(optional) Artifacts not to scan, takes 0 or more - use to not try scanning specific artifacts generated by the Veracode Packager, only works with --scan_type 'folder'.",
            action="append",
            required=False
        )
        parser.add_argument(
            "-d",
            "--debug",
            help="(optional) Set to output verbose logging.",
            required=False,
            action=argparse.BooleanOptionalAction
        )

        args = parser.parse_args()
        self.application = args.application
        self.application_guid = args.application_guid
        self.description = args.description
        self.business_criticality = args.business_criticality
        self.team_list = self.parse_team_list(args.team)
        self.application_custom_fields = self.parse_custom_field_list(args.application_custom_field)
        self.collection = args.collection
        self.collection_description = args.collection_description
        self.collection_custom_fields = self.parse_custom_field_list(args.collection_custom_field)
        self.business_unit = args.business_unit
        self.business_owner = args.business_owner
        self.business_owner_email = args.business_owner_email
        self.scan_type = args.scan_type
        self.source = args.source
        self.pipeline_scan = args.pipeline_scan
        self.workspace_name = args.workspace_name
        self.sandbox_name = args.sandbox_name
        self.version = args.version
        self.fail_build = args.fail_build        
        self.override_failure = args.override_failure
        self.vid = args.veracode_api_key_id
        self.vkey = args.veracode_api_key_secret        
        self.scan_timeout = args.scan_timeout
        self.veracode_cli_location = args.veracode_cli_location
        self.veracode_wrapper_location = args.veracode_wrapper_location
        self.git_repo_url = args.git_repo_url
        self.ignore_artifacts = args.ignore_artifact
        self.key_alias = args.key_alias
        self.link_project = args.link_project
        self.verbose = args.debug
        self.delete_incomplete_scan = args.delete_incomplete_scan

        self.validate_input()
