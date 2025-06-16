"""Config flow for OVO Charge (Bonnet) integration."""
import voluptuous as vol
from aiohttp import ClientSession

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OVOChargeApiClient, OVOChargeAuthError
from .const import DOMAIN, LOGGER

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str})
STEP_LINK_DATA_SCHEMA = vol.Schema({vol.Required("magic_link"): str})


class OVOChargeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  """Handle a config flow for OVO Charge."""

  VERSION = 1
  user_input: dict = {}

  async def async_step_user(self, user_input=None):
    """Handle the initial step."""
    errors = {}
    if user_input is not None:
      self.user_input[CONF_EMAIL] = user_input[CONF_EMAIL]
      session = async_get_clientsession(self.hass)
      try:
        await OVOChargeApiClient.request_magic_link(
          session, user_input[CONF_EMAIL]
        )
        return await self.async_step_link()
      except Exception:
        LOGGER.exception("Failed to request magic link")
        errors["base"] = "cannot_connect"

    return self.async_show_form(
      step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
    )

  async def async_step_link(self, user_input=None):
    """Handle the magic link verification step."""
    errors = {}
    if user_input is not None:
      email = self.user_input[CONF_EMAIL]
      link = user_input["magic_link"]
      session = async_get_clientsession(self.hass)

      try:
        tokens = await OVOChargeApiClient.verify_magic_link(
          session, email, link
        )
        await self.async_set_unique_id(tokens["user_id"])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
          title=email,
          data={
            "refresh_token": tokens["refresh_token"],
            "user_id": tokens["user_id"],
          },
        )
      except OVOChargeAuthError:
        errors["base"] = "invalid_auth"
      except Exception:
        LOGGER.exception("Unexpected error during link verification")
        errors["base"] = "unknown"

    return self.async_show_form(
      step_id="link",
      data_schema=STEP_LINK_DATA_SCHEMA,
      errors=errors,
      description_placeholders={"email": self.user_input[CONF_EMAIL]},
    )