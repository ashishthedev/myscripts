'''
File: Download_Website.py
Author: Ashish Anand
Description: Downloads the website for local inspection
Date: 2013-06-28 Fri 02:04 PM
'''

import sys
import os
from time import sleep
import urllib2
import urllib
from Util.Misc import PrintInBox
from datetime import datetime
from urlparse import urljoin, urlparse

DOWNLOAD_DIR = os.path.join("B:\\Tools","Downloaded_Offline_Websites", datetime.today().strftime("%Y-%m-%d"))

headers={'User-agent' : 'Mozilla/5.0'}
headers={'User-agent' : 'ZakiraBot.96'}


def WriteForFile(dlDir, url, html):
    fileName = urllib.url2pathname(urlparse(url).path)
    if fileName in ["", "/", "\\"]: fileName = "root"

    while len(fileName) > 2 and fileName[0] == "\\":
        fileName = fileName[1:]

    if not fileName.endswith(".html"): fileName += ".html"

    fileName = urllib.quote(fileName)
    path = os.path.join(dlDir, fileName)
    with open(path, "w") as f:
        f.write(html)

    return



from HTMLParser import HTMLParser
class MyHTMLParser(HTMLParser):
    """A subclass of HTMLParser for proper parsing of pages."""
    def __init__(self, page, strict=False, fl=sys.stdout):
        HTMLParser.__init__(self)
        self.strict = strict
        self.fl = fl
        self.titleRecoding = 0
        self.bodyRecoding = 0
        self.page = page
        self.currentTag = ""
        PrintInBox(page.url, fl=self.fl)

    def handle_starttag(self, tag, attrs):
        #print("Encountered a start tag: " + tag + " and some attributes" + str(attrs), file=self.fl)
        self.currentTag = tag
        if tag.lower() == "img":
            for (key, val) in attrs:
                if key == "alt":
                    self.handle_data(val)

        if tag.lower() == 'a':
            for (att, val) in attrs:
                if att.lower() == "href":
                    self.page.kidPages.append(val)

        if tag.lower() == 'title':
            self.titleRecoding +=1

        if tag.lower() == 'body':
            self.bodyRecoding +=1

    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.titleRecoding -=1

        if tag.lower() == 'body':
            self.bodyRecoding -=1

    def handle_data(self, data):
        if self.titleRecoding:
            self.page.title += data

    def handle_charref(self, data):
        #print("Encountered some charref  :", data, file=self.fl)
        pass

    def handle_comment(self, data):
        #print("Encountered some comment :", data, file=self.fl)
        pass

    def handle_decl(self, data):
        #print("Encountered some declaration  :", data, file=self.fl)
        pass

    def handle_entityref(self, data):
        #print("Encountered some entityref  :", data, file=self.fl)
        pass

    def handle_startendtag(self, tag, attr):
        pass


class Page():
    """Represents a single page"""
    def __init__(self, url, fl=sys.stdout):
        self.url = url
        self.fl = fl
        self.kidPages = list()
        self.html = None
        self.title = ""

    def Parse(self):
        req = urllib2.Request(self.url, None, headers)
        self.html = urllib2.urlopen(req).read()

        html_parser = MyHTMLParser(self, fl=self.fl)
        html_parser.feed(self.html)
        html_parser.close()


class Crawler():
    """Crawler is the calm and composed, ever forgiving observer under whose guidance everything happens."""
    def __init__(self, cfg, fl=sys.stdout):
        self.dlDir = cfg.dlDir
        self.startingUrl = cfg.website
        self.alreadySeenUrls = list()
        self.yetToBeScannedUrls = list()
        self.yetToBeScannedUrls.append(self.startingUrl)
        self.timeInterval = cfg.timeInterval
        self.fl = fl

    def NewUrlSighted(self, url):
        #Stuff to be performed when a new url is sighted
        url = urllib.splittag(url)[0] #Remove the named anchor references after'#'

        if url.find(self.startingUrl) != -1: #The new url should contain the starting url. This is to prevent crawler save rest of the internet to the local hard drive.
            if url not in self.alreadySeenUrls and url not in self.yetToBeScannedUrls:
                #Scan only subdomain urls
                self.yetToBeScannedUrls.append(url)
                print("New Url Sighted:", url)

    def DoneWithUrl(self, url):
        #Stuff to be done when you are done with a url
        assert self.yetToBeScannedUrls.count(url) == 1, "A url has to be there in the list only once. Something goofed up. The url is present for " + str(self.yetToBeScannedUrls.count(url)) + " times"
        self.yetToBeScannedUrls.remove(url)

        assert self.alreadySeenUrls.count(url) == 0, "This url was already scanned. Seeing this url for second time"
        self.alreadySeenUrls.append(url)

    def CutLoose(self):
        while len(self.yetToBeScannedUrls) > 0 :
            eachUrl = self.yetToBeScannedUrls[0]
            res = "Scanning: " + eachUrl
            self.fl.write(res)
            sleep(self.timeInterval)
            try:
                page = Page(eachUrl, fl=self.fl)
                page.Parse()

                WriteForFile(self.dlDir, page.url, page.html)

                for eachKidUrl in page.kidPages:
                    self.NewUrlSighted(urljoin(eachUrl, eachKidUrl))
            except Exception as ex:
                PrintInBox(str(ex))

            finally:
                self.DoneWithUrl(eachUrl)

    def PrintState(self):
        res = "\nAlready seen urls:\n{}".format("\n".join(self.alreadySeenUrls))
        res += "\n\nYet to be scanned urls:\n{}".format("\n".join(self.yetToBeScannedUrls))
        PrintInBox(res)

def DownloadOneWebsite(cfg):
    cfg.dlDir = os.path.join(DOWNLOAD_DIR, urlparse(cfg.website).hostname)
    if not os.path.exists(cfg.dlDir):
        os.makedirs(cfg.dlDir)

    Crawler(cfg).CutLoose()

    import subprocess
    subprocess.call("{explorer} {fpath}".format(
        explorer = os.path.join(os.environ['windir'], "explorer.exe"),
        fpath=cfg.dlDir))


def ParseOptions():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--proxy", dest='proxy', action="store_true", required=False, default=False, help="Use proxy at localhost:9050")
    parser.add_argument("-w", "--website", dest='website', type=str, required=False, default=None, help="Website to be downloaded")
    parser.add_argument("-t", "--time", dest='timeInterval', type=int, required=False, default=5, help="Time interval between two consecutive requests")
    return parser.parse_args()

#Make sure Privoxy is running on 8118 and tor is running on 9050 and privoxy is forwarding socks4 and socks 5 to 9050
PROXY_URL = "127.0.0.1:8118"

def RegisterProxy():
    proxy_support = urllib2.ProxyHandler({"http":PROXY_URL})
    opener = urllib2.build_opener(proxy_support)
    urllib2.install_opener(opener)
    return

if __name__ == '__main__':
    cfg = ParseOptions()
    if cfg.proxy:
        PrintInBox("Using Proxy:{}".format(PROXY_URL))
        RegisterProxy()
    cfg.website = cfg.website or "http://localhost:8080/"
    DownloadOneWebsite(cfg)
