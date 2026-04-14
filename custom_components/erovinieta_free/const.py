"""Constante pentru integrarea CNAIR eRovinieta Free."""

DOMAIN = "erovinieta_free"
VERSION = "1.0.0"
ATTRIBUTION = "Date furnizate de www.erovinieta.ro"

BASE_URL = "https://www.erovinieta.ro/vignettes-portal-web"
URL_LOGIN = f"{BASE_URL}/login"
URL_GET_USER_DATA = f"{BASE_URL}/rest/setariUtilizatorPortal"
URL_GET_PAGINATED = f"{BASE_URL}/rest/desktop/home/getDataPaginated"
URL_GET_COUNTRIES = f"{BASE_URL}/rest/anonymous/getCountries"
URL_TRECERI_POD = (
    f"{BASE_URL}/rest/anonymous/bridge/detectionsAndPayments/"
    "getDetectionsAndPayments"
)

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 3600
MIN_UPDATE_INTERVAL = 300
MAX_UPDATE_INTERVAL = 86400

PLATFORMS = ["sensor"]

TOKEN_VALIDITY_SECONDS = 3500