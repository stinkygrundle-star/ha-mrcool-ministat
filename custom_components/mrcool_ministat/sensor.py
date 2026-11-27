from __future__ import annotations
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfElectricPotential, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    stat, coord = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        MiniStatSensor(coord, entry, "temperature", "Temperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.FAHRENHEIT),
        MiniStatSensor(coord, entry, "humidity", "Humidity", SensorDeviceClass.HUMIDITY, PERCENTAGE),
        MiniStatSensor(coord, entry, "battery_voltage", "Battery voltage", SensorDeviceClass.VOLTAGE,
                       UnitOfElectricPotential.VOLT, EntityCategory.DIAGNOSTIC),
    ])


class MiniStatSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coord, entry, key, name, dc, unit, category=None):
        super().__init__(coord)
        self._key = key
        self._attr_name = name
        self._attr_device_class = dc
        self._attr_native_unit_of_measurement = unit
        self._attr_entity_category = category
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.unique_id)}}

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self._key)
