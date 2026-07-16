import socket

def check():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 5432))
    # Send a Postgres StartupMessage
    # Length: 8 bytes (int32)
    # Protocol: 196608 (int32, v3.0)
    msg = b'\x00\x00\x00\x08\x00\x03\x00\x00'
    s.sendall(msg)
    data = s.recv(1024)
    print("RAW:", data)
    try:
        print("cp1251:", data.decode("cp1251"))
    except:
        pass
    try:
        print("cp866:", data.decode("cp866"))
    except:
        pass
    s.close()

if __name__ == "__main__":
    check()
