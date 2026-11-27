from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak, async_discovered_service_info
from homeassistant.const import CONF_ADDRESS
from .const import DOMAIN


class MiniStatFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._disc: BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(self, info: BluetoothServiceInfoBleak):
        await self.async_set_unique_id(info.address)
        self._abort_if_unique_id_configured()
        self._disc = info
        self.context["title_placeholders"] = {"name": info.name}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="MRCOOL Mini Stat", data={CONF_ADDRESS: self._disc.address})
        return self.async_show_form(step_id="confirm", description_placeholders={"name": self._disc.name})

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ADDRESS].upper())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="MRCOOL Mini Stat", data={CONF_ADDRESS: user_input[CONF_ADDRESS].upper()})
        found = {i.address: f"{i.name} ({i.address})" for i in async_discovered_service_info(self.hass)
                 if (i.name or "").startswith("SMARTHVAC")}
        schema = vol.Schema({vol.Required(CONF_ADDRESS): vol.In(found)}) if found else vol.Schema({vol.Required(CONF_ADDRESS): str})
        return self.async_show_form(step_id="user", data_schema=schema)
