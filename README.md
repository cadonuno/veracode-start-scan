# Veracode scan workflow plugin
Allows for simple implementation of a Veracode scanning workflow.

## Requirements:
- Python 3.12+
- The Veracode CLI is installed
- If using the Veracode Packager (--scan_type "artifact"): the local machine is able to compile the application and the packaging command can run successfully
- Java is installed (and added to the system path)
- The Veracode API wrapper is available in the local system
- To use Agent-based SCA, it needs to be installed in the local system and available through the `srcclr` command

## Installation
Clone this repository:
    git clone https://github.com/cadonuno/veracode-start-scan.git

Install dependencies:

    cd /veracode-start-scan
    pip install -r requirements.txt

## Run
    python ./src/veracode-start-scan.py (arguments)

## Arguments supported are:

API Credentials:
- `-vid`, `--veracode_api_key_id` - Veracode API key ID to use - a non-human/API account is recommended.
- `-vkey`, `--veracode_api_key_secret` - Veracode API key secret to use - a non-human/API account is recommended.

Proxy:
- `-purl`, `--proxy_url` - (Optional) URL of proxy server to use.
- `-pport`, `--proxy_port` - (Optional) Port of proxy server to use.
- `-puser`, `--proxy_username` - (Optional) Username to use to authenticate to proxy.
- `-ppass`, `--proxy_password` - (Optional) Password to use to authenticate to proxy.

Application Parameters:
- `-ai`, `--application_guid` - GUID of the application to scan.
- `-a`, `--application` - Name of the application to scan, replaces --application_guid and will create an application if it doesn't exist.
- `-ra`, `--require_application` - (optional) Pass this flag to fail the build if the application does not exist - used to avoid creating new applications
- `-sau`, `--skip_application_update` - (optional) Pass this flag to skip the application update - does nothing if the application does NOT exist.
- `-desc`, `--description` - (optional) Description of the application - if the application already exists, it WILL be updated.
- `-at`, `--application_tags` - (optional) Tags to be added to the application - if the application already exists, it WILL be updated.
- `-bc`, `--business_criticality` - Business criticality of the application - if the application already exists, it WILL be updated.
- `-ac`, `--application_custom_field` - (optional) Colon(:)-separated key-value pairs for the custom fields to set for the APPLICATION PROFILE, takes 0 or more. I.e.: A Field:Some Value.
- `-url`, `--git_repo_url` - (optional) URL of the git repository scanned.
- `-ka`, `--key_alias` - (optional) If using CMKs, sets the key alias to use for this application - if the application already exists, will NOT be updated

Collection Parameters:
- `-c`, `--collection` - (optional) Name of the collection to assign to the application - will be created if none are found.
- `-rc`, `--require_collection` - (optional) Pass this flag to fail the build if the collection does not exist - used to avoid creating new collections.
- `-scu`, `--skip_collection_update` - (optional) Pass this flag to skip the collection update - does nothing if the collection does NOT exist.
- `-cd`, `--collection_description` -(optional) Description of the collection - if the collection already exists, it WILL be updated.
- `-ct`, `--collection_tags` - (optional) Tags to be added to the collection - if the collection already exists, it WILL be updated.
- `-cc`, `--collection_custom_field` - (optional) Colon(:)-separated key-value pairs for the custom fields to set for the COLLECTION, takes 0 or more. I.e.: A Field:Some Value.

Both Application and Collection:
- `-t`, `--team` - Teams to assign to the application, takes 1 or more - if a team does not exist, it will be created and if the application/collection exists, it WILL be updated (overriding any existing teams).
- `-rt`, `--require_teams` - (optional) Pass this flag to fail the build if any teams do not exist - used to avoid creating new teams.
- `-b`, `--business_unit` - (optional) Name of the Business unit to assign to the application AND collection - if the BU does not exist, it will be created and if the application/collection exists, it WILL be updated.
- `-rbu`, `--require_business_unit` - (optional) Pass this flag to fail the build if the business unit does not exist - used to avoid creating new business units.
- `-bo`, `--business_owner` - (optional) Name of the business owner - if the application/collection exists, it WILL be updated.
- `-boe`, `--business_owner_email` - (optional) E-mail of the business owner - if the application/collection exists, it WILL be updated.

