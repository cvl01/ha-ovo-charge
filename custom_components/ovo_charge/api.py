"""API Client for OVO Charge (Bonnet)."""

import asyncio
import time
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from aiohttp import ClientError, ClientSession

from .const import (
    API_HEADERS,
    API_KEY,
    BASE_API_URL,
    EMAIL_SIGNIN_URL,
    LOGGER,
    OOB_CODE_URL,
    REFRESH_TOKEN_URL,
    REQUEST_HEADERS,
)

# Default token expiration time in seconds (1 hour)
DEFAULT_TOKEN_EXPIRY_SECONDS = 3600
# Buffer time before expiration to refresh token (5 minutes)
TOKEN_REFRESH_BUFFER_SECONDS = 300


class OVOChargeApiClientError(Exception):
    """Exception to indicate a general API error."""


class OVOChargeAuthError(OVOChargeApiClientError):
    """Exception to indicate an authentication error."""


class OVOChargeApiClient:
    """OVO Charge API Client."""

    def __init__(
        self,
        session: ClientSession,
        refresh_token: Optional[str] = None,
    ):
        """Initialize the API client."""
        self._session = session
        self._refresh_token = refresh_token
        self._id_token: Optional[str] = None
        self._user_id: Optional[str] = None
        self._token_expires_at: Optional[float] = None

    def _is_token_valid(self) -> bool:
        """Check if the current ID token is valid and not expired."""
        if not self._id_token:
            return False

        if not self._token_expires_at:
            return False

        # Check if token expires within the buffer time
        current_time = time.time()
        return current_time < (self._token_expires_at - TOKEN_REFRESH_BUFFER_SECONDS)

    async def _ensure_valid_token(self) -> None:
        """Ensure we have a valid, non-expired ID token."""
        if not self._is_token_valid():
            await self.refresh_id_token()

    async def _request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a request to the API."""
        try:
            async with self._session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                response.raise_for_status()
                return await response.json()
        except ClientError as e:
            LOGGER.error("API request error: %s", e)
            raise OVOChargeApiClientError from e

    async def refresh_id_token(self) -> Dict[str, Any]:
        """Refresh the idToken using the refreshToken."""
        if not self._refresh_token:
            raise OVOChargeAuthError("No refresh token available.")

        body = {
            "grantType": "refresh_token",
            "refreshToken": self._refresh_token,
        }
        url = f"{REFRESH_TOKEN_URL}?key={API_KEY}"
        try:
            data = await self._request("POST", url, headers=REQUEST_HEADERS, json=body)
            self._id_token = data["id_token"]
            self._user_id = data["user_id"]
            self._refresh_token = data["refresh_token"]

            # Calculate token expiration time
            expires_in = int(data.get("expires_in", DEFAULT_TOKEN_EXPIRY_SECONDS))
            self._token_expires_at = time.time() + expires_in

            LOGGER.debug(
                "Token refreshed successfully, expires in %d seconds", expires_in
            )

            return {
                "id_token": self._id_token,
                "user_id": self._user_id,
                "refresh_token": self._refresh_token,
            }
        except OVOChargeApiClientError as e:
            raise OVOChargeAuthError("Failed to refresh token") from e

    async def get_active_charge_session(self) -> Optional[Dict[str, Any]]:
        """Get user charge logs and return the active session if one exists."""
        # Ensure we have a valid token before making the request
        await self._ensure_valid_token()

        if not self._id_token:
            raise OVOChargeAuthError("Unable to obtain valid id_token.")

        headers = API_HEADERS.copy()
        headers["Authorization"] = self._id_token
        url = f"{BASE_API_URL}/me/logs?limit=1&offset=0&include_unfinished=true"

        try:
            data = await self._request("GET", url, headers=headers)
            # The first item is the most recent. Check if it's active.
            if data.get("items") and data["items"][0].get("status") == "ACTIVE":
                LOGGER.debug("Active charge session found: %s", data["items"][0])
                return data["items"][0]
            
            
        except OVOChargeApiClientError:
            # If the request fails, it might be due to token issues
            # Force a token refresh and try once more
            LOGGER.warning("API request failed, attempting token refresh")
            await self.refresh_id_token()
            if not self._id_token:
                raise OVOChargeAuthError("Unable to refresh id_token.")
            headers["Authorization"] = self._id_token
            data = await self._request("GET", url, headers=headers)
            if data.get("items") and data["items"][0].get("status") == "ACTIVE":
                return data["items"][0]

        return None

    @staticmethod
    async def request_magic_link(session: ClientSession, email: str) -> None:
        """Request a magic link to be sent to the user's email."""
        body = {
            "requestType": "EMAIL_SIGNIN",
            "email": email,
            "continueUrl": "https://joinbonnet.com?flow=logIn",
            "iOSBundleId": "com.bonnet.driver",
            "androidPackageName": "com.bonnet",
            "canHandleCodeInApp": True,
        }
        url = f"{OOB_CODE_URL}?key={API_KEY}"
        try:
            async with session.post(url, headers=REQUEST_HEADERS, json=body) as resp:
                resp.raise_for_status()
        except ClientError as e:
            raise OVOChargeApiClientError("Failed to request magic link") from e

    @staticmethod
    async def verify_magic_link(
        session: ClientSession, email: str, link: str
    ) -> Dict[str, str]:
        """Verify the magic link and return tokens."""
        try:
            # First, parse the URL the user provided.
            parsed_user_link = urlparse(link)
            query_params = parse_qs(parsed_user_link.query)

            # Check if it's a dynamic link with a nested 'link' parameter.
            if "link" in query_params:
                # It is. Extract the inner URL and parse it.
                inner_link = query_params["link"][0]
                inner_parsed = urlparse(inner_link)
                inner_params = parse_qs(inner_parsed.query)
                oob_code = inner_params.get("oobCode", [None])[0]
            else:
                # It's not nested. Assume oobCode is in the top-level query.
                oob_code = query_params.get("oobCode", [None])[0]

            if not oob_code:
                raise OVOChargeAuthError("oobCode not found in the provided link.")
        except Exception as e:
            # Catch any parsing errors (e.g., malformed URL)
            raise OVOChargeAuthError(f"Invalid magic link format: {e}") from e

        body = {"email": email, "oobCode": oob_code}
        url = f"{EMAIL_SIGNIN_URL}?key={API_KEY}"
        try:
            async with session.post(url, headers=REQUEST_HEADERS, json=body) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return {
                    "refresh_token": data["refreshToken"],
                    "id_token": data["idToken"],
                    "user_id": data["localId"],
                }
        except ClientError as e:
            raise OVOChargeAuthError("Failed to verify magic link") from e
