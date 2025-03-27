from VeracodeApi import link_sca_project, get_agent_sbom, get_scan_project_guid
from CliCaller import call_subprocess, save_sbom_file

def run_agent_sca(returned_values, results_file, scan_configuration):
    sca_results = run_agent_sca_inner(results_file, scan_configuration)
    if scan_configuration.link_project and sca_results[2]:
        scan_configuration.project_guid = link_sca_project(sca_results[2], scan_configuration)
    elif sca_results[2]:
        scan_configuration.project_guid = get_scan_project_guid(sca_results[2], scan_configuration)
    returned_values["SCA Scan"] = sca_results

    if scan_configuration.sbom_type:
        save_sbom_file(get_agent_sbom(scan_configuration), scan_configuration)

def run_agent_sca_inner(results_file, scan_configuration):
    commands=["srcclr", "scan", scan_configuration.srcclr_to_scan, "--recursive", "--allow-dirty"]
    if scan_configuration.verbose:
        commands.append("--debug")
    return call_subprocess(process_id="Running SCA Scan", scan_configuration=scan_configuration, fail_on_error=False, 
                            commands=commands,
                            additional_env=[{"name": "SRCCLR_API_URL", "value": scan_configuration.srcclr_api_url},
                                            {"name": "SRCCLR_API_TOKEN", "value": scan_configuration.srcclr_token}],
                            results_file=results_file,
                            shell=True,
                            return_line_filter=["Full Report Details", "https://"])
