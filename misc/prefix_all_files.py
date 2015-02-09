#This files adds a prefix to all the files in current folder.
#Useful when different folders have to merged together into a master folder and still some grouping has to be maintained
#In that case run this file with prefix "1_", "2_" etc.
import sys
import os
import shutil
PREFIX = ""
def main():

  if not sys.argv[1]:
    raise Exception("Please provide a prefix")
  global PREFIX
  PREFIX = sys.argv[1]
  cwd = os.getcwd()
  for f in os.listdir(cwd):
    oldPath = os.path.join(cwd,f)
    newPath = os.path.join(cwd, PREFIX+ f)
    print(oldPath, "-->", newPath)
    shutil.move(oldPath, newPath)


if __name__ == "__main__":
  main()
