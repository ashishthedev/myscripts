###########################################################
## Intent: To run in a dir and remove certain strings from
## names of all the mp3 files that are stored beneath it.
##
## Name: Ashish Anand
##
## Date: 2013-05-06 Mon 05:41 PM
###########################################################

import os
TAG_LIST = ["Cool - guy",
        "cool guy",
        "{{a2zRg}}",
        "[]",
        "-",
        ]

def RemovebadWordsFrom(absolutePath):
    for w in TAG_LIST:
        if w.lower() in absolutePath.lower():
            x = absolutePath
            y = absolutePath.lower().replace(w.lower(), ' ')
            y = y.strip()
            os.rename(x, y)
            print("Renamed {} to {}".format(x, y))

def SanitizeDirs(path):
    for root, dirs, files in os.walk(path):
        for eachDir in dirs:
            for eachBadWord in TAG_LIST:
                if eachBadWord.lower() in eachDir.lower():
                    RemovebadWordsFrom(os.path.join(root, eachDir.lower()))
def SanitizeFiles(path):
    for root, dirs, files in os.walk(path):
        for eachFileName in files:
            if not eachFileName.endswith("mp3"): continue # If the file is not mp3 then ignore
            for eachBadWord in TAG_LIST:
                if eachBadWord.lower() in eachFileName.lower():
                    RemovebadWordsFrom(os.path.join(root, eachFileName.lower()))
def SanitizeMp3Name(path):
    SanitizeDirs(path)
    SanitizeFiles(path)

if __name__ == '__main__':
    SanitizeMp3Name(os.getcwd())
