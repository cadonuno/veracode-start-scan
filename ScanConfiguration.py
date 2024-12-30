import argparse
import os
from Constants import ALLOWED_CRITICALITIES, SCAN_TYPES
from VeracodeApi import get_application_id, get_collection_id, get_business_unit_id, get_team_id, get_application_policy_name
from ErrorHandler import exit_with_error

class Team:
    name: str
    guid: str

    def __init__(self, name, scan_configuration):
        self.name = name
        self.guid = get_team_id(name, scan_configuration)

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
    application : str
    description : str
    business_criticality : str
    team_list : list[Team]
    application_custom_fields : list[CustomField]

    collection : str
    collection_description : str
    collection_custom_fields : list[CustomField]

    business_unit : str
    business_owner : str
    business_owner_email : str

    type : str

    source : str
    pipeline_scan : bool
    sandbox_name : str
    fail_build : bool
    vid : str
    vkey : str
    scan_timeout : int

    application_guid : str
    collection_guid : str
    business_unit_guid : str    
    policy_name : str

    def append_error(self, errors, field_value, field_name, error_message):
        errors.append(f"ERROR: '{field_value}' is not a valid value for the '{field_name}' parameter - {error_message}")
        return errors

    def validate_field(self, errors, field_value, field_name, error_message, check_function):
        if field_value and check_function(field_value):
            errors = self.append_error(errors, field_value, field_name, error_message)

        return errors

    def validate_list(self, errors, list_to_check, parameter_name, test_funtion, field_value_function, error_function):
        for custom_field in list_to_check:
            if custom_field and test_funtion(custom_field):
                errors = self.append_error(errors, field_value_function(custom_field), parameter_name, error_function(custom_field))

        return errors

    def validate_input(self):
        errors = []
        errors = self.validate_field(errors, self.application, "-a/--application", "Application name cannot be longer than 256 characters", lambda application: len(application) > 256)
        self.application_guid = get_application_id(self.application, self)

        errors = self.validate_field(errors, self.description, "-d/--description", "Description cannot be longer than 4000 characters", lambda description: len(description) > 4000)
        errors = self.validate_field(errors, self.business_criticality, "-bc/--business_criticality", "Business Criticality must be one of these values: VeryHigh, High, Medium, Low, VeryLow", lambda business_criticality: not business_criticality.replace(" ", "").lower() in ALLOWED_CRITICALITIES)
        errors = self.validate_list(errors, self.application_custom_fields, "-ac/--application_custom_field", lambda custom_field: custom_field.error, lambda custom_field: custom_field.value, lambda custom_field: custom_field.error)

        errors = self.validate_field(errors, self.collection, "-c/--collection", "Collection name cannot be longer than 256 characters", lambda collection: len(collection) > 256)
        self.collection_guid = get_collection_id(self.collection, self)
        errors = self.validate_field(errors, self.collection_description, "-cd/--collection_description", "Collection Description cannot be longer than 4000 characters", lambda description: len(description) > 4000)
        errors = self.validate_list(errors, self.collection_custom_fields, "-cc/--collection_custom_field", lambda custom_field: custom_field.error, lambda custom_field: custom_field.value, lambda custom_field: custom_field.error)

        if self.business_unit:
            self.business_unit_guid = get_business_unit_id(self.business_unit, self)
        errors = self.validate_field(errors, self.business_owner, "-bo/--business_owner", "Business Owner name cannot be longer than 128 characters", lambda business_owner: len(business_owner) > 128)
        errors = self.validate_field(errors, self.business_owner_email, "-boe/--business_owner_email", "Business Owner e-mail cannot be longer than 256 characters", lambda business_owner_email: len(business_owner_email) > 256)

        errors = self.validate_list(errors, self.team_list, "-t/--team", lambda team: len(team.name) > 256, lambda team: team.name, lambda _: "Team name cannot be longer than 256 characters")
        
        errors = self.validate_field(errors, self.type, "-st/--scan_type", "Type must be one of these values: folder, artifact", lambda type: not type.replace(" ", "").lower() in SCAN_TYPES)

        errors = self.validate_field(errors, self.source, "-s/--source", f"File not found {self.source}", lambda source: not os.path.exists(source))
        if self.pipeline_scan and self.sandbox_name:
            errors = self.append_error(errors, self.sandbox_name, "-sn/--sandbox_name", "Pipeline scan does not support a sandbox name")
        
        errors = self.validate_field(errors, self.sandbox_name, "-sn/--sandbox_name", "Sandbox name cannot be longer than 256 characters", lambda sandbox_name: len(sandbox_name) > 256)

        if self.pipeline_scan and self.version:
            errors = self.append_error(errors, self.version, "-v/--version", "Pipeline scan does not support a scan name")
        errors = self.validate_field(errors, self.version, "-v/--version", "Scan name cannot be longer than 256 characters", lambda version: len(version) > 256)

        if errors:
            exit_with_error(errors, len(errors)*-1, self)

        if self.pipeline_scan:
            self.policy_name = get_application_policy_name(self.application_guid, self)


    def parse_custom_field_list(self, custom_field_list):
        return map(custom_field_list, lambda custom_field: CustomField(custom_field))

    def parse_team_list(self, team_list):
        return map(team_list, lambda team_name: Team(team_name, self))

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="This script starts a scan in Veracode."
        )

        #Application Parameters:
        parser.add_argument(
            "-a",
            "--application",
            help="Applications to scan - if it does not exist, it will be created.",
            required=True
        )
        parser.add_argument(
            "-d",
            "--description",
            help="Description of the application - if the application already exists, it WILL be updated.",
            required=False
        )
        parser.add_argument(
            "-d",
            "--description",
            help="Description of the application - if the application already exists, it WILL be updated.",
            required=False
        )
        parser.add_argument(
            "-bc",
            "--business_criticality",
            help="(optional) Business criticality of the application - if the application already exists, it WILL be updated.",
            required=True
        )
        parser.add_argument(
            "-t",
            "--team",
            help="(optional) Teams to assign to the application, takes 0 or more - non-existing teams will be created.",
            action="append",
            required=False
        )
        parser.add_argument(
            "-ac",
            "--application_custom_field",
            help="(optional) Colon(:)-separated key-value pairs for the custom fields to set for the APPLICATION PROFILE, takes 0 or more. I.e.: A Field:Some Value.",
            action="append",
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
            help="Description of the collection - if the collection already exists, it WILL be updated.",
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
            "-b",
            "--business_unit",
            help="Name of the Business unit to assign to the application AND collection - if the BU does not exist, it will be created and if the application/collection exists, it WILL be updated.",
            required=False
        )
        parser.add_argument(
            "-bo",
            "--business_owner",
            help="Name of the business owner - if the application/collection exists, it WILL be updated.",
            required=False
        )
        parser.add_argument(
            "-boe",
            "--business_owner_email",
            help="E-mail of the business owner - if the application/collection exists, it WILL be updated.",
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
            help="Source for the scan. For 'folder', will call the Veracode packager on it, otherwise, will send it directly to the scanner",
            required=True
        )
        parser.add_argument(
            "-ps",
            "--pipeline_scan",
            help="Set to run a pipeline scan. If set, will fetch the policy assigned to the application profile (if one exists) before proceeding - does NOT support a Sandbox name.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-sn",
            "--sandbox_name",
            help="Name of the sandbox to use for the scan, leave empty to run a Policy Scan.",
            required=False
        )
        parser.add_argument(
            "-v",
            "--version",
            help="Name of the scan/version - has to be unique and does NOT support pipeline scans.",
            required=False
        )
        parser.add_argument(
            "-vid",
            "--veracode_api_key_id",
            help="Your Veracode API key ID.",
            required=True
        )
        parser.add_argument(
            "-vkey",
            "--veracode_api_key_secret",
            help="Your Veracode API key secret.",
            required=True
        )
        parser.add_argument(
            "-sc",
            "--scan_timeout",
            help="Scan timeout (in minutes). If empty or 0, will not wait for Sandbox/Policy scans to complete",
            required=False
        )
        parser.add_argument(
            "-f",
            "--fail_build",
            help="Set to run a fail the build if application fails policy evaluation.",
            required=False,
            action=argparse.BooleanOptionalAction
        )
        parser.add_argument(
            "-o",
            "--override_failure",
            help="Set to return a 0 on error. This can be used to avoid breaking a pipeline.",
            required=False,
            action=argparse.BooleanOptionalAction
        )

        args = parser.parse_args()
        self.application = args.application
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
        self.type = args.type
        self.source = args.source
        self.pipeline_scan = args.pipeline_scan
        self.sandbox_name = args.sandbox_name
        self.version = args.version
        self.fail_build = args.fail_build        
        self.override_failure = args.override_failure
        self.vid = args.veracode_api_key_id
        self.vkey = args.veracode_api_key_secret        
        self.scan_timeout = args.scan_timeout

        self.validate_input()
