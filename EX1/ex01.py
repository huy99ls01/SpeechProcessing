import librosa
import sounddevice as sd
import soundfile as sf
import sys
import argparse
import queue
import threading
import os

# Arguments
ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', required=True, help="Audio files output directory.")
ap.add_argument('-f', '--file', required=True, help="Input text file.")
ap.add_argument('-i', '--index', help="Index file for audio files")

args = ap.parse_args()

# Text file, paragraphs and sentences handling

txt_file = open(args.file, "r", encoding="utf8")
txt_content = txt_file.readlines()
txt_extracted_content = []

for extract in txt_content:
    # Split paragraphs at '.'
    sentences = extract.split('.')
    for s in sentences:
        s = s.strip()
        if s: # Take only non-empty strings
            txt_extracted_content.append("\"" + s.strip() + ".\"")

print("Extracted {} sentences.".format(len(txt_extracted_content)))

# Audio file output
OUTPUT_DIR = args.output
FILE_APPEND = "sentences"
FILE_EXT = ".wav"

print("Type in prefix for recording file_names: (Leave blank for default)")
print("Default is " + FILE_APPEND + "_#.wav")
new_append = input("Input: ")

if (new_append):
    FILE_APPEND = new_append
 
print("Outputting to " + OUTPUT_DIR + "/" + FILE_APPEND + "_#.wav\n")

# Controls
STOP_RECORD_CMD = "/s"
RECORD_CMD = "/r"

inputQueue = queue.Queue()

def read_kb_input(inputQueue):
    while True:
        input_str = input()
        inputQueue.put(input_str)

# Indexing functions
def writeIndex(file, sentence, file_name):
    file.write(file_name + "\n")
    file.write(sentence + "\n")

# Recording functions
SAMPLE_RATE = 22050
CHANNELS = 2

q = queue.Queue()

def callback( indata, frames, time, status):
    #This is called (from a separate thread) for each audio block.
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())

def record(file_name):
    try:
        #Open a new soundfile and attempt recording
        with sf.SoundFile(file_name, mode='x', samplerate=SAMPLE_RATE, channels=CHANNELS, subtype="PCM_24") as file:
            with sd.InputStream(samplerate=SAMPLE_RATE, device=sd.default.device, channels=CHANNELS, callback=callback):
                print("Recording ... ('{}' to stop recording)".format(STOP_RECORD_CMD))
            
                while True:
                    file.write(q.get())

                    if (inputQueue.qsize() > 0):
                        input_str = inputQueue.get()
                        if (input_str == STOP_RECORD_CMD):
                            break

                print("Saved to: {}\n".format(file_name))

    except Exception as e:
        print(e)

def mainRecording():
    inputThread = threading.Thread(target=read_kb_input, args=(inputQueue,), daemon=True)
    inputThread.start()

    index_file = None
    if args.index:
        index_file = open(os.path.join(OUTPUT_DIR, args.index), "w", encoding='utf-8')

    i = 0
    for s in txt_extracted_content:
        print("{}\n".format(s))
        file_name = OUTPUT_DIR + "/" + FILE_APPEND + "_{}".format(i) + FILE_EXT
        i += 1
        print("Output: " + file_name)
        input("Press any key to start recording.")
        record(file_name)
        if index_file is not None:
            writeIndex(index_file, s, file_name)

    if index_file is not None:
        index_file.close()

    return

mainRecording()
