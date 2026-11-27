"""Talks to the Mini Stat over Bluetooth. Plain ASCII, no auth."""
from __future__ import annotations
import asyncio, logging, re
from dataclasses import dataclass
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache
from .const import CMD_CHAR, NOTIFY_CHAR, FD02_CHAR, KEY_NORMAL

_LOGGER = logging.getLogger(__name__)
ACK_RE = re.compile(r"\{ACK:([\d.\-]+),([\d.\-]+)\}")
STATE_RE = re.compile(r"\(State:([^)]*)\)")


@dataclass
class UnitState:
    power: bool = True
    mode: str = "4"
    setpoint: int = 69
    fan: str = "0"
    sleep: bool = False
    follow_me: bool = False
    from_device: bool = False


def parse_unit(code: str) -> UnitState | None:
    """Field 13 of the State reply, e.g. 1469000 = on, heat, 69F, fan auto, sleep 0, follow me 0."""
    if len(code) < 7 or not code.isdigit():
        return None
    mode, tt, fan = code[1], int(code[2:4]), code[4]
    if mode not in "012345" or not 55 <= tt <= 90 or fan not in "0123":
        return None
    return UnitState(power=code[0] != "0", mode=mode, setpoint=tt, fan=fan,
                     sleep=code[5] == "1", follow_me=code[6] == "1", from_device=True)


class MiniStat:
    def __init__(self, ble_device: BLEDevice) -> None:
        self._dev = ble_device
        self._client: BleakClientWithServiceCache | None = None
        self._lock = asyncio.Lock()
        self._buf = ""
        self._reply: asyncio.Future | None = None
        self.temperature: float | None = None
        self.humidity: float | None = None
        self.raw_state: list[str] | None = None
        self.firmware: str | None = None
        self.unit = UnitState()

    def set_ble_device(self, dev: BLEDevice) -> None:
        self._dev = dev

    @property
    def connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    def _on_notify(self, _h, data: bytearray) -> None:
        self._buf += data.decode(errors="ignore")
        while "\r\n" in self._buf:
            line, self._buf = self._buf.split("\r\n", 1)
            _LOGGER.debug("Mini Stat RX %s", line)
            if m := STATE_RE.search(line):
                f = m.group(1).split(",")
                self.raw_state = f
                self.firmware = f[0]
                try:
                    self.temperature, self.humidity = float(f[2]), float(f[3])
                except (IndexError, ValueError):
                    pass
                if len(f) > 12 and (u := parse_unit(f[12])):
                    self.unit = u
                else:
                    _LOGGER.debug("Mini Stat: could not parse unit state from %s", f)
            elif m := ACK_RE.search(line):
                self.temperature, self.humidity = float(m.group(1)), float(m.group(2))
            if self._reply and not self._reply.done():
                self._reply.set_result(line)

    async def _ensure(self) -> None:
        if self.connected:
            return
        self._client = await establish_connection(
            BleakClientWithServiceCache, self._dev, self._dev.address,
            disconnected_callback=lambda _c: _LOGGER.debug("Mini Stat disconnected"),
        )
        try:
            await self._client.start_notify(FD02_CHAR, lambda *_: None)
        except Exception as err:  # noqa: BLE001 - optional, app does it first
            _LOGGER.debug("FD02 notify failed: %s", err)
        await self._client.start_notify(NOTIFY_CHAR, self._on_notify)

    async def _send(self, cmd: str, timeout: float = 8) -> str | None:
        async with self._lock:
            await asyncio.wait_for(self._ensure(), 30)
            self._reply = asyncio.get_running_loop().create_future()
            _LOGGER.debug("Mini Stat TX %s", cmd)
            await self._client.write_gatt_char(CMD_CHAR, f"{cmd}\r\n".encode(), response=False)
            try:
                return await asyncio.wait_for(self._reply, timeout)
            except asyncio.TimeoutError:
                _LOGGER.warning("Mini Stat: no reply to %s", cmd)
                return None

    async def poll(self) -> None:
        await self._send("TTM(SC1)")

    async def send_state(self, key: str = KEY_NORMAL, *, power=None, mode=None, setpoint=None,
                         fan=None, sleep=None, power_digit: str | None = None) -> None:
        u = self.unit
        p = power_digit if power_digit is not None else ("1" if (u.power if power is None else power) else "0")
        m = u.mode if mode is None else mode
        t = u.setpoint if setpoint is None else int(setpoint)
        f = u.fan if fan is None else fan
        s = "1" if (u.sleep if sleep is None else sleep) else "0"
        await self._send(f"TTM(AS,{key}{p}{m}{t:02d}{f}{s}00000000)")
        # remember what we asked for until the next status poll confirms it
        if key == "0":
            self.unit = UnitState(power=p == "1", mode=m, setpoint=t, fan=f, sleep=s == "1",
                                  follow_me=u.follow_me, from_device=False)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.disconnect()
