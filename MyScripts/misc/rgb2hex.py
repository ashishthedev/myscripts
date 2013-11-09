'''
File: rgb2hex.py
Author: Ashish Anand
Description: Take red,green, blue value and show the hex equivalent
'''

from UtilConfig import GetAppDir
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("red", type = int, help="Red component of the color.")
    parser.add_argument("green", type = int, help="Red component of the color.")
    parser.add_argument("blue", type = int, help="Red component of the color.")
    parser.add_argument("desc", type = str, help="Some comment where this color is picked from")

    args = parser.parse_args()
    comment = args.desc
    r = "{:0>2X}".format(args.red)
    g = "{:0>2X}".format(args.green)
    b = "{:0>2X}".format(args.blue)
    hexStr = r+g+b
    suggestedColorName = args.desc.upper().replace(" ", "_")

    filePath = os.path.join(GetAppDir(), "FrequentFliers", "actions.txt")
    with open(filePath, "a") as f:
        f.write("\nColor: " + comment)
        f.write("\nR:{0}, G:{1}, B:{2}".format(args.red, args.green, args.blue))
        f.write("\n{}=\"#{}\"".format(suggestedColorName, hexStr.upper()))
        f.write("\n_________________________________________________________________________________")
        f.write("\n")


if __name__ == '__main__':
    main()