Scan Parameters:
- `-st`, `--scan_type` - Type of scan, either 'folder' or 'artifact'.
- `-s`, `--source` - Source for the scan. For 'folder', will call the Veracode packager on it, otherwise, will send it directly to the scanner.
- `-cbs`, `--cleanup_before_start` - (optional) Pass this flag to clear the build output directory before calling a build. Only available for --scan_type 'folder'.
- `-cbe`, `--cleanup_before_exit` - (optional) Pass this flag to delete the scanned files on exit - does nothing for --scan_type 'artifact'.
- `-ps`, `--pipeline_scan` - (optional) Pass this flag to run a pipeline scan. If set, will fetch the policy assigned to the application profile (if one exists) before proceeding - does NOT support a Sandbox name.
- `-wn`, `--workspace_name` - (optional) Name of the workspace to use for Agent-based SCA scans - If empty and using the Pipeline Scanner, SCA results will not be generated.
- `-sbom`, `--sbom_type` - (optional) Set the type of SBOM to fetch for the project after the scan - if using Policy/Sandbox scan, requires a scan_timeout.
- `-lp`, `--link_project` - (optional) Pass this flag to link the agent SCA project to the Application profile (requires a workspace name).
- `-sn`, `--sandbox_name` - (optional) Name of the sandbox to use for the scan, leave empty to run a Policy Scan.
- `-v`, `--version` - Name of the scan/version - has to be unique for each application/sandbox combo and does NOT support pipeline scans - mandatory if not using -ps/--pipeline_scan.
- `-del`, `--delete_incomplete_scan` - (optional) Sets a value for the -deleteincompletescan parameter for the upload and scan action (not supported, or needed, for the pipeline scan).
- `-wt`, `--wait_for_timeout` - (optional) Sets a timeout (in minutes) to wait for the previous scan to complete before trying to start a new scan (not supported or needed for the pipeline scan, or if using --delete_incomplete_scan).
- `-sct`, `--scan_timeout` - (optional) Scan timeout (in minutes). If empty or 0, will not wait for Sandbox/Policy scans to complete.
- `-f`, `--fail_build` - (optional) Pass this flag to fail the build if application fails policy evaluation.
- `-o`, `--override_failure` - (optional) Pass this flag to return a 0 on error. This can be used to avoid breaking a pipeline.
- `-cli`, `--veracode_cli_location` - Location of the Veracode CLI installation.
- `-wra`, `--veracode_wrapper_location` - Location of the Veracode API Wrapper jar.
- `-i`, `--include` - (optional) Case-sensitive, comma-separated list of module name patterns that represent the names of modules to scan as top-level modules. The * wildcard matches 0 or more characters. The ? wildcard matches exactly one character.
- `-e`, `--exclude` - (optional) Case-sensitive, comma-separated list of module name patterns that represent the names of modules NOT to scan as top-level modules. The * wildcard matches 0 or more characters. The ? wildcard matches exactly one character.
- `-sanftlm`, `--scan_all_non_fatal_top_level_modules` - (optional) Case-sensitive, comma-separated list of module name patterns that represent the names of modules to scan as top-level modules. The * wildcard matches 0 or more characters. The ? wildcard matches exactly one character.
- `-ia`, `--ignore_artifact` - (optional) Artifacts not to scan, takes 0 or more - use to not try scanning specific artifacts generated by the Veracode Packager, only works with --scan_type 'folder'
- `-d`, `--debug` - (optional) Pass this flag to output verbose logging.
- `-fs`, `--fallback_sandbox` - (optional) Sandbox name to fallback to if packaged application is bigger than 200MB (pipeline scan limit).

## Example Usage:

### Package an application, creating or updating the application profile, business unit, teams, and collection, if necessary, and run a Policy/Sandbox and an Agent-based SCA scan, waiting for results and breaking build if it fails policy:
    python ./src/veracode-start-scan.py -vid <veracode_api_id> -vkey <veracode_api_key> -a <application_name> -bc <business_criticality> (-desc <application_description>) (-at <application_tags>) (-t <team1> -t <team2>...) (-bu <business_unit>) (-ac <custom_field_name>:<application_custom_field_value> -ac <custom_field_name>:<application_custom_field_value>...) -c <collection_name> (-cd <collection_description>) (-ct <collection_tags>) (-cc <custom_field_name>:<collection_custom_field_value> -cc <custom_field_name>:<collection_custom_field_value>...) (-bo <business_owner> -boe <business_owner_email>) (-sn <sandbox_name>) -st "folder" -s <path_to_project> -v <scan_name(unique)> -wn <agent_workspace_name> (-sct <scan_timeout>) (-del 1) (-lp) (--sbom <sbom_type>) (-i <modules_to_select>) (-e <modules_not_to_select>) (-sanftlm) (-d) -f

### Package an application, run a Pipeline and an Agent-based SCA scan, waiting for results and breaking build if it fails policy or if application profile, business unit, teams, or collection doesn't exist but UPDATING them if they do exist:
    python ./src/veracode-start-scan.py -vid <veracode_api_id> -vkey <veracode_api_key> -a <application_name> -bc <business_criticality> (-desc <application_description>) (-at <application_tags>) (-t <team1> -t <team2>...) (-bu <business_unit>) (-ac <custom_field_name>:<application_custom_field_value> -ac <custom_field_name>:<application_custom_field_value>...) -ra -rc -rt -rbu -c <collection_name> (-cd <collection_description>) (-ct <collection_tags>) (-cc <custom_field_name>:<collection_custom_field_value> -cc <custom_field_name>:<collection_custom_field_value>...) (-bo <business_owner> -boe <business_owner_email>) -st "folder" -s <path_to_project> -ps -wn <agent_workspace_name>  (-lp) (--sbom <sbom_type>) (-i <modules_to_select>) (-d) -f
    
### Package an application, run a Pipeline and an Agent-based SCA scan, waiting for results and breaking build if it fails policy or if application profile doesn't exist WITHOUT updating it if it exists:
    python ./src/veracode-start-scan.py -vid <veracode_api_id> -vkey <veracode_api_key> -a <application_name> -bc <business_criticality> -ra -sau -rc -scu -rt -rbu -st "folder" -s <path_to_project> -ps -wn <agent_workspace_name>  (-lp) (--sbom <sbom_type>) (-i <modules_to_select>) (-d) -f

### Package an application, run a Policy/Sandbox and an Agent-based SCA scan, waiting for results and breaking build if it fails policy or if application profile doesn't exist WITHOUT updating it if it exists:
    python ./src/veracode-start-scan.py -vid <veracode_api_id> -vkey <veracode_api_key> -a <application_name> -bc <business_criticality> -ra -sau -rc -scu -rt -rbu (-sn <sandbox_name>) -st "folder" -s <path_to_project> -ps -wn <agent_workspace_name>  (-lp) (--sbom <sbom_type>) (-i <modules_to_select>) (-d) -f