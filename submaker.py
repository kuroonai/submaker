#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 12 22:29:13 2019

@author:Naveen Kumar Vasudevan, 
        400107764,
        Doctoral Student, 
        The Xi Research Group, 
        McMaster University, 
        Hamilton, 
        Canada.
        
        naveenovan@gmail.com
        https://naveenovan.wixsite.com/kuroonai
"""
'''
  Make sure that ffmpeg is installed and in PATH on your system
  https://ffmpeg.org/download.html
  
  usage
  
  This tool translates the given audio into subtitles in the language one wants by slicing the length to the seconds given on the time line
  Python submaker.py /media/sf_dive/FFOutput/d1.mp3 en 10 


'''

import speech_recognition as sr
import os
from pydub import AudioSegment
import numpy as np
from tqdm import tqdm
import sys
import subprocess
from fnmatch import fnmatch

from googletrans import Translator
translator = Translator()


loc =  sys.argv[1] #'/media/sf_dive/FFOutput/d4.mp3' #sys.argv[1]
lang = sys.argv[2] #'ta' #sys.argv[2]
cut =  int(sys.argv[3]) #10 #int(sys.argv[3])

#alternates = sys.argv[4].split(',')

if os.name == 'posix':
    s = '/'
    os.chdir(s.join(loc.split('/')[:-1]))
    inputfile = loc.split('/')[-1]
    fn ="%s.srt"%inputfile.split('.')[0]

elif os.name == 'nt':
    s = '\\'
    os.chdir(s.join(loc.split('\\')[:-1]))
    inputfile = loc.split('\\')[-1]
    fn ="%s.srt"%inputfile.split('.')[0]

    
os.remove('transcript.wav') if os.path.exists('transcript.wav') else None

if inputfile.split('.')[1] != 'wav':subprocess.call(['ffmpeg', '-i', inputfile,'transcript.wav'])

wholeaudio = AudioSegment.from_wav("transcript.wav")
wholelen = len(wholeaudio)

os.remove(fn) if os.path.exists(fn) else None
os.remove("translated.srt") if os.path.exists("translated.srt") else None

for seq,t1t,t2t in tqdm(zip(range(1,int(wholelen/(cut*1000))+1),np.arange(0, round(wholelen/cut), cut), np.arange(cut, round(wholelen/cut), cut)), total=int(wholelen/(cut*1000)), unit = "segment" ):
    #print(t1*1000,t2*1000, t2*1000-t1*1000)
    t1 = t1t*1000
    t2 = t2t*1000
    
    if t2 > wholelen : 
    
        break
# transcribe audio file                                                         
    #AUDIO_FILE = "transcript.wav"
    #wholeaudio = AudioSegment.from_wav("transcript.wav")
    newAudio = wholeaudio[t1:t2]
    newAudio.export('temp.wav', format="wav")

    newfile = 'temp.wav'
    # use the audio file as the audio source                                        
    r = sr.Recognizer()
    
    with sr.AudioFile(newfile) as source:
        audio = r.record(source)  # read the entire audio file                  
        
        #print("\n%d\n00:00:00,%d --> 00:00:00,%d"%(seq,t1,t2),file=open("output.srt", "a"))
        try:
            
            #print(r.recognize_google(audio, language="ta-IN"),file=open("output.srt", "a"))
            if fnmatch(lang,'en*'):
                trans = r.recognize_google(audio, language=lang)
                print("\n%d\n00:00:00,%d --> 00:00:00,%d"%(seq,t1,t2),file=open(fn, "a"))
                print(trans,file=open(fn, "a"))
            else:
                trans=translator.translate(r.recognize_google(audio, language=lang)).text
                print("\n%d\n00:00:00,%d --> 00:00:00,%d"%(seq,t1,t2),file=open(fn, "a"))
                print(trans,file=open(fn, "a"))
                #en-US - English, US
                #en-IN - English, India
                #en-GB - English, UK
                #vi-VN - Vietnamese, Vietnam
                #ta-IN - Tamil, India
                #es-MX - Spanish, Mexico
        except:
            pass


