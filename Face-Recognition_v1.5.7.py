# added faster comparison (pop recognised faces)
# added clearing of encodings while program is running
# added input functionalities like clearing and saving images

import face_recognition, cv2
import os, sys, shutil
import pickle
from PIL import Image
import PySimpleGUI as psg
import pyttsx3, random, datetime, csv, pickle
from threading import Thread
from queue import Queue
from cvlib import detect_face
import ctypes

print('Self learning Face Recognition with ID')
print('Version 1.5.7, Ng Kin Meng, Ansel Kee\n')

#function for text to speech
global engine, run, speech, colors
if sys.platform == 'linux':
    engine = pyttsx3.init('dummy')
elif sys.platform == 'win32':
    engine = pyttsx3.init()
run = True
speech = Queue()
colors = {}

def class_attendance():
    global window, present, class_list
    with open('class_list.txt', 'r') as f:
        class_list = list(set(i.strip().split(',')[1] for i in f))

    psg.theme('DarkGrey4')
    present = []
    class_list.sort()
    layout = [[psg.Text('Present'+' '*28), psg.Text('Names')],
              [psg.Listbox(values=present, size=(20, 20), key="present", auto_size_text=True), psg.Listbox(values = class_list, size=(20,20), key="names", auto_size_text=True)]]
    window = psg.FlexForm("", size=(350, 375),layout=layout, resizable=True, no_titlebar=True, grab_anywhere=True).Finalize()
    window.refresh()
    return

class_attendance()
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
def update(name):
    global window, present
    try:
        class_list.remove(name)
    except:
        pass
    present.append(name)
    window.Element("names").Update(class_list, scroll_to_index=len(class_list))
    window.Element("present").Update(present, scroll_to_index=len(present))
    window.refresh()
    return

def tts():
    global run
    while speech.qsize():
        run = False
        engine.say(speech.get())
        engine.runAndWait()
    run = True
    return

def say(text):
    global run, speech
    speech.put(text)
    if run:
        Thread(target=tts).start()
    return

# Returns (R, G, B) from name
def name_to_color(name):
    # Take 3 first letters, tolower()
    # lowercased character ord() value rage is 97 to 122, substract 97, multiply by 8
    return [(ord(c.lower())-97)*8 for c in str(name)[:3]]


