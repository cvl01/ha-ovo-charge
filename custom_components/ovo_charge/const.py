"""Constants for the OVO Charge (Bonnet) integration."""
from logging import getLogger

DOMAIN = "ovo_charge"
LOGGER = getLogger(__package__)

# API Constants from documentation
API_KEY = "AIzaSyBc8a2MgrJ3krmxixlWflgVGg5ZQ_pHF78"
BASE_API_URL = "https://bonnetapps.com/driver/api/1.1"
OOB_CODE_URL = (
  "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode"
)
EMAIL_SIGNIN_URL = (
  "https://www.googleapis.com/identitytoolkit/v3/relyingparty/emailLinkSignin"
)
REFRESH_TOKEN_URL = "https://securetoken.googleapis.com/v1/token"

# Headers
REQUEST_HEADERS = {
  "Content-Type": "application/json",
  "x-client-version": "iOS/FirebaseSDK/11.13.0/FirebaseCore-iOS",
  "x-ios-bundle-identifier": "com.bonnet.driver",
}

API_HEADERS = {
  "Content-Type": "application/json",
  "User-Agent": "OVOCharge/1 CFNetwork/3826.500.131 Darwin/24.5.0",
  "app-version": "3.14.3",
  "app-platform": "ios",
}

# Configuration
CONF_EMAIL = "email"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_ID_TOKEN = "id_token"
CONF_USER_ID = "user_id"

# Update interval
SCAN_INTERVAL_ACTIVE_CHARGE = 60  # seconds
SCAN_INTERVAL_IDLE = 300  # seconds