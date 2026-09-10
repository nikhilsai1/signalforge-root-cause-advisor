import socket, threading, struct, time, random

registers = [1, 75, 62, 72, 0]

def simulate():
    global registers
    elapsed = 0
    while True:
        time.sleep(1)
        elapsed += 1
        if elapsed > 30:
            registers = [0, min(150, 95 + random.randint(15, 30)), 62, min(110, 85 + random.randint(5, 15)), 14]
        else:
            registers = [1, 70 + random.randint(-4, 4), 62, 72 + random.randint(-1, 2), 0]

def handle_client(conn):
    while True:
        try:
            header = conn.recv(6)
            if not header or len(header) < 6:
                break
            tid, pid, length = struct.unpack('>HHH', header)
            body = conn.recv(length)
            if not body:
                break
            unit_id = body[0]
            func_code = body[1]
            if func_code == 3:
                addr, count = struct.unpack('>HH', body[2:6])
                val_bytes = b''.join([struct.pack('>H', v) for v in registers[:count]])
                resp_pdu = bytes([func_code, len(val_bytes)]) + val_bytes
                resp = struct.pack('>HHH', tid, pid, len(resp_pdu) + 1) + bytes([unit_id]) + resp_pdu
                conn.sendall(resp)
        except Exception:
            break
    conn.close()

def main():
    threading.Thread(target=simulate, daemon=True).start()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 5020))
    s.listen(5)
    print('[*] Modbus TCP Server running on 127.0.0.1:5020')
    print('[*] Ready for EcoStruxure & Telemetry Bridge!')
    while True:
        conn, _ = s.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n[*] Server stopped.')
