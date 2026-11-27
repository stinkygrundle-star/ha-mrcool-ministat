# MRCOOL Mini Stat Bluetooth protocol notes

Decoded 2026-11-26 from a Android phone HCI snoop log of the MRCOOL SmartHVAC app.

## Device
- Name: SMARTHVAC_01_xxx, address XX:XX:XX:XX:XX:XX, firmware V1.1.2
- No pairing, no password, no encryption. Plain ASCII text commands.
- Bluetooth must be woken on the thermostat (hold Temp Up + Power 5 s); it turns off after 15 min of inactivity (whether a live connection keeps it on is still untested).

## GATT
| Purpose | Service | Characteristic | Handle |
|---|---|---|---|
| Commands (write without response) | FFE5 | FFE9 | 0x0020 |
| Replies (notify) | FFE0 | FFE4 | 0x001B (CCCD 0x001D) |
| App enables this first (notify) | FD00 | FD02 | 0x0079 (CCCD 0x007A) |

App connect sequence: enable FD02 notify -> enable FFE4 notify -> read FF92 (=08) and FF95 (=02) -> send `TTM(SC1)` -> send `TTM(TS,...)`.
Every command ends with `\r\n`.

## Commands
- `TTM(SC1)` : ask for full status. Reply:
  `(State:V1.1.2,<MAC>,68.9,57.1,0,5,85,2.6,1,1,62,86,1469000,85,85,0,0,1,3,8)`
  - 68.9 = room temperature °F, 57.1 = humidity % (likely), 62/86 = setpoint min/max. Other fields unknown.
- `TTM(TS,YY:MM:DD:W:HH:MM:SS:0:-05:00)` : set the clock (example `TTM(TS,26:11:26:5:14:36:06:0:-05:00)`, W=5 for Thursday).
- `TTM(AS,0PMTTF000000000)` : set the unit state (15 digits after the comma).
  - P = power (1 = on)
  - M = mode (4 = heat, 3 = fan only; others not yet captured)
  - TT = setpoint °F (69, 70)
  - F = fan (0 = auto, 1 = low; others not yet captured)
  - Trailing 9 zeros: unknown (maybe swing/sleep/timer)
- Every command is answered with `{ACK:<temp>,<humidity>}`, e.g. `{ACK:68.9,57.1}`.

## Captured sequence (all confirmed)
| Command | Meaning |
|---|---|
| `AS,014700000000000` | heat, 70°F, fan auto |
| `AS,014690000000000` | heat, 69°F, fan auto |
| `AS,014691000000000` | heat, 69°F, fan low |
| `AS,013690000000000` | fan only, 69°F, fan auto |

## Still to learn
Mode digits for cool, dry, auto and off (P=0?); fan digits for medium/high; whether the connection keeps Bluetooth from timing out.

## Capture 2 (2026-11-26 7:42–8:01 PM) — revised command layout
`TTM(AS,KPMTTFX00000000)` where **K is a "key" code** (which button was pressed) and the rest is the full desired state.

| K | Meaning (confirmed by worksheet timing) |
|---|---|
| 0 | normal state change (mode / setpoint / fan / power) |
| 1 | FP (freeze protection) button, sets M=5 |
| 2 | Turbo |
| 3 | Swing toggle (P digit 1) / louver step (P digit 0, sent once per tap) |
| 5 | LED display toggle |
| 6 | Follow me |

M (mode): 0 auto, 1 cool, 2 dry, 3 fan only, 4 heat, 5 FP (8°C/46°F heat).
F (fan): 0 auto, 1 low, 2 medium, 3 high.
P: 1 on, 0 off (with K=0).
X (digit 7): toggles with some extras (seen 1 around turbo and follow me); meaning TBD.

### Status readback
`TTM(SC1)` field 13 looks like the live state: `1469000` = on, heat, 69°F, fan auto; `1569010` after FP; `1469001`. Format appears to be P M TT F + flags, so HA can probably read the real mode/setpoint instead of assuming it.
