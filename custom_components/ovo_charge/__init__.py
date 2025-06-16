"""The OVO Charge (Bonnet) integration."""
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import OVOChargeApiClient
from .const import (
  CONF_REFRESH_TOKEN,
  DOMAIN,
  LOGGER,
  SCAN_INTERVAL_ACTIVE_CHARGE,
  SCAN_INTERVAL_IDLE,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
  """Set up OVO Charge from a config entry."""
  session = async_get_clientsession(hass)
  api_client = OVOChargeApiClient(
    session, entry.data[CONF_REFRESH_TOKEN]
  )

  async def async_update_data():
    """Fetch data from API endpoint."""
    data = await api_client.get_active_charge_session()
    # If a session is active, poll faster
    if data:
      coordinator.update_interval = timedelta(
        seconds=SCAN_INTERVAL_ACTIVE_CHARGE
      )
    else:
      coordinator.update_interval = timedelta(seconds=SCAN_INTERVAL_IDLE)
    return data

  coordinator = DataUpdateCoordinator(
    hass,
    LOGGER,
    name="ovo_charge_sensor",
    update_method=async_update_data,
    update_interval=timedelta(seconds=SCAN_INTERVAL_IDLE),
  )

  await coordinator.async_config_entry_first_refresh()

  hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

  await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

  return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
  """Unload a config entry."""
  if unload_ok := await hass.config_entries.async_unload_platforms(
    entry, PLATFORMS
  ):
    hass.data[DOMAIN].pop(entry.entry_id)

  return unload_ok