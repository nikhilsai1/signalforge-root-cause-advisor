import time
import json
import os
from datetime import datetime
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("127.0.0.1", port=5020)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, "live_telemetry.json")

print("[*] Telemetry Bridge started.")
print(f"[*] Writing Modbus data to: {OUTPUT_FILE}")

while True:
    try:
        if not client.connected:
            client.connect()
        rr = client.read_holding_registers(address=0, count=5)
        if not rr.isError():
            status, load, tank, temp, alarm = rr.registers
            data = {
                "timestamp": time.time(),
                "timestamp_readable": datetime.now().strftime("%H:%M:%S"),
                "motor_run_status": "RUNNING" if status == 1 else "TRIPPED",
                "motor_load_pct": load,
                "tank_level_pct": tank,
                "bearing_temp_c": temp,
                "active_alarm_code": alarm,
                "root_cause_candidate": "VFD_OVERLOAD" if alarm == 14 else "NONE",
                "Motor_1_RunStatus": "RUNNING" if status == 1 else "TRIPPED",
                "Motor_1_Load_Pct": load,
                "Tank_Level_Pct": tank,
                "Bearing_Temp_C": temp,
                "Active_Alarm_Code": alarm
            }
            with open(OUTPUT_FILE, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[{data['timestamp_readable']}] [OK] Live Data -> Motor: {data['motor_run_status']} | Load: {load}% | Temp: {temp}C")
        else:
            print("[!] Could not read registers. Is modbus_sim_server running?")
    except Exception as e:
        print(f"[!] Error: {e} (will retry connection)")
        client.close()
    time.sleep(1)