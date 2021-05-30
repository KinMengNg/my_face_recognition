#To automate sorting the ids to their names

import shutil
import os

ENCODINGS_DIR = 'known_faces_encodings'
PIC_DIR = 'known_faces_pic'
copied_lst = []
for folder in os.listdir(ENCODINGS_DIR):
    #if its first character is a number,its an id(unassigned name)
    if folder[0].isnumeric():
        name = input("Who's face does ID {} belong to? Press ENTER to skip this ID: ".format(folder))
        #Iterate through each encoding in the folder(the encoding is a pickle)
        for encoding in os.listdir('{}/{}'.format(ENCODINGS_DIR, folder)): #just putting folder doesnt seem to work

            #If ENTER
            if name == '':
                continue
            
            #if the name already exist
            elif name in os.listdir(ENCODINGS_DIR):
                #so i know what to delete later
                copied_lst.append(folder)
                
                print('Copying {} to {}'.format(encoding, name))
                shutil.copy('{}/{}/{}'.format(ENCODINGS_DIR, folder, encoding), '{}/{}/{}'.format(ENCODINGS_DIR, name, encoding))
                print('Copying {}_Pic to {}'.format(folder, name))
                                                                #to remove .pkl extension
                shutil.copy('{}/{}_Pic/{}.jpg'.format(PIC_DIR, folder, encoding[:-4]), '{}/{}/{}.jpg'.format(PIC_DIR, name, encoding[:-4]))
            #if the name does not exist yet
            else:
                copied_lst.append(folder)
                os.mkdir('{}/{}'.format(ENCODINGS_DIR, name))
                os.mkdir('{}/{}'.format(PIC_DIR, name))
                print('Copying {} to {}'.format(encoding, name))
                shutil.copy('{}/{}/{}'.format(ENCODINGS_DIR, folder, encoding), '{}/{}/{}'.format(ENCODINGS_DIR, name, encoding))
                print('Copying {}_Pic to {}'.format(folder, name))
                                                                #to remove .pkl extension
                shutil.copy('{}/{}_Pic/{}.jpg'.format(PIC_DIR, folder, encoding[:-4]), '{}/{}/{}.jpg'.format(PIC_DIR, name, encoding[:-4]))

            print('Done!')

flag = input('Do you wish to delete the original folders of the copied IDs? [y/n]')

if flag == 'y' or flag == 'Y':
    for folder in os.listdir(ENCODINGS_DIR):
        
        if folder in copied_lst:
            print('Deleting {}'.format(folder))
            shutil.rmtree('{}/{}'.format(ENCODINGS_DIR, folder))
            print('Deleting {}_Pic'.format(folder))
            shutil.rmtree('{}/{}_Pic'.format(PIC_DIR, folder))
    print('Done!')

elif flag == 'n' or flag == 'N':
    print('Deletion skipped.')

else:
    print("That was neither 'y' or 'n', Deletion skipped.")
    
                
