ALLOWED_CRITICALITIES = ["VERY HIGH", "HIGH", "MEDIUM", "LOW", "VERY LOW"]
ALLOWED_DELETE_INCOMPLETE_SCAN = ["0", "1", "2"]
SCAN_TYPES = ["folder", "artifact"]
SBOM_TYPES = ["cyclonedx", "spdx"]
PACKAGER_OUTPUT = "./.verascan"
SCA_URL_MAP = {
    'eu': "https://sca-api.veracode.eu",
    'fedramp': "https://sca-api.veracode.us",
    'global': "https://sca-api.veracode.com",
}