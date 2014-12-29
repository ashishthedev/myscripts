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

    cumulativeFile = "profResultsCumulative" + scriptName.split()[0] + ".txt"
    with open(cumulativeFile, "wb") as f:
        p = pstats.Stats(TEMP_FILE, stream=f)
        p.strip_dirs().sort_stats('cumulative').print_stats(550)

    timeSortedFile = "profResultsTimeWise" + scriptName.split()[0] + ".txt"
    with open(timeSortedFile, "wb") as f:
        p = pstats.Stats(TEMP_FILE, stream=f)
        p.strip_dirs().sort_stats('time').print_stats(550)

    os.remove(TEMP_FILE)
    OpenFileForViewing(cumulativeFile)
    OpenFileForViewing(timeSortedFile)
    return

if __name__ == '__main__':
    main()
