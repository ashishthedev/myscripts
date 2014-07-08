'''
File: Ugc.py
Author: Ashish Anand
Description: To download all the net papers
Date: 2012-10-20 Sat 01:30 PM
'''

import sys
import os
import re
import urllib.request
from Util.Misc import OpenFileForViewing
from html.parser import HTMLParser

TIME_BETWEEN_FETCHES = 1
MY_PUNCTUATION_TO_DELETE = [',', '.', '\\t', '\\n', '\\r']

class LinkFetcher(HTMLParser):
    """A subclass of HTMLParser with sole purpose of returning links of a specific pattern."""
    def __init__(self, url, regexPattern, strict=False, fl=sys.stdout):
        super(LinkFetcher, self).__init__(self)
        self.strict = strict
        self.fl = fl
        self.tempData = ""
        self.url = url
        self.regexPattern = re.compile(regexPattern)
        self.anchorTextList = list()
        self.anchorLinkList = list()
        self.anchorRecoding = False  # By default we are not recording the anchor elements
        self.html_resp = str(urllib.request.urlopen(self.url).read())
        self.feed(self.html_resp)

    def GiveMeZippedLinks(self):
        zipped = zip(self.anchorLinkList, self.anchorTextList)
        return list(zipped)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for (att, val) in attrs:
                if att == "href":
                    if self.regexPattern.match(val):
                        self.anchorLinkList.append(val)
                        self.anchorRecoding = True  # Since anchors are not nested, we are using boolen values to detect them

    def handle_endtag(self, tag):
        if tag == 'a':
            if self.anchorRecoding:
                self.anchorTextList.append(self.tempData.strip())
                self.tempData = ""
                self.anchorRecoding = False

    def handle_data(self, data):
        if self.anchorRecoding:
            for eachChar in MY_PUNCTUATION_TO_DELETE:
                data = data.replace(eachChar, ' ')
                data = data.strip()
            self.tempData += str(data)


def ProcessOneWebsite(website):
    outputKnowledgeDir = os.path.join("B:\\Desktop","UGCPapers")
    os.makedirs(outputKnowledgeDir, exist_ok=True)
    monthYearPapaerLinks = GiveMeLinksofThisPatternFromThisPage(website, "http://ugcnetonline.in/question_papers.*php")
    for eachPaperLink, linkTest in monthYearPapaerLinks:
        print(eachPaperLink)

    #outputKnowledgeFilePath = os.path.join(outputKnowledgeDir, fileName)
    #OpenFileForViewing(outputKnowledgeFilePath)


def GiveMeLinksofThisPatternFromThisPage(homeUrl, regexPattern):
    """Parses the page and returns a list of urls conforming to pattern given as the argument"""
    parser = LinkFetcher(homeUrl, regexPattern)
    zippedLinks = parser.GiveMeZippedLinks()
    parser.close()
    return zippedLinks



if __name__ == '__main__':
    ProcessOneWebsite("http://www.ugcnetonline.in/previous_question_papers.php")
