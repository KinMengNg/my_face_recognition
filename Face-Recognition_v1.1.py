###Assigns new id to unknown faces

import face_recognition
import os
import cv2
import pickle
import time
from PIL import Image

print('Self learning Face Recognition with ID')
print('Version 1.1, Ng Kin Meng')
print('')

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

KNOWN_FACES_DIR = 'known_faces_encodings'
UNKNOWN_FACES_DIR = 'test_folder' 
TOLERANCE = float(input("Please specify desired tolerance (0.0 < Tolerance < 1.0): "))
#Scale will determine how fast this thing is, Scales the picture
SCALE = int(input('''Please enter expected distance of camera from face
[1, 2, 3 or 4; 1 being the furthest, and 4 being the closest]
This will help optimize the speed of the program.
Expected Distance: '''))

FRAME_THICKNESS = 3
FONT_THICKNESS = 2
MODEL = 'cnn'  # default: 'hog', other one can be 'cnn' - CUDA accelerated (if available) deep-learning pretrained model

#To capture the video
video = cv2.VideoCapture(0)

print('Loading known faces...')
known_faces = []
known_names = []

# We oranize known faces as subfolders of KNOWN_FACES_DIR
# Each subfolder's name becomes our label (name)
for name in os.listdir(KNOWN_FACES_DIR):
    print('Starting with ' + name + '!')

    # Next we load every file of faces of known person
    for filename in os.listdir("{}/{}".format(KNOWN_FACES_DIR,name)):
        print('Loading: ', filename)

        # Load an image
        #image = face_recognition.load_image_file("{}/{}/{}".format(KNOWN_FACES_DIR, name, filename))

        # Get 128-dimension face encoding
        # Always returns a list of found faces, for this purpose we take first face only (assuming one face per image as you can't be twice on one image)
        #encoding = face_recognition.face_encodings(image)[0]
        encoding = pickle.load(open('{}/{}/{}'.format(KNOWN_FACES_DIR, name, filename), 'rb'))

        # Append encodings and name
        known_faces.append(encoding)
        known_names.append(name)
        
    print('Done with ' + str(name) + '!')

if len(known_names) > 0:
    next_id = len(known_names) + 1

else:
    next_id = 1


print('Processing unknown faces...')

while True:
    """CHOOSE ONE ONLY, EITHER VIDEO OR IMAGE"""
    # Load image
    #print("Filename {}".format(filename), end='')
    #image = face_recognition.load_image_file("{}/{}".format(UNKNOWN_FACES_DIR, filename))

    #Load video
    ret, image = video.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_image = cv2.resize(image, (0, 0), fx=(1/SCALE), fy=(1/SCALE))

    # This time we first grab face locations - we'll need them to draw boxes
    locations = face_recognition.face_locations(small_image) #, model=MODEL)

    # Now since we know loctions, we can pass them to face_encodings as second argument
    # Without that it will search for faces once again slowing down whole process
    encodings = face_recognition.face_encodings(small_image, locations)

    # We passed our image through face_locations and face_encodings, so we can modify it
    # First we need to convert it from RGB to BGR as we are going to work with cv2
    #image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # But this time we assume that there might be more faces in an image - we can find faces of dirrerent people
    print(", found {} face(s)".format(len(encodings)))

    for face_encoding, face_location in zip(encodings, locations):
        results = []
        if known_faces != []: #TO SKIP IF ITS EMPTY< CAUSE IF EMPTY IT CAUSESPROBLEM
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
                match = known_names[results.index(min(results))] #the smallest distance gives closest face
                print(" - {} from position {}: {}, in {}".format(match, results.index(min(results)), min(results), results))

            else:
                match = known_names[results.index(True)]
                print(" - {} from {}".format(match, results))
        else:
            #Creates a new folder to store the unknown facve, thus now known
            match = str(next_id)
            next_id += 1
            known_names.append(match)
            known_faces.append(face_encoding)
            os.mkdir('{}/{}'.format(KNOWN_FACES_DIR, match))
            pkl_file = open('{}/{}/{}-{}.pkl'.format(KNOWN_FACES_DIR, match, match, int(time.time())), 'wb')
            pickle.dump(face_encoding, pkl_file)

            #i just created this so i know which id goes to who, i use pil cause idk how use cv2
            os.mkdir('known_faces_pic/{}_Pic'.format(match))
            #top, right, bottom, left = face_location

            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top = face_location[0] * SCALE
            right = face_location[1] * SCALE
            bottom = face_location[2] * SCALE
            left = face_location[3] * SCALE

            face_image = image[top:bottom, left:right]
            pil_image = Image.fromarray(face_image)
            pil_image.save('known_faces_pic/{}_Pic/{}-{}.jpg'.format(match, match, int(time.time())))

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

