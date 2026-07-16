import socket
import time

try:
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(("2406:da1a:314:7101:6108:13cf:61f5:863b", 5432))
    print("✅ TCP connection to Supabase IPv6:5432 succeeded!")
    s.close()
except Exception as e:
    print("❌ TCP connection failed:", e)
