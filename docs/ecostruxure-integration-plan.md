# EcoStruxure Integration — Step-by-Step for Manjunath

## What this actually gets us (read this first)

Right now `integration/modbus_sim_server.py` is a real Modbus TCP server (you wrote it, it works, it's genuinely real protocol communication) — but nothing in EcoStruxure talks to it. The backend is the only thing reading it.

**The plan below turns your existing simulator into a shared PLC data source that BOTH EcoStruxure and the FastAPI backend read from independently, over real Modbus.** That's the strongest honest claim we can make without physical PLC hardware: a real Schneider HMI screen, driven by a real Modbus connection, showing the exact same live tag values the AI is reasoning about. When someone asks "is this real EcoStruxure," the answer becomes yes — same data source, same protocol, two real consumers.

**Don't change `telemetry_bridge.py` or any backend code.** They already work correctly against this simulator. This is entirely EcoStruxure-side configuration.

## Register map (your simulator's actual protocol — use these exact values)

Your `modbus_sim_server.py` responds to Modbus function code 3 (Read Holding Registers), unit ID can be anything (it's not validated), starting address 0, all values 16-bit unsigned integers:

| Address | Register | Normal range | Fault value |
|---|---|---|---|
| 0 | Motor_1_RunStatus | 1 = running | 0 = tripped |
| 1 | Motor_1_Load_Pct | ~66-74 | ~110-125 |
| 2 | Tank_Level_Pct | 62 (constant) | 62 (unchanged) |
| 3 | Bearing_Temp_C | ~71-74 | ~90-100 |
| 4 | Active_Alarm_Code | 0 | 14 (VFD overload) |

The fault triggers automatically 30 seconds after the simulator starts, and stays until you restart it.

## Steps

### 1. Start the shared data source
```
python integration/modbus_sim_server.py
```
Leave this running for the rest of this setup **and** for the demo itself — both EcoStruxure and the backend need it alive simultaneously. Confirm it prints `Modbus TCP Server running on 127.0.0.1:5020`.

**If EcoStruxure runs on a different machine than this simulator** (e.g. a separate Windows PC with the Schneider software, not your dev laptop): change line 42 in `modbus_sim_server.py` from `s.bind(('127.0.0.1', 5020))` to `s.bind(('0.0.0.0', 5020))` and use that machine's actual LAN IP (not `127.0.0.1`) in EcoStruxure's driver config below. If they're on the same machine, leave it as-is and use `127.0.0.1`.

### 2. New project in EcoStruxure Operator Terminal Expert
Open the software, create a new HMI project (any target panel model is fine — we're only using the software's built-in simulator/runtime, not deploying to physical hardware).

### 3. Add a Modbus TCP/IP driver
In the project's Communication/Driver settings, add a new driver:
- Driver type: **Modbus TCP/IP** (sometimes listed as "MODBUS TCP" or "Modbus Ethernet")
- IP address: `127.0.0.1` (or the LAN IP from step 1 if on a different machine)
- Port: `5020`
- Unit ID / Slave ID: `1` (your simulator ignores this value, so any number works)

### 4. Define tags
In the tag/address database, add 5 tags pointing at that driver, one per register above:

| Tag name | Address | Data type |
|---|---|---|
| Motor_1_RunStatus | 400001 (or 0, depending on your software's addressing convention) | 16-bit unsigned / Word |
| Motor_1_Load_Pct | 400002 (or 1) | 16-bit unsigned / Word |
| Tank_Level_Pct | 400003 (or 2) | 16-bit unsigned / Word |
| Bearing_Temp_C | 400004 (or 3) | 16-bit unsigned / Word |
| Active_Alarm_Code | 400005 (or 4) | 16-bit unsigned / Word |

Note: some HMI tools address holding registers starting at 40001/400001 (1-indexed with a 4xxxx prefix), others use the raw 0-indexed address directly. If the values don't look right once you're testing (step 6), this offset-by-one convention is the first thing to check.

### 5. Build the screens
Keep it simple, per the original plan — this is a credibility prop, not the main deliverable:

**Screen 1 — Motor status:**
- A status lamp/indicator bound to `Motor_1_RunStatus` (green when 1, red when 0)
- Numeric displays for `Motor_1_Load_Pct`, `Bearing_Temp_C`, `Tank_Level_Pct`
- Optional: a bar graph or trend for `Motor_1_Load_Pct` so the climb to fault is visually obvious

**Screen 2 — Alarm banner:**
- A text or lamp object bound to `Active_Alarm_Code`, visible/red when the value equals 14, hidden/green otherwise
- Label it something like "VFD OVERLOAD" to match `SOP-14`'s actual alarm description

### 6. Test it live
Run EcoStruxure's simulation/runtime mode (with the driver pointed at the running Modbus server from step 1). You should see:
- Normal values for the first ~30 seconds (status=running, load ~70%, temp ~72°C, alarm=0)
- After ~30 seconds: status flips to tripped, load jumps to ~110-125%, temp climbs to ~90-100°C, alarm banner shows 14

This is the exact same fault injection `checkpoint_live_modbus.py` already verified against the backend — if EcoStruxure shows the same transition at the same time as `data/live_telemetry.json` updates, you've confirmed both are reading the identical real data.

### 7. Verification checkpoint (for the demo and for your own confidence)
With the simulator, EcoStruxure runtime, and `telemetry_bridge.py` all running at once:
1. Screenshot EcoStruxure showing the fault state (status=tripped, alarm banner lit, load >100%)
2. In the same moment, check `data/live_telemetry.json` — it should show matching values (`"Active_Alarm_Code": 14`, similar load/temp numbers, allowing for the ~1 second poll interval)
3. Save both as evidence — this pairing is the actual proof for the "real EcoStruxure integration" claim

## Time budget and fallback

This is real configuration work in unfamiliar software, not a code change — budget **45-60 minutes**, not the original plan's 15-minute stretch-goal timebox (that 15-minute box was for Path B, visual embedding, which is a much harder ask). If you're past 60 minutes and the driver won't connect or tags won't bind:

- **Don't burn the whole remaining clock on it.** Fall back to presenting what's already true and demoed: real Modbus protocol integration (simulator ↔ backend), verified end-to-end, architecturally identical to what EcoStruxure would need — "the pipe is real, we ran out of time to also wire the Schneider HMI screen into it." That's an honest, still-credible fallback position, distinct from claiming something that isn't there.
- Common failure points to check first if the driver won't connect: firewall blocking port 5020, wrong IP (localhost vs LAN IP if on separate machines), and the address-offset convention in step 4.
