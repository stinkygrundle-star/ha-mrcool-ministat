"""Toggle buttons. The Mini Stat treats these as key presses, like the app does."""
from __future__ import annotations
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN, KEY_TURBO, KEY_SWING, KEY_LED, KEY_FOLLOW

BUTTONS = [
    ("turbo", "Turbo toggle", "mdi:fan-plus", KEY_TURBO, None),
    ("swing", "Swing toggle", "mdi:arrow-oscillating", KEY_SWING, "1"),
    ("louver_step", "Louver step", "mdi:arrow-up-down", KEY_SWING, "0"),
    ("led", "Display LED toggle", "mdi:led-on", KEY_LED, None),
    ("follow_me", "Follow me toggle", "mdi:thermometer-check", KEY_FOLLOW, None),
]


async def async_setup_entry(hass, entry, async_add_entities):
    stat, coord = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MiniStatButton(stat, coord, entry, *b) for b in BUTTONS)


class MiniStatButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, stat, coord, entry, key, name, icon, code, pdigit):
        self._stat, self._coord, self._code, self._pdigit = stat, coord, code, pdigit
        self._attr_name, self._attr_icon = name, icon
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.unique_id)}}

    async def async_press(self):
        await self._stat.send_state(self._code, power_digit=self._pdigit)
        await self._coord.async_request_refresh()
