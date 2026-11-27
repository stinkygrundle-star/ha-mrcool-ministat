# MRCOOL Mini Stat (Bluetooth) for Home Assistant

Local control of the **MRCOOL Mini Stat** IR/Bluetooth thermostat (MTSK02, shows up as `SMARTHVAC_01_xxx`) straight from Home Assistant's Bluetooth. No cloud, no extra hardware, no IR blaster: HA talks to the Mini Stat, and the Mini Stat keeps sending IR to your MRCOOL mini-split as usual.

Unofficial. Not affiliated with MRCOOL. Tested on one unit (firmware V1.1.2) with a Raspberry Pi 4's built-in Bluetooth.

## What you get
- **Climate entity:** off, auto, cool, dry, fan only, heat · setpoint 62–86 °F · fan auto/low/medium/high · presets sleep and freeze protection (FP)
- **Real state readback:** changes made on the thermostat or in the app show up in HA
- **Sensors:** room temperature, humidity and battery voltage (2 x AA; roughly 3.0 V new, replace around 2.4 V) from the Mini Stat
- **Buttons:** turbo, swing, louver step, display LED, follow me (these are toggles, like the app)

## Install (HACS)
1. HACS → ⋮ → **Custom repositories** → add `https://github.com/stinkygrundle-star/ha-mrcool-ministat` as type **Integration**.
2. Install **MRCOOL Mini Stat (Bluetooth)** and restart Home Assistant.
3. On the Mini Stat, hold **Temp Up + Power for 5 seconds** until the Bluetooth icon shows.
4. Settings → Devices & services → **Add integration** → MRCOOL Mini Stat. Pick your thermostat (or enter its Bluetooth address).

Manual install: copy `custom_components/mrcool_ministat` into your HA `config/custom_components/` folder and restart.

## Things to know
- **One connection at a time.** While HA is connected, the SmartHVAC phone app can't connect. Disable the integration if you need the app.
- **Bluetooth wake.** The Mini Stat turns its Bluetooth off when nothing is connected (within a few minutes). HA keeps it awake while connected, but after a long HA outage or power cut you must wake it again (Temp Up + Power, 5 s). An automation that notifies you when `sensor.<name>_temperature` goes unavailable is a good idea.
- **Batteries.** The Mini Stat runs on 2 x AA and its screen only shows a low-battery icon late. The `Battery voltage` sensor (about 3.0 V with new batteries) lets you get warned early. Suggested phone alert, replacing the entity and notify service names with yours:

  ```yaml
  alias: Mini Stat low battery
  triggers:
    - trigger: numeric_state
      entity_id: sensor.mini_stat_battery_voltage
      below: 2.4
      for: { minutes: 30 }
    - trigger: time
      at: "09:00:00"   # daily reminder until replaced
  conditions:
    - condition: numeric_state
      entity_id: sensor.mini_stat_battery_voltage
      below: 2.4
  actions:
    - action: notify.mobile_app_your_phone
      data:
        title: Replace Mini Stat batteries
        message: "Mini Stat batteries are at {{ states('sensor.mini_stat_battery_voltage') }} V. Time to replace the 2 AA batteries."
  ```
- **Range.** Your HA Bluetooth adapter (or an ESPHome Bluetooth proxy) needs to be within range of the thermostat.
- Turbo, swing, louver step and display LED are press-to-toggle buttons; the thermostat doesn't report their state (the LED in particular can't be known, since the Mini Stat talks to the unit by one-way IR). Follow me state is reported as an attribute on the climate entity.

## How it works
The Mini Stat exposes a BLE serial service. Commands are plain ASCII (`TTM(SC1)` for status, `TTM(AS,...)` to set state). See [PROTOCOL.md](PROTOCOL.md). Contributions and captures from other units/firmware are welcome.
