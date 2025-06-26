"""Sensor platform for OVO Charge (Bonnet)."""

from typing import Any, Dict

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_USER_ID, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    user_id = entry.data[CONF_USER_ID]

    sensors = [
        OVOChargeStatusSensor(coordinator, user_id),
        OVOChargeEnergySensor(coordinator, user_id),
        OVOChargePowerSensor(coordinator, user_id),
        OVOChargeCostSensor(coordinator, user_id),
    ]
    async_add_entities(sensors)


class OVOChargeBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for OVO Charge sensors."""

    def __init__(self, coordinator, user_id: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._user_id = user_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._user_id)},
            "name": "OVO Charge",
            "manufacturer": "OVO",
            "model": "Account",
            "entry_type": "service",
        }

    @property
    def active_session(self) -> Dict[str, Any] | None:
        """Return the active session data from the coordinator."""
        return self.coordinator.data


class OVOChargeStatusSensor(OVOChargeBaseSensor):
    """Sensor for the current charging status."""

    _attr_icon = "mdi:ev-station"
    _attr_name = "OVO Charge Status"

    def __init__(self, coordinator, user_id: str):
        """Initialize the sensor."""
        super().__init__(coordinator, user_id)
        self._attr_unique_id = f"{user_id}_status"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if self.active_session:
            status = self.active_session.get("status")
            if status == "ACTIVE":
                power = self.active_session.get("power", 0)
                if power > 0:
                    return "Charging"
                else:
                    return "Full"
            elif status == "INVALID":
                return "Invalid"
        return "Disconnected"

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        """Return the state attributes."""
        if self.active_session:
            return {
                "address": self.active_session.get("address"),
                "operator": self.active_session.get("operator"),
                "start_time": self.active_session.get("date_time"),
                "currency": self.active_session.get("currency"),
                "total_cost": self.active_session.get("total_cost"),
                "command_id": self.active_session.get("command_id"),
            }
        return None


class OVOChargeEnergySensor(OVOChargeBaseSensor):
    """Sensor for the energy delivered during a charge."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_name = "OVO Charge Energy"

    def __init__(self, coordinator, user_id: str):
        """Initialize the sensor."""
        super().__init__(coordinator, user_id)
        self._attr_unique_id = f"{user_id}_energy"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.active_session:
            return self.active_session.get("kwh")
        return 0.0


class OVOChargePowerSensor(OVOChargeBaseSensor):
    """Sensor for the current charging power."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_name = "OVO Charge Power"

    def __init__(self, coordinator, user_id: str):
        """Initialize the sensor."""
        super().__init__(coordinator, user_id)
        self._attr_unique_id = f"{user_id}_power"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.active_session:
            return self.active_session.get("power")
        return 0.0


class OVOChargeCostSensor(OVOChargeBaseSensor):
    """Sensor for the total cost of charging."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_name = "OVO Charge Cost"

    def __init__(self, coordinator, user_id: str):
        """Initialize the sensor."""
        super().__init__(coordinator, user_id)
        self._attr_unique_id = f"{user_id}_cost"
        # Set default currency, will be updated when we get API data
        self._currency_unit = "EUR"

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the currency of the charge."""
        # Update currency if we have session data with a currency
        if self.active_session and self.active_session.get("currency"):
            api_currency = self.active_session.get("currency")
            if (
                api_currency
                and isinstance(api_currency, str)
                and api_currency != self._currency_unit
            ):
                self._currency_unit = api_currency

        # Always return the stored currency unit, never None or empty string
        return self._currency_unit

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.active_session:
            # The API provides cost in the currency's smallest unit (e.g., cents)
            total_cost = self.active_session.get("total_cost")
            if total_cost is not None:
                return total_cost / 100
        return 0.0

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        """Return additional state attributes including the actual API currency."""
        if self.active_session:
            return {
                "api_currency": self.active_session.get("currency"),
                "total_cost_raw": self.active_session.get("total_cost"),
            }
        return None
