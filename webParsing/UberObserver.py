'''
File: UberObserver.py
Author: Ashish Anand
Description: Creates a tree of all the pages inside a domain
Date: 2012-10-15 Mon 01:20 PM
'''

import sys
import os
from time import sleep
import urllib2
from UtilMisc import PrintInBox, OpenFileForViewing
from collections import Counter
from datetime import datetime
from urlparse import urlparse, urljoin

MY_PUNCTUATION_TO_DELETE = [',', '.', '\\t', '\\n', '\\r']
IGNORE_WORDS_LIST_IN_LOWER_CASE = ['a', 'the', 'of', 'for', 'and', 'to', 'in', 'is', 'that', 'as']
headers={'User-agent' : 'Mozilla/5.0'}
headers={'User-agent' : 'ZakiraBot.96'}

from HTMLParser import HTMLParser
class MyHTMLParser(HTMLParser):
    """A subclass of HTMLParser for proper parsing of pages."""
    def __init__(self, bodyWordsDict, page, strict=False, fl=sys.stdout):
        HTMLParser.__init__(self)
        self.bodyWordsDict = bodyWordsDict
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
        if self.titleRecoding: self.page.title += data

        for eachChar in MY_PUNCTUATION_TO_DELETE:
            data = data.replace(eachChar, ' ')

        data = data.strip()
        if len(data) == 0: return

        self.fl.write("\n<{}>\n {}\n".format(self.currentTag, data))

        words = data.split()
        words = [x.lower() for x in words]
        d = self.bodyWordsDict
        for eachWord in words:
            if eachWord not in d:
                d[eachWord] = 1
            else:
                d[eachWord] += 1

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
    def __init__(self, url, bodyWordsDict, fl=sys.stdout):
        self.url = url
        self.fl = fl
        self.kidPages = list()
        self.html_resp = None
        self.bodyWordsDict = bodyWordsDict    # Key = wors, value = count
        self.title = ""

        html_parser = MyHTMLParser(self.bodyWordsDict, self, fl= self.fl)

        req = urllib2.Request(self.url, None, headers)
        html = urllib2.urlopen(req).read()
        html_parser.feed(html)
        html_parser.close()


class Crawler():
    """Crawler is the calm and composed, ever forgiving observer under whose guidance everything happens."""
    def __init__(self, startingUrl, fl=sys.stdout):
        self.startingUrl = startingUrl
        self.alreadySeenUrls = list()
        self.yetToBeScannedUrls = list()
        self.yetToBeScannedUrls.append(startingUrl)
        self.fl = fl

    def NewUrlSeen(self, url):
        #Stuff to be performed when a new url is sighted
        if url.find(self.startingUrl)!=-1:
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
        bodyWordsDict = Counter()
        for eachUrl in self.yetToBeScannedUrls:
            res = "Scanning: " + eachUrl
            self.fl.write(res)
            sleep(1)
            try:
                page = Page(eachUrl, bodyWordsDict, fl=self.fl)
                for eachKidUrl in page.kidPages:
                    self.NewUrlSeen(urljoin(eachUrl, eachKidUrl))
            except Exception as ex:
                PrintInBox(str(ex))
                raise ex

            finally:
                self.DoneWithUrl(eachUrl)


        self.fl.write("\n")
        PrintInBox("Most common words", fl=self.fl)

        for eachKey, count in bodyWordsDict.most_common(500):
            if eachKey not in IGNORE_WORDS_LIST_IN_LOWER_CASE:
                self.fl.write("{}:{}\n".format(eachKey, count))


def ProcessOneWebsite(website):

    fileName = urlparse(website).netloc + ".txt"

    outputKnowledgeDir = os.path.join("B:\\Desktop","WebsiteKeywords", datetime.today().strftime("%Y-%b-%d"))
    if not os.path.exists(outputKnowledgeDir):
        os.makedirs(outputKnowledgeDir)
    outputKnowledgeFilePath = os.path.join(outputKnowledgeDir, fileName)
    with open(outputKnowledgeFilePath, "w") as f:
        crawler = Crawler(website, fl=f)
        crawler.CutLoose()
    OpenFileForViewing(outputKnowledgeFilePath)

def ParseOptions():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-np", "--no-proxy", dest='noProxy', action="store_true", default=False, help="Do not use proxy at localhost:9050") #By default we will use proxy.
    return parser.parse_args()

#Make sure Privoxy is running on 8118 and tor is running on 9050 and privoxy is forwarding socks4 and socks 5 to 9050
PROXY_URL = "127.0.0.1:8118"

def RegisterProxy():
    proxy_support = urllib2.ProxyHandler({"http":PROXY_URL})
    opener = urllib2.build_opener(proxy_support)
    urllib2.install_opener(opener)
    return

if __name__ == '__main__':
    args = ParseOptions()
    if not args.noProxy:
        PrintInBox("Using Proxy:{}".format(PROXY_URL))
        RegisterProxy()
    ProcessOneWebsite("http://localhost:8080/contact-us.html")
