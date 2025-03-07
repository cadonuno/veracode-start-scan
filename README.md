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

Arguments supported include:

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
- `-desc`, `--description` - (optional) Description of the application - if the application already exists, it WILL be updated.
- `-at`, `--application_tags` - (optional) Tags to be added to the application - if the application already exists, it WILL be updated.
- `-bc`, `--business_criticality` - Business criticality of the application - if the application already exists, it WILL be updated.
- `-ac`, `--application_custom_field` - (optional) Colon(:)-separated key-value pairs for the custom fields to set for the APPLICATION PROFILE, takes 0 or more. I.e.: A Field:Some Value.
- `-url`, `--git_repo_url` - (optional) URL of the git repository scanned.
- `-ka`, `--key_alias` - (optional) If using CMKs, sets the key alias to use for this application - if the application already exists, will NOT be updated

Collection Parameters:
- `-c`, `--collection` - (optional) Name of the collection to assign to the application - will be created if none are found.
- `-cd`, `--collection_description` -(optional) Description of the collection - if the collection already exists, it WILL be updated.
- `-ct`, `--collection_tags` - (optional) Tags to be added to the collection - if the collection already exists, it WILL be updated.
- `-cc`, `--collection_custom_field` - (optional) Colon(:)-separated key-value pairs for the custom fields to set for the COLLECTION, takes 0 or more. I.e.: A Field:Some Value.

Both Application and Collection:
- `-t`, `--team` - Teams to assign to the application, takes 1 or more - if a team does not exist, it will be created and if the application/collection exists, it WILL be updated (overriding any existing teams).
- `-b`, `--business_unit` - (optional) Name of the Business unit to assign to the application AND collection - if the BU does not exist, it will be created and if the application/collection exists, it WILL be updated.
- `-bo`, `--business_owner` - (optional) Name of the business owner - if the application/collection exists, it WILL be updated.
- `-boe`, `--business_owner_email` - (optional) E-mail of the business owner - if the application/collection exists, it WILL be updated.

Scan Parameters:
- `-st`, `--scan_type` - Type of scan, either 'folder' or 'artifact'.
- `-s`, `--source` - Source for the scan. For 'folder', will call the Veracode packager on it, otherwise, will send it directly to the scanner.
- `-ps`, `--pipeline_scan` - (optional) Set to run a pipeline scan. If set, will fetch the policy assigned to the application profile (if one exists) before proceeding - does NOT support a Sandbox name.
- `-wn`, `--workspace_name` - (optional) Name of the workspace to use for Agent-based SCA scans. Only used if -ps is true - If empty, SCA will not be run alongside the Pipeline Scan.
- `-sbom`, `--sbom_type` - (optional) Set the type of SBOM to fetch for the project after the scan - if using Policy/Sandbox scan, requires a scan_timeout.
- `-lp`, `--link_project` - (optional) Set to link the agent SCA project to the Application profile (requires a workspace name).
- `-sn`, `--sandbox_name` - (optional) Name of the sandbox to use for the scan, leave empty to run a Policy Scan.
- `-v`, `--version` - Name of the scan/version - has to be unique for each application/sandbox combo and does NOT support pipeline scans - mandatory if not using -ps/--pipeline_scan.
- `-del`, `--delete_incomplete_scan` - (optional) Sets a value for the -deleteincompletescan parameter for the upload and scan action (not supported, or needed, for the pipeline scan).
- `-wt`, `--wait_for_timeout` - (optional) Sets a timeout (in minutes) to wait for the previous scan to complete before trying to start a new scan (not supported or needed for the pipeline scan, or if using --delete_incomplete_scan).
- `-sct`, `--scan_timeout` - (optional) Scan timeout (in minutes). If empty or 0, will not wait for Sandbox/Policy scans to complete.
- `-f`, `--fail_build` - (optional) Set to fail the build if application fails policy evaluation.
- `-o`, `--override_failure` - (optional) Set to return a 0 on error. This can be used to avoid breaking a pipeline.
- `-cli`, `--veracode_cli_location` - Location of the Veracode CLI installation.
- `-wra`, `--veracode_wrapper_location` - Location of the Veracode API Wrapper jar.
- `-i`, `--include` - (optional) Case-sensitive, comma-separated list of module name patterns that represent the names of modules to scan as top-level modules. The * wildcard matches 0 or more characters. The ? wildcard matches exactly one character.
- `-ia`, `--ignore_artifact` - (optional) Artifacts not to scan, takes 0 or more - use to not try scanning specific artifacts generated by the Veracode Packager, only works with --scan_type 'folder'
- `-d`, `--debug` - (optional) Set to output verbose logging.