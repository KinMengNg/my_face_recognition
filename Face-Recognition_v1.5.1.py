###Attendance system

import face_recognition
import os
import cv2
import pickle
import time
from PIL import Image
import shutil
import PySimpleGUI as psg
import pyttsx3
import random
import csv
import datetime
from imutils.video import WebcamVideoStream
import argparse
import imutils
from threading import Thread
from queue import Queue

print('Self learning Face Recognition with ID')
print('Version 1.5, Ng Kin Meng')
print('')

#function for text to speech
global engine
engine = pyttsx3.init()

global speech
speech = Queue()

def update(name):
    try:
        class_list.remove(name)
    except:
        pass
    present.append(name)    
    window.Element("names").Update(class_list, scroll_to_index=len(class_list))
    window.Element("present").Update(present, scroll_to_index=len(present))
    window.refresh()

def tts():

    while speech.qsize():
        text = speech.get()
        engine.say(text)
        engine.runAndWait()
        engine.endLoop()
        print(text)

#Function to resize the window to fit the screen
def ResizeWithAspectRatio(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)

# Returns (R, G, B) from name
def name_to_color(name):
    # Take 3 first letters, tolower()
    # lowercased character ord() value rage is 97 to 122, substract 97, multiply by 8
    color = [(ord(c.lower())-97)*8 for c in str(name)[:3]]
    return color


#i put in function so more robust, and less global variables, also cause i want to introduce some other stuff in future
def my_face_recognition():
    
    
    ENCODINGS_DIR = 'known_faces_encodings'
    UNKNOWN_FACES_DIR = 'test_folder'
    PIC_DIR = 'known_faces_pic'
    TOLERANCE = float(input("Please specify desired tolerance (0.0 < Tolerance < 1.0): "))
    #Scale will determine how fast this thing is, Scales the picture
    SCALE = int(input('''Please enter expected distance of camera from face
    [1, 2, 3 or 4; 1 being the furthest, and 4 being the closest]
    This will help optimize the speed of the program.
    Expected Distance: '''))

    FRAME_THICKNESS = 3
    FONT_THICKNESS = 2
    MODEL = 'cnn'  # default: 'hog', other one can be 'cnn' - CUDA accelerated (if available) deep-learning pretrained model

    #counter for tts, so not every round it says
    tts_counter = 0
    tts_lst = [] #temporary memory of the last n names

    
    
    #names of present people
    attendance = {}
    
    #To capture the video
    video = WebcamVideoStream(src=0).start()

