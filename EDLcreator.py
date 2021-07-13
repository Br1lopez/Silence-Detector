import math
import os
import argparse
import cv2
from moviepy.editor import VideoFileClip
from pathlib import Path

dir = os.getcwd()
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--videopath', help='Raw clip path')
parser.add_argument('-t', '--title', help='Raw clip name')
args = parser.parse_args()

framerate = 25

def get_sec(time_str):
    h, m, s, f = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s) + float(f)/float(framerate)

if args.videopath:
    cap=cv2.VideoCapture(args.videopath)
    framerate = cap.get(cv2.CAP_PROP_FPS)
    video_folder, video_name = os.path.split(args.videopath)

    if Path(args.videopath+".txt").is_file():
        parameters_path = args.videopath+".txt"
    elif Path(os.path.splitext(args.videopath)[0]+".txt").is_file():
        parameters_path = os.path.splitext(args.videopath)[0]+".txt"
    elif Path(video_folder+"\parameters.txt").is_file():
        parameters_path = video_folder+"\parameters.txt"
    else:
        parameters_path = "null"
    print("Parametros: " + parameters_path)

    if parameters_path == "null":
        print("parameters.txt not accessible")
        start_time = 0
        end_time = VideoFileClip(args.videopath).duration
    else:
        parameters = open(parameters_path,"r").readlines()
        start_time = get_sec(parameters[4])
        end_time = get_sec(parameters[7])




else:
    print("ERROR")

if args.title:
    title = args.title
elif args.videopath:
    title = video_name
else:
    title = parameters[10]

def to_hms(time):
    s, f = divmod(int(float(time)*int(framerate)), int(framerate))
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return '{:0>2}:{:0>2}:{:0>2}:{:0>2}'.format(h, m, s, f)

def cut_index(i):
    num=i+1
    return f'{num:03d}'

def search_value(parameter_name, line):
    try:
        found=line.split(parameter_name+" ",1)[1]
        found=found.split(" ",1)[0]
    except AttributeError:
        print("VALUE ERROR")
        # AAA, ZZZ not found in the original string
        found = '' # apply your error handling
    return found


# CARGAMOS EL TEXTO
print("Loading FFMPEG Text...")
old_file = open("silences_raw.txt","r", encoding='utf-16')
lines = old_file.readlines()

silence_starts = []
silence_ends = []
raw_cuts_in = []
raw_cuts_out = []
cuts_duration = []
tl_cuts_in = []
tl_cuts_out = []

print("Analyzing FFMPEG Text...")
i = 1
for line in lines:
    #print(" Line "+str(i)+" of "+str(len(lines)))
    if "silence_start" in line:
        t = float(search_value("silence_start:", line))
        print("Start value "+str(i)+" found: "+str(t))
        silence_starts.append(t)
    if "silence_end" in line:
        t = float(search_value("silence_end:", line))
        print("End value "+str(i)+" found: "+str(t))
        silence_ends.append(t)
        t = float(search_value("silence_duration:", line))
        print("Duration value "+str(i)+" found: "+str(t))
    i += 1
print(str(len(silence_starts))+" silences found, ")

i = 0
while i < len(silence_starts):
    print("Checking silence start num "+str(i+1)+ " of "+str(len(silence_starts))+" ("+to_hms(silence_starts[i])+")")
    if silence_starts[i] <= start_time:
        print("Deleting it...")
        if silence_ends[i] > start_time:
            start_time = silence_ends[i]
            print("New Start Time: "+to_hms(start_time))
            runloop = True
        del silence_starts[i]
        del silence_ends[i]
        i = 0
    else:
        i += 1

i = 0
while i < len(silence_ends):
    print("Checking silence end num "+str(i+1)+ " of "+str(len(silence_ends))+" ("+to_hms(silence_ends[i])+")")
    if silence_ends[i] >= end_time:
        print("Deleting it...")
        if silence_starts[i] < end_time:
            end_time = silence_starts[i]
            print("New End Time: "+to_hms(end_time))
            runloop = True
        del silence_starts[i]
        del silence_ends[i]
        i = 0
    else:
        i += 1




new_file = open(args.videopath+".edl","w")
new_file.write("TITLE: "+title)
new_file.write("\n")
new_file.write("FCM: NON-DROP FRAME")

cut_offset = 0.5
#Calculating cuts
raw_cuts_in.append(start_time)
for i in range(len(silence_starts)):
    raw_cuts_in.append(silence_ends[i] - cut_offset if silence_ends[i] > cut_offset else 0)
    raw_cuts_out.append(silence_starts[i] + cut_offset)
raw_cuts_out.append(end_time)

for i in range(len(raw_cuts_in)):
    cuts_duration.append(raw_cuts_out[i]-raw_cuts_in[i])

accumulated_time = 0
for i in range(len(raw_cuts_in)):
    tl_cuts_in.append(accumulated_time)
    tl_cuts_out.append(accumulated_time + cuts_duration[i])
    accumulated_time += cuts_duration[i]

for i in range(len(raw_cuts_in)):
    new_file.write("\n")
    new_file.write("\n")
    new_file.write(cut_index(i)+"  AX       AA/V  C        "+to_hms(raw_cuts_in[i])+" "+to_hms(raw_cuts_out[i])+" "+to_hms(tl_cuts_in[i])+" "+to_hms(tl_cuts_out[i]))
    new_file.write("\n")
    new_file.write("* FROM CLIP NAME: " + video_name)
    print("Subclip "+cut_index(i)+" |  Start Time: "+to_hms(raw_cuts_in[i])+"   End Time: "+to_hms(raw_cuts_out[i]))




#new_file.write("\n")
#new_file.write(open("final.txt").read())
