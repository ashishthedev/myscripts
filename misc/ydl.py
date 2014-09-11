###################################################################
## Intent: To download youtube videos
## Prerequisites: Python and youtube-dl should be present
## Youtube-dl is available from https://github.com/rg3/youtube-dl/
## Author: Ashish Anand
## Date: 2013-03-09 Sat 01:24 PM
###################################################################

import subprocess
import os
from datetime import datetime

MAX_RETIRES = 10
BASEPATH = "b:\\YoutubeVideosDownloaded"
_LOGFILE = os.path.join(BASEPATH, "YoutubeDLLog.txt")
_YTURLLIST = os.path.join(BASEPATH, "YoutubeURLsQueue.txt")

def SanitizeUrls():
    WriteUrlsToFile([url.strip() for url in GetUrlsFromFile() if len(url.strip()) > 0])

def GetUrlsFromFile():
    with open(_YTURLLIST) as fd:
        return [line.strip() for line in fd.readlines()]

def WriteUrlsToFile(urls):
    with open(_YTURLLIST, "w") as fd:
        fd.write("\n".join(urls))
    return

def HowManyUrlsLeft():
    return len(GetUrlsFromFile())

def AddUrlToFile(url):
    YLog("Adding {} to queue".format(url))
    urls = GetUrlsFromFile()
    urls.append(url.strip())
    WriteUrlsToFile(urls)
    return

def RemoveUrlFromList(url):
    YLog("Removing {} from queue".format(url))
    urls = GetUrlsFromFile()
    urls.remove(url.strip())
    WriteUrlsToFile(urls)
    return

def AnyMoreUrlsLeft():
    SanitizeUrls()
    urls = GetUrlsFromFile()
    if len(urls) > 0:
        return True
    else:
        return False

def GetNextUrl():
    assert AnyMoreUrlsLeft() == True
    return GetUrlsFromFile()[0]

def YLog(msg):
    res = "{}| {} \n".format(datetime.today().strftime("%A, %d-%b-%Y %I:%M%p "), msg)
    print(res);
    with open(_LOGFILE, "a") as fd:
        fd.write(res)

def YoutubeDownload(args, onlyAudio=False):
    if not os.path.exists(_YTURLLIST):
      YLog("%s doesnot exist. Nothing to download".format(_YTURLLIST))
      return
    with open(_LOGFILE, "w"):
      #Just create the blank file and exit
      pass

    # All urls (separated by new line) in current vim window will be downloaded
    audioFlag = ""
    if onlyAudio:
      audioFlag = "--extract-audio --audio-format mp3" #Not working
    else:
      audioFlag = "--keep-video"

    YLog("Execution Begins Now\n{}".format("_"*60))
    YLog("Total {} urls in queue".format(str(HowManyUrlsLeft())))

    while AnyMoreUrlsLeft():
      line = GetNextUrl()
      if line.strip().startswith("#"):
        RemoveUrlFromList(line)
        continue
      YLog("Downloading 1 of {}".format(str(HowManyUrlsLeft())))
      YDLPATH = os.path.join("B:\\", "Tools", "Youtubedl", "youtube-dl.exe")
      #http://en.wikipedia.org/wiki/YouTube#Quality_and_codecs
      QUALITY = "-f 18/22/82/83/85/84/133/134/135/136/137"
      playlistInfo = ""
      if line.find("playlist") != -1:
        playlistInfo = "%(playlist)s" + "-" + "_%(playlist_index)s_"
      FINAL_NAME_FORMAT = "-o " + os.path.join("B:\\", "YoutubeVideosDownloaded") + os.path.sep + playlistInfo + "%(title)s-%(id)s.%(ext)s"
      ydlParametersList = ["--restrict-filenames", "--continue", "--console-title", FINAL_NAME_FORMAT]

      flagsAndUrl = line.split()
      assert len(flagsAndUrl) > 0, "Why are we processing an empty line"
      if len(flagsAndUrl) == 1:
        newUrl = flagsAndUrl[0]
        flags = []
      else:
        newUrl = flagsAndUrl[-1] #Url is always the last.
        flags = flagsAndUrl[:-1]
        ydlParametersList.extend(flags)

      if args.rate:
        YLog("Setting the ratelimit to {}".format(args.rate))
        ydlParametersList.append("--rate-limit {}".format(args.rate))

      ydlParametersStr = " ".join(ydlParametersList)
      cmd = YDLPATH + " " + QUALITY + " " + audioFlag + " " + ydlParametersStr +  " " + newUrl
      YLog("Executing: {}".format(cmd))
      retries = 0
      while retries < MAX_RETIRES: # Retry for a couple of times if failed.
        if retries > 0:
          YLog("Retrying download for {}".format(newUrl))
        else:
          YLog("Fresh download in progress for {}".format(newUrl))
        result = subprocess.call(cmd)
        if result == 0 : # 0 means success
          #Success
          RemoveUrlFromList(newUrl)
          YLog("+++++++Download successful for {}".format(newUrl))
          break

        YLog("--------Download failed for {}".format(newUrl))
        retries += 1
        if retries == MAX_RETIRES:
          retries = 0
          if raw_input("The url:{} could not be downloaded in {} retries. You want to delete it?(y/n)".format(newUrl, MAX_RETIRES)).lower() == 'y':
            RemoveUrlFromList(newUrl)
            #Bailing out. This url is faulty and cannot be downloaded
            break
    YLog("Execution Ends Now\n{}".format("_"*60))
    return

def ParseArgs():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("-r", "--rate-limit", dest='rate', type=str, default=None, help="Rate limit")
    return p.parse_args()

def main():
    try:
        args = ParseArgs()
        YoutubeDownload(args)
    except Exception as ex:
        #import pdb; pdb.set_trace()
        print(str(ex))

if __name__ == '__main__':
    main()

