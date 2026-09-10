import logging
import threading
import time
import random
from datetime import datetime

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import StartTcpServer

HOST = "127.0.0.1"
PORT = 5020
FAULT_TRIGGER_SECONDS = 30

# Register layout (holding registers, function code 3):
#   0: Motor_1_RunStatus   (1=running, 0=tripped)
#   1: Motor_1_Load_Pct    (~70 normal, ~110-125 fault)
#   2: Tank_Level_Pct      (constant 62)
#   3: Bearing_Temp_C      (~72 normal, ~90-100 fault)
#   4: Active_Alarm_Code   (0 normal, 14 fault)

lock = threading.Lock()
fault_active = False
start_time = time.monotonic()

# zero_mode=True makes register address 0 map directly to datastore index 0,
# matching standard Modbus wire addressing (address 0 = first holding register).
# Without it, pymodbus applies its legacy +1 offset and every read comes back
# shifted by one register.
store = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(0, [1, 70, 62, 72, 0]),
    zero_mode=True,
)
context = ModbusServerContext(slaves=store, single=True)


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# pymodbus logs connect/disconnect events internally at DEBUG level (there's no
# INFO-level hook for it, and no peer IP attached to those specific messages).
# Rather than dumping pymodbus's full DEBUG stream (which includes a hex trace
# of every single poll), filter it down to just connection lifecycle lines and
# print them in the same timestamped style as everything else.
_CONNECTION_EVENTS = {
    "Connected to server": "[CONNECT] Client connected",
    "Connection lost": "[DISCONNECT] Client disconnected",
}


class _ConnectionLogFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        for needle, label in _CONNECTION_EVENTS.items():
            if needle in msg:
                log(label)
                break
        return False  # never let pymodbus's raw line print, we re-emit our own


def setup_connection_logging():
    pymodbus_logger = logging.getLogger("pymodbus.logging")
    pymodbus_logger.setLevel(logging.DEBUG)
    pymodbus_logger.addFilter(_ConnectionLogFilter())
    pymodbus_logger.addHandler(logging.NullHandler())
    pymodbus_logger.propagate = False


def normal_registers():
    return [1, 70 + random.randint(-4, 4), 62, 72 + random.randint(-1, 2), 0]


def fault_registers():
    return [0, 95 + random.randint(15, 30), 62, 85 + random.randint(5, 15), 14]


def write_registers(values):
    with lock:
        store.setValues(3, 0, values)


def set_fault(active, reason):
    global fault_active
    with lock:
        if active == fault_active:
            return
        fault_active = active
    write_registers(fault_registers() if active else normal_registers())
    if active:
        log(f"[FAULT] Fault state TRIGGERED ({reason}) -> Motor_1_RunStatus=0, Active_Alarm_Code=14")
    else:
        log(f"[RESET] Returned to normal state ({reason})")


def simulate():
    while True:
        time.sleep(1)
        elapsed = time.monotonic() - start_time
        with lock:
            currently_fault = fault_active
        if elapsed >= FAULT_TRIGGER_SECONDS and not currently_fault:
            set_fault(True, "auto 30s timer")
        elif currently_fault:
            write_registers(fault_registers())
        else:
            write_registers(normal_registers())


def console_trigger():
    log("[*] Press ENTER to force-trigger the fault now. Type 'reset' + ENTER to return to normal (rehearsal only).")
    while True:
        try:
            cmd = input().strip().lower()
        except EOFError:
            return
        if cmd == "reset":
            set_fault(False, "manual reset")
        else:
            set_fault(True, "manual trigger")


def main():
    setup_connection_logging()

    threading.Thread(target=simulate, daemon=True).start()
    threading.Thread(target=console_trigger, daemon=True).start()

    log(f"[*] Modbus TCP Server (pymodbus, spec-compliant) starting on {HOST}:{PORT}")
    log(f"[*] Fault will auto-trigger {FAULT_TRIGGER_SECONDS}s after startup, or press ENTER anytime.")
    StartTcpServer(context=context, address=(HOST, PORT))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
