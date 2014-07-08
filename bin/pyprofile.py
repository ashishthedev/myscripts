import subprocess
import sys
import pstats
import os
from Util.Misc import OpenFileForViewing

def main():
    if not sys.argv[1]:
        raise Exception("Syntax: pyprofile '<scriptName> <scriptargs>'")

    scriptName = str(sys.argv[1])
    TEMP_FILE="temp.out"
    subprocess.call("python -m cProfile -o " + TEMP_FILE + " -s time " + scriptName)

    FINAL_FILE = "profResultsCumulative" + scriptName.split()[0] + ".txt"
    with open(FINAL_FILE, "wb") as f:
        p = pstats.Stats(TEMP_FILE, stream=f)
        p.strip_dirs().sort_stats('cumulative').print_stats(550)

    FINAL_FILE = "profResultsTimeWise" + scriptName.split()[0] + ".txt"
    with open(FINAL_FILE, "wb") as f:
        p = pstats.Stats(TEMP_FILE, stream=f)
        p.strip_dirs().sort_stats('time').print_stats(550)
    os.remove(TEMP_FILE)
    OpenFileForViewing(FINAL_FILE)

if __name__ == '__main__':
    main()
