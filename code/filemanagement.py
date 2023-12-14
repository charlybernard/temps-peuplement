import os
import json

def read_file(filename, split_lines=False):
    file = open(filename, "r")
    file_content = file.read()
    if split_lines:
        file_content = file_content.split("\n")
    file.close()
    return file_content

def read_json_file(filename):
    file = open(filename)
    data = json.load(file)
    file.close()
    return data

def write_file(content,filename):
    file = open(filename, "w")
    file.write(content)
    file.close()

def create_folder_if_not_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def remove_folder_if_exists(folder):
    if os.path.exists(folder):
        remove_folder(folder)

def remove_folder(folder):
    for e in os.listdir(folder):
        abspath_e = os.path.join(folder, e)
        print(abspath_e)
        if os.path.isfile(abspath_e):
            remove_file_if_exists(abspath_e)
        elif os.path.isdir(abspath_e):
            remove_folder(e)
        else:
            print(e)

    os.rmdir(folder)
        
def remove_file_if_exists(filename):
    if os.path.exists(filename):
        os.remove(filename)