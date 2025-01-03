ALLOWED_CRITICALITIES = ["veryhigh", "high", "medium", "low", "verylow"]
SCAN_TYPES = ["folder", "artifact"]
PACKAGER_OUTPUT = "./.verascan"
SCA_URL_MAP = {
    'eu': "https://sca-api.veracode.eu",
    'fedramp': "https://sca-api.veracode.us",
    'global': "https://sca-api.veracode.com",
}