#i put in function so more robust, and less global variables, also cause i want to introduce some other stuff in future
def my_face_recognition():
    global run, speech
    global next_id, known_faces, known_names, encoding_storage, current_names, previous_names, attendance, previous_locations, previous_matches_index
    global ENCODINGS_DIR, PIC_DIR
    ENCODINGS_DIR = 'known_faces_encodings'
    PIC_DIR = 'known_faces_pic'
    record = False
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
    image = cv2.flip(video.read()[1], 1)
    
    user32 = ctypes.windll.user32
    screen_res = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    scale_width = screen_res[0] / image.shape[1]
    scale_height = screen_res[1] / image.shape[0]
    scale = min(scale_width, scale_height)
    
    print('Loading known faces...')
    known_faces, known_names = {}, []
    encoding_storage, current_names, previous_names = {}, [], []
    # oranize known faces as subfolders of ENCODINGS_DIR
    # Each subfolder's name becomes the label (name)
    for name in os.listdir(ENCODINGS_DIR):
        print(f'Starting with {name}!')
        known_faces[name] = []
        known_names.append(name)
        #load every file of faces of known person
        for filename in os.listdir(f"{ENCODINGS_DIR}/{name}"):
            print(f'Loading: {filename}')

            # Get 128-dimension face encoding
            # returns a list of found faces
            with open(f'{ENCODINGS_DIR}/{name}/{filename}', 'rb') as pkl_file:
                encoding = pickle.load(pkl_file)
                # Append encodings and name
                known_faces[name].append(encoding)
        print(f'Done with {str(name)}!')

    next_id = len(known_names) + 1
    attendance = dict.fromkeys(known_names, None)

    print('Processing unknown faces...')

    copied_lst = [] #lst to chek what i copied and deleted, just for referenceand debugging

    previous_locations = [] #locations of the topleft corner of faces from the previous image
    previous_matches_index = [] #index of matches from last iteration

    while True:
        try:
            #to put in the current TOP LEFT locations of the detected faces later, and also acts as a reset
            current_locations = [] # will consist of lists of [Left, Top]
            current_matches_index = [] #also acts as reset
            current_names = []

            #Load video and flip
            image = cv2.flip(video.read()[1], 1)
            # This grabs the face locations, need them to draw boxes
            locations = [(i[1], i[2], i[3], i[0]) for i in detect_face(image, enable_gpu=True)[0]]

            # assume that there might be more faces in an image - we can find faces of dirrerent people
            #so for each location
            for face_location in locations:
                results = []
                match = None

                #check for every location, if the location is close to a previous location
                top, left = face_location[0], face_location[3]
                counter = 0 #so i know the index
                found = False

                #print(previous_locations)
                # issue with wrong name is here
                for location in previous_locations: #if its empty itll just skip
                    #if the difference in pixels are less than 20, can assume its the same face
                    if abs(location[0] - left) < 20 and abs(location[1] - top) < 20:
                        #print('itwent in here')
                        match = known_names[previous_matches_index[counter]]
                        found = True
                        current_locations.append([left, top])
                        current_matches_index.append(previous_matches_index[counter])
                        if match not in current_names:
                            current_names.append(match)
                        if match not in encoding_storage.keys():
                            encoding_storage[match] = known_faces[match]
                            known_faces.pop(match)
                        # greet the match
                        if match not in tts_lst:
                            tts_lst.append(match)
                            sylables = str(match).replace('_', ' ')
                            print("proximity", sylables)
                            say(f'Hello there {str(sylables)}!')
                            say(random.choice(['Nice to meet you!', 'You look familiar.', 'How do you do?']))
                            update(sylables)
                            #if more than 6 names will remove the first name(refrshing temp memory)
                            if len(tts_lst) > 6:
                                tts_lst.pop(0)

                        if match in tts_lst:
                            tts_counter += 1
                            if tts_counter % 500 == 0: #every 500th loop
                                tts_counter = 0
                                sylables = str(match).replace('_', ' ')
                                sylables = sylables.replace('mr', 'mister')
                                say(f'Ohh Hi, {str(sylables)}. You are still here.')

                        if record: 
                            top, right, bottom, left = face_location
                            timestamp = int(datetime.datetime.utcnow().timestamp())
                            
                            with open(f'{ENCODINGS_DIR}/{match}/{match}-{timestamp}.pkl', 'wb') as pkl_file:
                                pickle.dump(face_encoding, pkl_file)
                                
                            face_image = image[top:bottom, left:right]
                            pil_image = Image.fromarray(face_image)
                            image_file = f'known_faces_pic/{match}/{match}-{timestamp}.png'
                            pil_image.save(image_file)
                        
                        break #since found already, break

                        #for now dont care abut confidence, maybe some other time confidence = face_recognition.face_distance(iinin)
                    else:
                        counter += 1

                for i in previous_names:
                    if i not in current_names and i in encoding_storage:
                        known_faces[i] = encoding_storage[i]
                        encoding_storage.pop(i)
                        known_names.append(known_names.pop(known_names.index(i)))
                        
                #if theres no proximity matches from the last frame, then must run the whole thing to check who is it
                if not found:
                   #face_dstance returns a confidence score,
                   #the lower the scorer the 'closer' the encoding is to the known encoding, thus higher confidence, vice versa
                    #encoding is the most time psending part, so only check when its necesarry
                    print("matching: ", known_faces.keys(), encoding_storage.keys())
                    face_encoding = face_recognition.face_encodings(image, [face_location])[0] #it returns a list, of 1 element, so i take the first
                    try: #incase results are 0, meaning a new run
                        results = [min(list(face_recognition.face_distance(faces, face_encoding))) for faces in known_faces.values()]
                        closest = min(results)
                    except:
                        closest = 1
                    print(closest)
                    if closest < TOLERANCE:
                        #print(list(zip(known_names, results)))
                        #Identify the match from known_names, which have the same length as results
                        #print("Compared:", list(zip(list(known_faces.keys()), results)))
                        match = list(known_faces.keys())[results.index(closest)]
                        print(match, results.index(closest), list(known_faces.keys()), list(known_faces.keys())[results.index(closest)])
                        #append the data of this location into the respective lists
                        current_locations.append([face_location[3], face_location[0]])
                        current_matches_index.append(results.index(closest))

                        # greet the match
                        if match not in tts_lst:
                            tts_lst.append(match)
                            #print(tts_lst)
                            sylables = str(match).replace('_', ' ')
                            sylables = sylables.replace('mr', 'mister')
                            print('saying', sylables)
                            say(f'Hello there! {str(sylables)}')
                            say(random.choice(['Nice to meet you!', 'You look familiar.', 'How do you do?']))
                            update(sylables)
                            #if more than 6 names will remove the first name(refrshing temp memory)
                            if len(tts_lst) > 6:
                                tts_lst.pop(0)

                        if match in tts_lst:
                            tts_counter += 1
                            if tts_counter % 500 == 0: #every 500th loop
                                tts_counter = 0
                                sylables = str(match).replace('_', ' '  )
                                say(f'Ohh Hi! {str(sylables)}. You are still here.')
                        
                        #Attendance part
                        try:
                            attendance[match]
                            with open('attendance.csv', 'a', newline='') as csvfile:
                                fields = [datetime.datetime.now().date(), datetime.datetime.now().time(), match]
                                csv.writer(csvfile).writerow(fields)
                            attendance.pop(match)
                            say('Attendance recorded.')
                        except:
                            pass

                    else:
                        #Creates a new folder to store the unknown face, thus now known
                        match = str(next_id)
                        next_id += 1
                        known_names.append(match)
                        index = known_names.index(match) #so i know what index to change
                        
                        try: #need this to prevent FileExistError
                          os.mkdir(f'{ENCODINGS_DIR}/{match}')
                        except:
                          pass
                        timestamp = int(datetime.datetime.utcnow().timestamp())
                        with open(f'{ENCODINGS_DIR}/{match}/{match}-{timestamp}.pkl', 'wb') as pkl_file:
                            pickle.dump(face_encoding, pkl_file)

                        os.mkdir(f'known_faces_pic/{match}_Pic')

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
                        attendance[name] = None
                        
                        if name in known_faces:
                            known_faces[name].append(face_encoding)
                        elif name in encoding_storage:
                            encoding_storage[name].append(face_encoding)
                        elif name and name not in 'dD':
                            known_faces[name] = [face_encoding]
                        print(name)
                        #Iterate through each encoding in the folder(the encoding is a pickle)
                        for encoding in os.listdir(f'{ENCODINGS_DIR}/{match}'): #just putting folder doesnt seem to work

                            #If ENTER or D
                            if name in ('', None, 'd', 'D'):
                                #just delete it , save alot of erros and trouble, regardless
                                shutil.rmtree(f'{ENCODINGS_DIR}/{match}')
                                shutil.rmtree(f'{PIC_DIR}/{match}_Pic')

                                #since i removed it, i should pop it out of the knwon_names and known_faces, which i just added earlier jn
                                known_names.pop()
                                next_pic -= 1

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
                                    copied_lst.append(match)
                                    os.mkdir(f'{ENCODINGS_DIR}/{name}')
                                    os.mkdir(f'{PIC_DIR}/{name}')
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

                # Wite a name
                cv2.putText(image, match, (left + 10, bottom + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), FONT_THICKNESS)


            #update previous
            previous_locations = current_locations
            previous_matches_index = current_matches_index
            previous_names = current_names
            #Show video
            window_width = int(image.shape[1] * scale)
            window_height = int(image.shape[0] * scale)
            cv2.namedWindow('', cv2.WINDOW_NORMAL)
            #resize the window according to the screen resolution
            cv2.resizeWindow('', window_width, window_height)
            cv2.imshow('', image)
            key = cv2.waitKey(1)
            if  key == ord('s'):
                print("saving")
                record = True
            elif key == ord('q'):
                video.release()
                cv2.destroyAllWindows()
                break
            elif key == ord('c'):
                clear()
        except Exception as e:
            print(repr(e))
            pass

def clear():
    global next_id, known_faces, known_names, encoding_storage, current_names, previous_names, attendance, previous_locations, previous_matches_index
    global ENCODINGS_DIR, PIC_DIR
    next_id = 0
    known_names, current_names, previous_names, previous_locations, previous_matches_index = [], [], [], [], []
    encoding_storage, known_faces, attendance = {}, {}, {}
    for i in os.listdir(ENCODINGS_DIR):
        shutil.rmtree(f'{ENCODINGS_DIR}/{i}')
        try:
            shutil.rmtree(f'{PIC_DIR}/{i}')
        except:
            shutil.rmtree(f'{PIC_DIR}/{i}_Pic')
    print('Cleared!')
    return
    
my_face_recognition()
