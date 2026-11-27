from __future__ import annotations
from datetime import timedelta
import logging
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, POLL_SECONDS
from .device import MiniStat

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    address = entry.data[CONF_ADDRESS]
    dev = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if not dev:
        raise ConfigEntryNotReady(f"Mini Stat {address} not seen. Wake its Bluetooth (Temp Up + Power 5 s).")
    stat = MiniStat(dev)

    async def _update():
        d = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
        if d:
            stat.set_ble_device(d)
        try:
            await stat.poll()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(str(err)) from err
        return {"temperature": stat.temperature, "humidity": stat.humidity,
                "battery_voltage": _battery(stat.raw_state), "raw": stat.raw_state}

    coord = DataUpdateCoordinator(hass, _LOGGER, name=DOMAIN, update_method=_update,
                                  update_interval=timedelta(seconds=POLL_SECONDS))
    await coord.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = (stat, coord)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        stat, _ = hass.data[DOMAIN].pop(entry.entry_id)
        await stat.disconnect()
    return ok


def _battery(raw):
    """Battery voltage from TTM(SC1) field 7 (two AA cells, e.g. 2.6)."""
    try:
        v = float(raw[7])
    except (TypeError, IndexError, ValueError):
        return None
    return v if 0.5 < v < 4.0 else None
