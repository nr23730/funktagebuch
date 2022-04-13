import pyaudio
import wave
import numpy as np
from sys import byteorder
from array import array
import time
import datetime
#import speech_recognition as sr

def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    signallevel = np.average(np.absolute(snd_data))
    #print(signallevel)
    return signallevel < 50

def write_auto():
    filename = "file"+'{0:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now()) + "_in.wav"
    waveFile = wave.open(filename, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
    frames.clear()

    # r = sr.Recognizer()
    #
    # audiofile = sr.AudioFile(filename)
    # with audiofile as source:
    #     myAudio = r.record(source)
    # try:
    #     s = r.recognize_sphinx(myAudio, language="de-DE")
    #     print("Text: " + s)
    # except Exception as e:
    #     print("Exception: " + str(e))

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 4096
RECORD_SECONDS = 5

audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK, input_device_index=0)
print("recording...")
frames = []

recordStarted=False
lastNoise=time.time()
#for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
while 1:
    data=stream.read(CHUNK)
    snd_data = array('h', data)
    if byteorder == 'big':
        snd_data.byteswap()

    silent = is_silent(snd_data)

    if(silent==False):
        lastNoise = time.time()
        if(recordStarted==False):
            print("Start recording")
        recordStarted=True

    if(recordStarted):
        frames.append(15*np.array(snd_data))
        if(time.time()-lastNoise>3):
            print("Stop recording")
            recordStarted=False
            write_auto()


print("finished recording")

# stop Recording
stream.stop_stream()
stream.close()
audio.terminate()
