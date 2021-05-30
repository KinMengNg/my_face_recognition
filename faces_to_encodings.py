###AJust to convert images to encondings, so i dont need to do it so many times
#saves alot of time

import face_recognition
import os
import cv2
import pickle
import time



KNOWN_FACES_DIR = 'known_faces'
UNKNOWN_FACES_DIR = 'unknown_faces' #"""UNCOMMENT FOR IMAGE"""
TOLERANCE = 0.5
FRAME_THICKNESS = 3
FONT_THICKNESS = 2
MODEL = 'cnn'  # default: 'hog', other one can be 'cnn' - CUDA accelerated (if available) deep-learning pretrained model


print('Processing known faces...')
known_faces = []
known_names = []

# We oranize known faces as subfolders of KNOWN_FACES_DIR
# Each subfolder's name becomes our label (name)
for name in os.listdir(KNOWN_FACES_DIR):
    print('Starting with ' + name + '!')
    os.mkdir('known_face_encodings/{}'.format(name))

    # Next we load every file of faces of known person
    for filename in os.listdir("{}/{}".format(KNOWN_FACES_DIR,name)):
        print('Loading: ', filename)

        # Load an image
        image = face_recognition.load_image_file("{}/{}/{}".format(KNOWN_FACES_DIR, name, filename))

        # Get 128-dimension face encoding
        # Always returns a list of found faces, for this purpose we take first face only (assuming one face per image as you can't be twice on one image)
        encoding = face_recognition.face_encodings(image)[0]


        #serialise the encoding
        print('Serialising the encoding')
        pkl_file = open('known_face_encodings/{}/{}-{}.pkl'.format(name, name, int(time.time())), 'wb')
        pickle.dump(encoding, pkl_file)
        print('Serialised: ' + str(filename))
        
    print('Done with ' + str(name) + '!')

