import time
import random
import threading
import asyncio
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext

# Create sequential data block starting at address 1
block = ModbusSequentialDataBlock(1, [1, 75, 62, 72, 0])

# In modern Pymodbus 3.8+, pass block directly as the single argument
context = ModbusServerContext(block)

def simulate_process():
    """Simulates motor sensor fluctuations and an overload trip after 30s."""
    elapsed = 0
    while True:
        time.sleep(1)
        elapsed += 1
        
        if elapsed > 30:
            load = min(150, 95 + random.randint(15, 30))
            temp = min(110, 85 + random.randint(5, 15))
            status = 0       # Tripped
            alarm_code = 14   # Overload Alarm
        else:
            load = 70 + random.randint(-4, 4)
            temp = 72 + random.randint(-1, 2)
            status = 1       # Running
            alarm_code = 0

        # Function code 3 (Holding Registers), starting at address 1
        context.setValues(3, 1, [status, load, 62, temp, alarm_code])

async def run_server():
    threading.Thread(target=simulate_process, daemon=True).start()
    print("[*] Modbus TCP Server running on 127.0.0.1:5020")
    print("[*] Server is active and waiting for connections...")
    await StartAsyncTcpServer(context=context, address=("127.0.0.1", 5020))

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")