'''
File: testParser.py
Author: Ashish Anand
Description: A file to test various functionality of HTML parser.
To check where will a tag land and how will it be handled when feed with html.
Date: 2012-10-18 Thu 12:42 PM
'''
from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print("handle_starttag:", tag)
        if tag.lower() == "img":
            for (key, val) in attrs:
                if key == "alt":
                    print("Img Alt: ", val)
                if key == "src":
                    print("Img Src: ", val)
    def handle_endtag(self, tag):
        print("handle_endtag  :", tag)
    def handle_data(self, data):
        print("handle_data    :", data)

p = MyHTMLParser(strict=False)
p.feed("""
<a target="_blank" href="http://ugcnetonline.in/question_papers_june2012.php"> <font style="font-size: 15pt" color="#0035EC">Question Papers of NET 
          June 2012</font></a>
          """)
p.close()
input("...")