##    #resize make it bigger
##    video.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
##    video.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    #nearly fullscreen NO DIFFERENCE
##    video.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)
##    video.set(cv2.CAP_PROP_FRAME_HEIGHT, 1440)
    

    print('Loading known faces...')
    known_faces = []    
    known_names = []

    # We oranize known faces as subfolders of ENCODINGS_DIR
    # Each subfolder's name becomes our label (name)
    for name in os.listdir(ENCODINGS_DIR):
        print(f'Starting with {name}!')

        # Next we load every file of faces of known person
        for filename in os.listdir(f"{ENCODINGS_DIR}/{name}"):
            print(f'Loading: {filename}')

            # Load an image
            #image = face_recognition.load_image_file("{}/{}/{}".format(ENCODINGS_DIR, name, filename))

            # Get 128-dimension face encoding
            # Always returns a list of found faces, for this purpose we take first face only (assuming one face per image as you can't be twice on one image)
            #encoding = face_recognition.face_encodings(image)[0]
            with open(f'{ENCODINGS_DIR}/{name}/{filename}', 'rb') as pkl_file:
                encoding = pickle.load(pkl_file)

                # Append encodings and name
                known_faces.append(encoding)
                known_names.append(name)
            
        print(f'Done with {str(name)}!')

    next_id = len(known_names) + 1


    print('Processing unknown faces...')

    copied_lst = []
    curr_time = time.time()
    while True:
        
        
        #To modify the tolerance and scale DURING the program, more for my debugging
        if cv2.waitKey(1) & 0xFF == ord('t'):
            TOLERANCE = float(input("Please specify new tolerance (0.0 < Tolerance < 1.0): "))

        if cv2.waitKey(1) & 0xFF == ord('d'):
            SCALE = int(input('''Please enter new distance of camera from face
    [1, 2, 3 or 4; 1 being the furthest, and 4 being the closest]
    New Distance: '''))
            
        #Load video
        image = video.read()

        window.refresh()
        
        if int(time.time()-curr_time) == 2:
            #Load video

            # Resize frame of video to 1/4 size for faster face recognition processing
            small_image = cv2.resize(image, (0, 0), fx=(1/SCALE), fy=(1/SCALE))

            # This time we first grab face locations - we'll need them to draw boxes
            locations = face_recognition.face_locations(small_image)#, model=MODEL)

            # Now since we know locations, we can pass them to face_encodings as second argument
            # Without that it will search for faces once again slowing down whole process
            encodings = face_recognition.face_encodings(small_image, locations)

            # We passed our image through face_locations and face_encodings, so we can modify it
            # First we need to convert it from RGB to BGR as we are going to work with cv2
            #image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # But this time we assume that there might be more faces in an image - we can find faces of dirrerent people
            print(f", found {len(encodings)} face(s)")


            for face_encoding, face_location in zip(encodings, locations):
                results = []
                if known_faces: #TO SKIP IF ITS EMPTY< CAUSE IF EMPTY IT CAUSESPROBLEM
                    # We use compare_faces (but might use face_distance as well)
                    # Returns array of True/False values in order of passed known_faces
                    results = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)

                # Since order is being preserved, we check if any face was found then grab index
                        # then label (name) of first matching known face withing a tolerance
                match = None
                break_flag = False #its actually a continue flag, but ya

                if True in results:  # If at least one is true, get a name of first of found labels
                    #modified_tol = TOLERANCE
                    #If there is more than one True, narrow the tolerence down
                    if results.count(True) > 1:
                        results = list(face_recognition.face_distance(known_faces, face_encoding)) #face_distance returns a numpy array
                        closest = min(results)
                        match = known_names[results.index(closest)] #the smallest distance gives closest face
                        print(f" - {match} from position {results.index(closest)}: {closest}")

                    else:
                        match = known_names[results.index(True)]
                        print(f" - {match} from {results}")

                    #either way, greet the match
                    if match not in tts_lst:
                        tts_lst.append(match)
                        sylables = str(match).replace('_', ' ', 10)
                        speech.put(f'Hello there! {str(sylables)}')
                        speech.put(random.choice(['Nice to meet you!', 'You look familiar.', 'How do you do?']))
                        update(sylables)

                        #if more than 6 names will remove the first name(refrshing temp memory)
                        if len(tts_lst) > 6:
                            tts_lst.pop(0)

                    if match in tts_lst:
                        tts_counter += 1
                        if tts_counter % 100 == 0: #every hundred loop
                            sylables = str(match).replace('_', ' ', 10)
                            speech.put(f'Ohh Hi! {str(sylables)}. You are still here.')

                    #Attendance part
                    try:
                        attendance[match]
                        with open('attendance.csv', 'a', newline='') as csvfile:
                            fields = [datetime.datetime.now().date(), datetime.datetime.now().time(), match]
                            csv.writer(csvfile).writerow(fields)
                        attendance[match] = None
                        print(f'Attendance recorded: {fields}')
                        speech.put('Attendance recorded.')
                    except:
                        pass
                    
                            
                            
                    
                else:
                    #Creates a new folder to store the unknown face, thus now known
                    match = str(next_id)
                    next_id += 1
                    known_names.append(match)
                    index = known_names.index(match) #so i know what index to change
                    known_faces.append(face_encoding)
                    os.mkdir(f'{ENCODINGS_DIR}/{match}')
                    timestamp = int(time.time())
                    with open(f'{ENCODINGS_DIR}/{match}/{match}-{timestamp}.pkl', 'wb') as pkl_file:
                        pickle.dump(face_encoding, pkl_file)

                    #i just created this so i know which id goes to who, i use pil cause idk how use cv2
                    os.mkdir(f'known_faces_pic/{match}_Pic')
                    #top, right, bottom, left = face_location

                    # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                    top = face_location[0] * SCALE
                    right = face_location[1] * SCALE
                    bottom = face_location[2] * SCALE
                    left = face_location[3] * SCALE

                    face_image = image[top:bottom, left:right]
                    pil_image = Image.fromarray(face_image)
                    image_file = f'known_faces_pic/{match}_Pic/{match}-{timestamp}.png'
                    pil_image.save(image_file) #IT NEEDS PNG FILE FORMAT TO WORK


                    #UPDATING THE DATABASE IMMEDIATELY
                    #greetunknown
                    t5 = Thread(target=tts, args=('Hello, who are you?',))
                    t5.start()

                    #Asking for input and showing the picture at the same time using pysimple gui
                    name = psg.popup_get_text(f"Who is ID {match}? Press ENTER to skip this ID, Press 'D' to Delete this ID: ", title = f'ID {match}', image = image_file)
                    
                    #Iterate through each encoding in the folder(the encoding is a pickle)
                    for encoding in os.listdir(f'{ENCODINGS_DIR}/{match}'): #just putting folder doesnt seem to work

                        #If ENTER
                        if name == '' or name == None:
                            continue

                        #If D
                        elif name == 'd' or name == 'D':
                            #input('1')
                            print(f'Deleting {match}')
                            shutil.rmtree(f'{ENCODINGS_DIR}/{match}')
                            print(f'Deleting {match}_Pic')
                            shutil.rmtree(f'{PIC_DIR}/{match}_Pic')
                        
                        #if the name already exist
                        else:
                            if name in os.listdir(ENCODINGS_DIR):
                                #so i know what to delete later
                                copied_lst.append(match)
                                #input('2')
                                
                                print(f'Copying {encoding} to {name}')
                                shutil.copy(f'{ENCODINGS_DIR}/{match}/{encoding}', f'{ENCODINGS_DIR}/{name}/{encoding}')
                                print(f'Copying {match}_Pic to {name}')
                                
                                #to remove .pkl extension
                                shutil.copy(f'{PIC_DIR}/{match}_Pic/{encoding[:-4]}.png', '{PIC_DIR}/{name}/{encoding[:-4]}.png')
                            
                            #if the name does not exist yet
                            else:
                                #input('3')
                                copied_lst.append(match)
                                os.mkdir(f'{ENCODINGS_DIR}/{name}')
                                os.mkdir(f'{PIC_DIR}/{name}')
                                print(f'Copying {encoding} to {name}')
                                shutil.copy(f'{ENCODINGS_DIR}/{match}/{encoding}', f'{ENCODINGS_DIR}/{name}/{encoding}')
                                print(f'Copying {match}_Pic to {name}')
                                
                                #to remove .pkl extension
                                shutil.copy(f'{PIC_DIR}/{match}_Pic/{encoding[:-4]}.png', f'{PIC_DIR}/{name}/{encoding[:-4]}.png')

                            known_names[index] = name
                            
                        print('Done!')


                        if match in copied_lst:
                            print(f'Deleting {match}')
                            shutil.rmtree(f'{ENCODINGS_DIR}/{match}')
                            print(f'Deleting {match}_Pic')
                            shutil.rmtree(f'{PIC_DIR}/{match}_Pic')
            

                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top = face_location[0] * SCALE
                right = face_location[1] * SCALE
                bottom = face_location[2] * SCALE
                left = face_location[3] * SCALE

                # Each location contains positions in order: top, right, bottom, left
                top_left = (left, top)
                bottom_right = (right, bottom)

                # Get color by name using our fancy function
                color = name_to_color(match)

                # Paint frame
                cv2.rectangle(image, top_left, bottom_right, color, FRAME_THICKNESS)

                # Now we need smaller, filled grame below for a name
                # This time we use bottom in both corners - to start from bottom and move 50 pixels down
                top_left = (left, bottom)
                bottom_right = (right, bottom + 22)

                # Paint frame
                cv2.rectangle(image, top_left, bottom_right, color, cv2.FILLED)

                # Wite a name
                cv2.putText(image, match, (left + 10, bottom + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), FONT_THICKNESS)

            
                Thread(target=tts).start()
                
            curr_time = time.time()

        """CHOOSE EITHER VIDEO OR IMAGE"""
        # Show photo
        #resize = ResizeWithAspectRatio(image, height=800) # Resize by width OR # Resize by height
        #cv2.imshow(filename, resize)
        #cv2.waitKey(0)
        #cv2.destroyWindow(filename)

        #Show video
        cv2.imshow('', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        


    ###ADDING 'ID_to_faces' here
    print('Copied:', copied_lst)
    


#runs it
filename = 'class_list.txt'
with open(filename, 'r') as f:
    class_list = list(set(i.strip().split(',')[1] for i in f))                    
    
psg.theme('DarkGrey4')
present = []
class_list = ['Amanda', 'Keiron', 'Neil', 'Max',
              'Chris', 'Bryan', 'Jeremiah', 'Jim',
              'Jonas', 'Janet', 'Claire', 'Jennifer',
              'Adam', 'Tom', 'William', 'Jack',
              'Ivan', 'Jane', 'Jill', 'John']
class_list.sort()

layout = [[psg.Listbox(values=present, size=(20,20), key="present", auto_size_text=True), psg.Listbox(values = class_list, size=(20,20), key="names", auto_size_text=True)]]
global window
window = psg.FlexForm("Borderless Window", size=(350, 375), resizable=True, no_titlebar=True, grab_anywhere=True)
window.Layout(layout).Finalize()
window.refresh()
#t.sleep()
my_face_recognition()




