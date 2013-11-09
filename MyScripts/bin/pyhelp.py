import os
import subprocess

PYTHON_BASE_DIR = "B:\\Python27"
PYTHON_DOC_DIR = os.path.join(PYTHON_BASE_DIR, "Doc")

def main():
    listOfFiles = os.listdir(PYTHON_DOC_DIR)
    for flName in listOfFiles:
        if os.path.splitext(flName)[1].lower() == ".chm":
            subprocess.call("explorer {}".format(os.path.join(PYTHON_DOC_DIR, flName)))

if __name__ == "__main__":
    main()
