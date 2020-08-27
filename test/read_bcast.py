import socket
import json
from threading import Thread
import struct
import time

DELAY = 1/30

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", 2566))

msg, addr = s.recvfrom(1024)
print(msg)
leds = [[0,0,0]]*36
print(leds)

def serialize_strip(led_strip):
    m = b''
    for i in led_strip:
        m+=struct.pack("!BBB", i[0], i[1], i[2])
    return m

def generate_frame_message(serialized_strip):
    m_base = b''
    m_base += struct.pack("!BB", 0, 255)
    m_base += serialized_strip
    print(m_base)
    return m_base

def recv_thread():
    global s

    while True:
        m, addr = s.recvfrom(1024)
        print(m)

Thread(target=recv_thread).start()
m_1 = serialize_strip(leds)
m = generate_frame_message(m_1)
s.sendto(m, addr)

while True:
    for i in range(len(leds)):
        leds[i] = [255, 0, 0]
        m_1 = serialize_strip(leds)
        m = generate_frame_message(m_1)
        s.sendto(m, addr)
        time.sleep(DELAY)
    for i in range(len(leds)):
        leds[i] = [0, 255, 0]
        m_1 = serialize_strip(leds)
        m = generate_frame_message(m_1)
        s.sendto(m, addr)
        time.sleep(DELAY)