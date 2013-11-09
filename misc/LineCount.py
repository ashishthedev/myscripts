'''
File: LineCount.py
Author: Ashish Anand
Description: A script to count lines written in python files
Date: 2012-10-04
'''

import argparse
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--ext", dest='ext', nargs="*", type=str, default=[".py"], help="List of extensions.")
    args = parser.parse_args()

    extensions = list(args.ext)
    print("Searching in :" + str(args.ext))
    i=0
    for dirPath, dirNames, fileNames in os.walk(os.curdir):
        for eachFile in fileNames:
            if os.path.splitext(eachFile)[1] in extensions:
                filePath = os.path.join(dirPath, eachFile)
                lines = LinesInFile(filePath)
                i += lines
                print(lines, str(filePath))
    print("_" * 60 + "\n{} lines".format(i))


def LinesInFile(filePath):
    with open(filePath, "r") as f:
        i=0
        for eachLine in f:
            i+=1
    return i

if __name__ == '__main__':
    main()
