import subprocess
import os
from os.path import normpath

SOURCE_FILENAME = normpath("C:\Users\Ichigo\Desktop\O\TAPE007\\TRACK001.MP3")
START_TIME="43.14"
RESULTING_FILE_NAME="Hum sub milke aiye data tere darbar"
END_TIME="46.43"

DESTINATION_DIR = normpath("b:\\desktop\\SplitSongs")
EXE_PATH= normpath("b:\Tools\Mp3SplitterCommandLine\mp3splt.exe")
def main():
    if not os.path.exists(DESTINATION_DIR):
        os.makedirs(DESTINATION_DIR)

    if not os.path.exists(SOURCE_FILENAME):
        raise Exception("{} doesnot exist. Please correct the path in {}".format(SOURCE_FILENAME, __fil__))

    if os.path.exists(os.path.join(DESTINATION_DIR, RESULTING_FILE_NAME+".mp3")):
        if raw_input("{} already exist. Overwrite(y/n)?".format(RESULTING_FILE_NAME)) != "y":
            return

    arglist = [EXE_PATH, SOURCE_FILENAME, START_TIME, END_TIME, "-f", "-d", DESTINATION_DIR, "-o", RESULTING_FILE_NAME]
    if raw_input("About to split {1} from {2} to {3} and place at {8}. Proceed(y/n)".format(*arglist)) != 'y':
        return

    subprocess.call(arglist)
    raw_input("Press any key to continue")
    subprocess.call("explorer.exe {}".format(DESTINATION_DIR))


if __name__ == '__main__':
    main()
