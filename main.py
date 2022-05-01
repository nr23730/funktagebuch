import pyaudio
import wave
import numpy as np
import sys
from sys import byteorder
from array import array
from pydub import AudioSegment, effects
import time
import os
import datetime

def is_silent(snd_data, noiseGateThreshold, isRecording):
    "Returns 'True' if below the 'silent' threshold"
    signallevel = np.average(np.absolute(snd_data))

    isSilent = signallevel < noiseGateThreshold

    if isSilent:
        postfix="            "
    else:
        postfix=" Gate Open  "

    if isRecording :
        prefix="Recording  "
    else:
        prefix="           "

    sys.stdout.write("\r"+prefix+"SignalLevel: " + format(int(signallevel), '4d')+postfix)
    sys.stdout.flush()
    return isSilent

def write_auto(savePostfix):
    filename = "file"+'{0:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now()) + savePostfix + ".mp3"

    datastream = b''.join(frames)

    segment=AudioSegment(datastream, sample_width=audio.get_sample_size(FORMAT), channels=CHANNELS, frame_rate=RATE)
    segment = effects.normalize(segment)
    segment.export(filename, format='mp3', bitrate='128')
    frames.clear()


def makeNoiseCal(audioStream):
    samples = []

    calibrationSamples=15
    for i in range(calibrationSamples):
        sys.stdout.write("\rCalibrating: "+str(int(100*i/calibrationSamples))+"%")
        sys.stdout.flush()
        data=audioStream.read(CHUNK, exception_on_overflow = False)
        snd_data = array('h', data)
        if byteorder == 'big':
            snd_data.byteswap()
        samples.append(np.average(np.absolute(snd_data)))


    print("Samples: "+str(samples))
    print("Mean: "+str(np.average(samples)))
    print("Std: "+str(np.std(samples)))

    sigma=6
    threshold=np.average(samples)+sigma*np.std(samples)
    print("Threshold: "+str(threshold))
    return threshold

if(len(sys.argv)==0):
    print("Usage: main.py [AudioDeviceIndex] [filePostfix]")

if len(sys.argv)>1:
    deviceIndex=int(sys.argv[1])
else:
    deviceIndex=0

if(len(sys.argv)>2):
    savePostfix=sys.argv[2]
else:
    savePostfix=""

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 4096
RECORD_SECONDS = 5

audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK, input_device_index=deviceIndex)
print("recording...")
frames = []

recordStarted=False
lastNoise=time.time()

gateThreshold = makeNoiseCal(stream)

while 1:
    data=stream.read(CHUNK, exception_on_overflow = False)
    snd_data = array('h', data)
    if byteorder == 'big':
        snd_data.byteswap()

    silent = is_silent(snd_data,gateThreshold, recordStarted)

    if(silent==False):
        lastNoise = time.time()
        if(recordStarted==False):
            print("\nStart recording")
        recordStarted=True

    if(recordStarted):
        frames.append(np.array(snd_data))
        if(time.time()-lastNoise>3):
            print("\nStop recording")
            recordStarted=False
            write_auto(savePostfix)


print("finished recording")

# stop Recording
stream.stop_stream()
stream.close()
audio.terminate()
