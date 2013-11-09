

import os
import shutil
from UtilMisc import MakeSureDirExists

DESTINATION_DIR = "B:\\Desktop\\PickedFiles\\"
def main():
    desirable_extensions = [".jpg", ".png", ".tif", "jpeg", ".ico"]

    cwd = os.getcwd()
    if raw_input("About to scan {} and copy all desirable files in {}(y/n)".format(cwd, DESTINATION_DIR)) != 'y':
        print("Not doing anything")
        return

    allFiles = GetPathsOfAllFilesOfType(desirable_extensions, cwd)
    MakeSureDirExists(DESTINATION_DIR)
    for eachFile in allFiles:
        leafName = os.path.split(eachFile)[1]
        shutil.copy(eachFile, os.path.join(DESTINATION_DIR, leafName))




def GetPathsOfAllFilesOfType(desirable_extensions, directory):
    """It all starts here."""
    allFiles = list()
    for dirpath, dirnames, filenames in os.walk(directory):
        for eachFile in filenames:
            ext = os.path.splitext(eachFile)[1]
            if ext not in desirable_extensions: continue

            path = os.path.join(dirpath, eachFile)

            allFiles.append(path)

    return allFiles

if __name__ == '__main__':
    main()
