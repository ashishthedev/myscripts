RESULTING_FILE_NAME="Side2"
DESTINATION_DIR="b:\desktop\SplitSongs"
SOURCE_FILENAME="D:\\MUSIC\\TAPE003\\TRACK001.MP3"
START_TIME="00.08"
END_TIME="46.25"
EXE_PATH="b:\Tools\Mp3SplitterCommandLine\mp3splt.exe"
import subprocess

def main():
    arglist = [EXE_PATH, SOURCE_FILENAME, START_TIME, END_TIME, "-f", "-d", DESTINATION_DIR, "-o", RESULTING_FILE_NAME]
    if raw_input("About to split {1} from {2} to {3} and place at {8}. Proceed(y/n)".format(*arglist)) != 'y':
        return
    arglist = [EXE_PATH, SOURCE_FILENAME, START_TIME, END_TIME, "-f", "-d", DESTINATION_DIR, "-o", RESULTING_FILE_NAME]
    subprocess.call(arglist)
    raw_input("Press any key to continue")


if __name__ == '__main__':
    main()
