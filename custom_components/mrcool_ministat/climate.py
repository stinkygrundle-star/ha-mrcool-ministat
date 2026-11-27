"""Climate entity for the Mini Stat. State comes from the thermostat's status reply."""
from __future__ import annotations
from homeassistant.components.climate import (ClimateEntity, ClimateEntityFeature, HVACMode,
                                              PRESET_NONE, PRESET_SLEEP)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, FANS, KEY_FP, KEY_NORMAL, MODE_AUTO, MODE_COOL, MODE_DRY, MODE_FAN, MODE_HEAT, MODE_FP

TO_HA = {MODE_AUTO: HVACMode.AUTO, MODE_COOL: HVACMode.COOL, MODE_DRY: HVACMode.DRY,
         MODE_FAN: HVACMode.FAN_ONLY, MODE_HEAT: HVACMode.HEAT, MODE_FP: HVACMode.HEAT}
TO_DEV = {HVACMode.AUTO: MODE_AUTO, HVACMode.COOL: MODE_COOL, HVACMode.DRY: MODE_DRY,
          HVACMode.FAN_ONLY: MODE_FAN, HVACMode.HEAT: MODE_HEAT}
FAN_NAMES = {v: k for k, v in FANS.items()}
PRESET_FP = "freeze_protection"


async def async_setup_entry(hass, entry, async_add_entities):
    stat, coord = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MiniStatClimate(stat, coord, entry)])


class MiniStatClimate(CoordinatorEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_min_temp = 62
    _attr_max_temp = 86
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO, HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY, HVACMode.HEAT]
    _attr_fan_modes = list(FANS)
    _attr_preset_modes = [PRESET_NONE, PRESET_SLEEP, PRESET_FP]
    _attr_supported_features = (ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
                                | ClimateEntityFeature.PRESET_MODE
                                | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF)

    def __init__(self, stat, coord, entry):
        super().__init__(coord)
        self._stat = stat
        self._attr_unique_id = f"{entry.unique_id}_climate"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.unique_id)}, "name": "MRCOOL Mini Stat",
                                  "manufacturer": "MRCOOL", "model": "Mini Stat (SmartHVAC BLE)"}
        self._last_on_mode = MODE_HEAT

    @property
    def _u(self):
        return self._stat.unit

    @property
    def assumed_state(self):
        return not self._u.from_device

    @property
    def hvac_mode(self):
        return TO_HA.get(self._u.mode, HVACMode.HEAT) if self._u.power else HVACMode.OFF

    @property
    def native_target_temperature(self):
        return self._u.setpoint

    @property
    def fan_mode(self):
        return FAN_NAMES.get(self._u.fan, "auto")

    @property
    def preset_mode(self):
        if self._u.mode == MODE_FP:
            return PRESET_FP
        return PRESET_SLEEP if self._u.sleep else PRESET_NONE

    @property
    def native_current_temperature(self):
        return self._stat.temperature

    @property
    def current_humidity(self):
        return self._stat.humidity

    @property
    def extra_state_attributes(self):
        return {"swing": self._u.swing, "state_from_device": self._u.from_device}

    async def _after(self):
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self._stat.send_state(power=False)
        else:
            self._last_on_mode = TO_DEV[hvac_mode]
            await self._stat.send_state(power=True, mode=TO_DEV[hvac_mode])
        await self._after()

    async def async_turn_on(self):
        mode = self._u.mode if self._u.mode != MODE_FP else self._last_on_mode
        await self._stat.send_state(power=True, mode=mode)
        await self._after()

    async def async_turn_off(self):
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_temperature(self, **kw):
        if (t := kw.get(ATTR_TEMPERATURE)) is not None:
            await self._stat.send_state(setpoint=round(t))
        await self._after()

    async def async_set_fan_mode(self, fan_mode):
        await self._stat.send_state(fan=FANS[fan_mode])
        await self._after()

    async def async_set_preset_mode(self, preset_mode):
        if preset_mode == PRESET_FP:
            await self._stat.send_state(KEY_FP, power=True, mode=MODE_FP)
        else:
            mode = self._last_on_mode if self._u.mode == MODE_FP else None
            await self._stat.send_state(KEY_NORMAL, mode=mode, sleep=preset_mode == PRESET_SLEEP)
        await self._after()
