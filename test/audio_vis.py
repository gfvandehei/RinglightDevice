import pyaudio
import numpy as np
from scipy.interpolate import interp1d
import math
import socket
import time
import struct
from threading import Thread

CHUNK = 4096 # number of data points to read at a time
RATE = 44100 # time resolution of the recording device (Hz)


p=pyaudio.PyAudio() # start the PyAudio class

"""info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
exit()"""
stream=p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
              frames_per_buffer=CHUNK, input_device_index=7) #uses default input device
m = interp1d([0,6000],[0,36])
current_data = 0


leds = [[0,0,0]]*36
print(leds)

def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

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

def send_audio_thread():
    global m
    global leds
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", 2566))
    msg, addr = s.recvfrom(1024)
    m_1 = serialize_strip(leds)
    m_2 = generate_frame_message(m_1)
    while True:
        real_value = int(translate(current_data, 0, 5000, 0, 36))
        if(real_value >= 36):
            real_value = 36
        print(real_value)
        for i in range(real_value):
            leds[i] = [0, 0, 255]
        m_1 = serialize_strip(leds)
        m_2 = generate_frame_message(m_1)
 
        s.sendto(m_2, addr)
        leds = [[0, 0, 0]]*36
        time.sleep(1/30)

Thread(target=send_audio_thread).start()

while True: #to it a few times just to see
    data = np.fromstring(stream.read(CHUNK),dtype=np.int16)
    data_fft = np.fft.rfft(data, 1)
    current_data = int(np.abs(data_fft[0]))
    if current_data > 5000:
        current_data = 6000
    #print(current_data)




# close the stream gracefully
stream.stop_stream()
stream.close()
p.terminate()