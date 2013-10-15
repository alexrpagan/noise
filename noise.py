import pyaudio
import audioop
import struct
import numpy
import wave
import sys
from Queue import Queue
from threading import Thread
from collections import deque

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
WINDOW_SIZE = .5
MAX = 500

def play_audio(filename, q):

    wf = wave.open(filename, 'rb')

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)

    data = wf.readframes(CHUNK)

    chunks = []
    while data != '':
        chunks.append(data)
        data = wf.readframes(CHUNK)

    loudness = 1

    window = deque([1],maxlen=5)

    while True:
        for chunk in chunks:
            if not q.empty():
                loudness = q.get()
                if loudness == -1:
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    q.task_done()
                    return
                else:
                    window.append(loudness)
            adjustment = float(sum(window)/len(window))
            s = numpy.fromstring(chunk, numpy.int16) * adjustment
            s = struct.pack('h'*len(s), *s)
            stream.write(s)

def find_input_device(p):
    device_index = None
    for i in range( p.get_device_count() ):
        devinfo = p.get_device_info_by_index(i)
        for keyword in ["mic","input"]:
            if keyword in devinfo["name"].lower():
                device_index = i
                return device_index
    if device_index == None:
        return None
    return device_index

def open_mic_stream(p):
    device_index = find_input_device(p)
    stream = p.open(  format = FORMAT,
                            channels = CHANNELS,
                            rate = RATE,
                            input = True,
                            input_device_index = device_index,
                            frames_per_buffer = INPUT_FRAMES_PER_BLOCK)
    return stream

def main():

    if len(sys.argv) < 2:
        print("Usage: %s filename.wav" % sys.argv[0])
        sys.exit(-1)

    p = pyaudio.PyAudio()
    q = Queue()
    t = Thread(target=play_audio, args=(sys.argv[1], q))
    t.daemon = True
    t.start()

    stream = open_mic_stream(p)

    samples = []

    try:
        while 1:
                if samples and len(samples) % int(WINDOW_SIZE / INPUT_BLOCK_TIME) == 0:
                    mean = numpy.mean(samples)
                    q.put(float(mean/MAX))
                    samples = []
                block = stream.read(INPUT_FRAMES_PER_BLOCK)
                amplitude = audioop.rms(block, 2)
                samples.append(amplitude)
    except KeyboardInterrupt:
        q.put(-1)
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main()

