#####################################################################
## Intent: Should be run when installing on a new box
## Date: 2013-10-14 Mon 12:44 PM
#####################################################################


import subprocess
import os
import shutil
def NormalizePathsSeparatedBy(paths, separator):
  newL = list()
  for eachP in paths.split(separator):
    absPath = Abspath(eachP)
    if absPath not in newL:
      newL.append(absPath)

  ret = separator.join(newL)
  print(paths)
  print("New normalized paths ==>")
  print(ret)
  print("_"*70)
  return ret

def AddThisToGlobalPath(currentPath, path):
  newPath = currentPath + ";" + path
  newPath = NormalizePathsSeparatedBy(newPath, ";")
  Setx("PATH", newPath)
  return newPath

def Setx(var, value):
  subprocess.call("""setx {} "{}" """.format(var, value))

def Abspath(path):
  return os.path.abspath(path)

def SetAPPDIREnvVariable():
  binDir = os.getcwd()
  appDir = Abspath(os.path.join(binDir, "..", "..", ".."))
  if raw_input("APPDIR=={} (y/n)".format(appDir)) != 'y':
    appDir = raw_input("Enter the appdirPath(Hint: parent of parent of pycrm.cfg)")
  Setx("APPDIR", appDir)
  return appDir

def main ():
    PYTHON_BASE_DIR = "B:\\python27\\"
    appDir = SetAPPDIREnvVariable()
    if not appDir:
      raise Exception("Could not set the environment variable APPDIR")

    currentPath = os.environ["PATH"]
    currentPath = AddThisToGlobalPath(currentPath, PYTHON_BASE_DIR)
    currentPath = AddThisToGlobalPath(currentPath, os.path.join(PYTHON_BASE_DIR, "Scripts"))
    currentPath = AddThisToGlobalPath(currentPath, os.path.join(appDir, "sdatdocs", "code", "bin"))
    homeDir = os.path.expanduser("~")
    shutil.copy(
        os.path.join(appDir, "sdatDocs", "code", "misc", "gitFiles", "gitconfigHome.txt"),
        os.path.join(homeDir, ".gitconfig")
    )
    shutil.copy(
        os.path.join(appDir, "sdatDocs", "code", "misc", "vimFiles", "_gvimrc sample place in Documents Folder"),
        os.path.join(homeDir, ".vimrc")
    )

if __name__ == "__main__":
  main()
