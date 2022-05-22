import pyaudio
import wave
import numpy as np
import sys
from threading import Thread
from sys import byteorder
from array import array
from pydub import AudioSegment, effects
import time
import os
import datetime

class AudioChanelRecorder:
    def is_silent(self, snd_data, noiseGateThreshold, isRecording):
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

        self.StatusText = self.postfix+" SignalLevel: " + format(int(signallevel), '4d')+postfix
        return isSilent

    StatusText="Not Started"

    def write_auto(self, datastream, savePostfix):
        print(self.postfix+" saving data")
        filename = "file"+'{0:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now()) + savePostfix + ".mp3"

        segment=AudioSegment(datastream, sample_width=self.audio.get_sample_size(self.FORMAT), channels=self.CHANNELS, frame_rate=self.RATE)
        segment = effects.normalize(segment)
        segment.export(filename, format='mp3', bitrate='128')
        
        print(self.postfix+" saving data done")

    def makeNoiseCal(self, audioStream):
        samples = []

        calibrationSamples=15
        for i in range(calibrationSamples):
            sys.stdout.write("\rCalibrating: "+str(int(100*i/calibrationSamples))+"%")
            sys.stdout.flush()
            data=audioStream.read(self.CHUNK, exception_on_overflow = False)
            snd_data = array('h', data)
            if byteorder == 'big':
                snd_data.byteswap()
            samples.append(np.average(np.absolute(snd_data)))


        print("Samples: "+str(samples))
        print("Mean: "+str(np.average(samples)))
        print("Std: "+str(np.std(samples)))

        sigma=6
        threshold=np.average(samples)+sigma*np.std(samples)
        print(self.postfix+" Threshold: "+str(threshold))
        return threshold
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 4096
    RECORD_SECONDS = 5
    postfix=""

    audio = pyaudio.PyAudio()

    def Run(self, deviceIndex, savePostfix):
        self.postfix=savePostfix
        # start Recording
        stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                            rate=self.RATE, input=True,
                            frames_per_buffer=self.CHUNK, input_device_index=deviceIndex)
        print(self.postfix+" recording...")
        frames = []

        recordStarted=False
        lastNoise=time.time()

        #gateThreshold = self.makeNoiseCal(stream)
        gateThreshold = 750

        while 1:
            data=stream.read(self.CHUNK, exception_on_overflow = False)
            snd_data = array('h', data)
            if byteorder == 'big':
                snd_data.byteswap()

            silent = self.is_silent(snd_data,gateThreshold, recordStarted)

            if(silent==False):
                lastNoise = time.time()
                if(recordStarted==False):
                    print("\n"+self.postfix+" Start recording")
                recordStarted=True

            if(recordStarted):
                frames.append(np.array(snd_data))
                if(time.time()-lastNoise>3):
                    print("\n"+self.postfix+" Stop recording")
                    recordStarted=False
                    Thread(target=self.write_auto, args=(b''.join(frames), savePostfix)).start()
                    frames.clear()

        print("finished recording")

        # stop Recording
        stream.stop_stream()
        stream.close()
        audio.terminate()

def main():
    device1=AudioChanelRecorder()
    device2=AudioChanelRecorder()

    Thread(target=device1.Run, args=(1,"out")).start()
    Thread(target=device2.Run, args=(2,"in")).start()

    while 1:
        time.sleep(0.2)

        sys.stdout.write("\r"+device1.StatusText+"     "+device2.StatusText)
        sys.stdout.flush()

if __name__ == "__main__":
    main()
