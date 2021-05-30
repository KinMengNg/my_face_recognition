###FOR BUILDING BLOCS
#No attendance
#added comparing differencee between pixel
#fixed tts

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
from threading import Thread
from queue import Queue
from cvlib import detect_face

print('Self learning Face Recognition with ID')
print('Version 1.5, Ng Kin Meng, Ansel Kee')
print('')

#function for text to speech
global engine
engine = pyttsx3.init()

global run
run = True

global speech
speech = Queue()

global colors
colors = {}

def tts(text):
    global run
    run = False
    engine.say(text)
    engine.runAndWait()
    while speech.qsize():
        run = False
        engine.say(speech.get())
        engine.runAndWait()
    run = True
    return

def say(text):
    global run, speech
    if run:
        Thread(target=tts, args=(text,)).start()
        pass
    else:
        speech.put(text)
    return

# Returns (R, G, B) from name
def name_to_color(name):
    # Take 3 first letters, tolower()
    # lowercased character ord() value rage is 97 to 122, substract 97, multiply by 8
    color = [(ord(c.lower())-97)*8 for c in str(name)[:3]]
    return color


#i put in function so more robust, and less global variables, also cause i want to introduce some other stuff in future
def my_face_recognition():
    global run, speech
    ENCODINGS_DIR = 'known_faces_encodings'
    PIC_DIR = 'known_faces_pic'

    while True:        
        try:
            TOLERANCE = float(input("Please specify desired tolerance (0.0 < Tolerance < 1.0): "))
            break
        except:
            continue        
    
    FRAME_THICKNESS = 3
    FONT_THICKNESS = 2
    MODEL = 'yolov3'

    #counter for tts, so not every round it says
    tts_counter = 0
    tts_lst = [] #temporary memory of the last n names

    #To capture the video
    video = cv2.VideoCapture(0)

    print('Loading known faces...')
    known_faces = []
    known_names = []

    # oranize known faces as subfolders of ENCODINGS_DIR
    # Each subfolder's name becomes the label (name)
    for name in os.listdir(ENCODINGS_DIR):
        print(f'Starting with {name}!')

        #load every file of faces of known person
        for filename in os.listdir(f"{ENCODINGS_DIR}/{name}"):
            print(f'Loading: {filename}')

            # Get 128-dimension face encoding
            # returns a list of found faces
            with open(f'{ENCODINGS_DIR}/{name}/{filename}', 'rb') as pkl_file:
                encoding = pickle.load(pkl_file)
                # Append encodings and name
                known_faces.append(encoding)
                known_names.append(name)
        print(f'Done with {str(name)}!')

    next_id = len(known_names) + 1


    print('Processing unknown faces...')

    copied_lst = [] #lst to chek what i copied and deleted, just for referenceand debugging

    previous_locations = [] #locations of the topleft corner of faces from the previous image
    previous_matches_index = [] #index of matches from last iteration
    
    #curr_time = time.time()
    while True:
        try:
            #print(time.time() - curr_time)
            #curr_time = time.time()
            #to put in the current TOP LEFT locations of the detected faces later, and also acts as a reset
            current_locations = [] # will consist of lists of [Left, Top]
            current_matches_index = [] #also acts as reset
            
            
            #Load video and flip
            image = cv2.flip(video.read()[1], 1)

            # This grabs the face locations, need them to draw boxes
            locations = [(i[1], i[2], i[3], i[0]) for i in detect_face(image)[0]]
                        #top, right, bottom, left 
            
            # Now since we know locations, we can pass them to face_encodings
            # Without that it will search for faces once again slowing down whole process
            #encodings = face_recognition.face_encodings(image, locations)

            # assume that there might be more faces in an image - we can find faces of dirrerent people
            #print(f", found {len(encodings)} face(s)")
            #so for each encoding at each location
            for face_location in locations:
                results = []
                match = None

                #check for every location, if the location is close to a previous location
                top, left = face_location[0], face_location[3]
                counter = 0 #so i know the index
                found_flag = False

                #print(previous_locations)
                
                for location in previous_locations: #if its empty itll just skip
                    #if the difference in pixels are less than 20, can assume its the same face
                    if abs(location[0] - left) < 20 and abs(location[1] - top) < 20:
                        #print('itwent in here')
                        match = known_names[previous_matches_index[counter]]
                        found_flag = True
                        current_locations.append([left, top])
                        current_matches_index.append(previous_matches_index[counter])

                        # greet the match
                        if match not in tts_lst:
                            tts_lst.append(match)
                            sylables = str(match).replace('_', ' ', 10)
                            say(f'Hello there! {str(sylables)}')
                            say(random.choice(['Nice to meet you!', 'You look familiar.', 'How do you do?']))
                            
                            #if more than 6 names will remove the first name(refrshing temp memory)
                            if len(tts_lst) > 6:
                                tts_lst.pop(0)

                        if match in tts_lst:
                            tts_counter += 1
                            if tts_counter % 500 == 0: #every 500th loop
                                tts_counter = 0
                                sylables = str(match).replace('_', ' ', 10)
                                say(f'Ohh Hi, {str(sylables)}. You are still here.')

                                
                        break #since found already, break
                    
                        #for now dont care abut confidence, maybe some other time confidence = face_recognition.face_distance(iinin)
                    else:
                        counter += 1
                     

                #if theres no proximity matches from the last frame, then must run the whole thing to check who is it
                if found_flag == False:
                   #face_dstance returns a confidence score,
                   #the lower the scorer the 'closer' the encoding is to the known encoding, thus higher confidence, vice versa
                    #encoding is the most time psending part, so only check when its necesarry
                    face_encoding = (face_recognition.face_encodings(image, [face_location]))[0] #it returns a list, of 1 element, so i take the first
                    #print(face_encoding)
                    for i in list(face_recognition.face_distance(known_faces, face_encoding)): # returns confidence
                        if i not in results: #prevent duplicates(for some reason theres occasionally duplicates due to zip i think)
                            results.append(i)
                    try: #incase results are 0, meaning a new run
                        closest = min(results)
                    except:
                        closest = 1


                    if closest < TOLERANCE:
                        #print(list(zip(known_names, results)))
                        #Identify the match from known_names, which have the same length as results
                        match = known_names[results.index(closest)]

                        #append the data of this location into the respective lists
                        current_locations.append([face_location[3], face_location[0]])
                        current_matches_index.append(results.index(closest))
                        

                        # greet the match
                        if match not in tts_lst:
                            tts_lst.append(match)
                            #print(tts_lst)
                            sylables = str(match).replace('_', ' ', 10)
                            say(f'Hello there! {str(sylables)}')
                            say(random.choice(['Nice to meet you!', 'You look familiar.', 'How do you do?']))
                            
                            #if more than 6 names will remove the first name(refrshing temp memory)
                            if len(tts_lst) > 6:
                                tts_lst.pop(0)

                        if match in tts_lst:
                            tts_counter += 1
                            if tts_counter % 500 == 0: #every 500th loop
                                tts_counter = 0
                                sylables = str(match).replace('_', ' ', 10)
                                say(f'Ohh Hi! {str(sylables)}. You are still here.')

                    else:
                        #Creates a new folder to store the unknown face, thus now known

                        match = str(next_id)
                        next_id += 1
                        known_names.append(match)
                        index = known_names.index(match) #so i know what index to change
                        known_faces.append(face_encoding)
                        try: #need this to prevent FileExistError
                          os.mkdir(f'{ENCODINGS_DIR}/{match}')
                        except:
                          pass
                        timestamp = int(time.time())
                        with open(f'{ENCODINGS_DIR}/{match}/{match}-{timestamp}.pkl', 'wb') as pkl_file:
                            pickle.dump(face_encoding, pkl_file)

                        #i just created this so i know which id goes to who, i use pil cause idk how use cv2
                        try: #Same
                          os.mkdir(f'known_faces_pic/{match}_Pic')
                        except:
                          pass

                        top, right, bottom, left = face_location

                        face_image = image[top:bottom, left:right]
                        pil_image = Image.fromarray(face_image)
                        image_file = f'known_faces_pic/{match}_Pic/{match}-{timestamp}.png'
                        pil_image.save(image_file) #IT NEEDS PNG FILE FORMAT TO WORK


                        #UPDATING THE DATABASE IMMEDIATELY
                        #greetunknown
                        say('Hello, who are you?',)

                        #Asking for input and showing the picture at the same time using pysimple gui
                        name = psg.popup_get_text(f"Who is ID {match}? Press ENTER to skip this ID, Press 'D' to Delete this ID: ", title = f'ID {match}', image = image_file)

                        #Iterate through each encoding in the folder(the encoding is a pickle)
                        for encoding in os.listdir(f'{ENCODINGS_DIR}/{match}'): #just putting folder doesnt seem to work

                            #If ENTER or D
                            if name == '' or name == None or name == 'd' or name == 'D':
                                #just delete it , save alot of erros and trouble, regardless
                                shutil.rmtree(f'{ENCODINGS_DIR}/{match}')
                                shutil.rmtree(f'{PIC_DIR}/{match}_Pic')

                                #since i removed it, i should pop it out of the knwon_names and known_faces, which i just added earlier jn
                                known_names.pop()
                                known_faces.pop()

                            #if a name was actually inputed
                            else:
                                #if its an existing name
                                if name in os.listdir(ENCODINGS_DIR):
                                    #so i know what to delete later
                                    copied_lst.append(match)

                                    shutil.copy(f'{ENCODINGS_DIR}/{match}/{encoding}', f'{ENCODINGS_DIR}/{name}/{encoding}')

                                    #to remove .pkl extension
                                    shutil.copy(f'{PIC_DIR}/{match}_Pic/{encoding[:-4]}.png', f'{PIC_DIR}/{name}/{encoding[:-4]}.png')

                                #if the name does not exist yet
                                else:
                                    #input('3')
                                    copied_lst.append(match)
                                    try:
                                        os.mkdir(f'{ENCODINGS_DIR}/{name}')
                                    except:
                                        print("encoding")
                                    try:
                                        os.mkdir(f'{PIC_DIR}/{name}')
                                    except:
                                        print('pic')
                                    shutil.copy(f'{ENCODINGS_DIR}/{match}/{encoding}', f'{ENCODINGS_DIR}/{name}/{encoding}')

                                    #to remove .pkl extension
                                    shutil.copy(f'{PIC_DIR}/{match}_Pic/{encoding[:-4]}.png', f'{PIC_DIR}/{name}/{encoding[:-4]}.png')

                                known_names[index] = name
                                
                                #same thing
                                current_locations.append([face_location[3], face_location[0]])
                                current_matches_index.append(index)

                            print('Done!')


                            if match in copied_lst:
                                shutil.rmtree(f'{ENCODINGS_DIR}/{match}')
                                shutil.rmtree(f'{PIC_DIR}/{match}_Pic')


                        

                # Scale back up face locations since the frame we detected in was scaled to 1/SCALE size
                top, right, bottom, left = face_location

                # Get color by name using sentdex fancy function
                try:
                    color = colors[match]
                except:
                    color = name_to_color(match)
                    colors[match] = color

                # Paint frame
                cv2.rectangle(image, (left, top), (right, bottom), color, FRAME_THICKNESS)
                cv2.rectangle(image, (left, bottom), (right, bottom+22), color, cv2.FILLED)

                # Write a name
                cv2.putText(image, match, (left + 10, bottom + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), FONT_THICKNESS)


            #update previous
            previous_locations = current_locations
            previous_matches_index = current_matches_index
            
            #Show video
            cv2.imshow('', image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except:
            pass

my_face_recognition()
