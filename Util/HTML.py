'''
File: HTML.py
Author: Ashish Anand
Description: A utility module to aid in generation of HTML.
Date: 25-Sept-2012

'''

from Util.Colors import MyColors
def Html(x):
    return "<HTML>" + str(x) + "</HTML>"


def Body(x):
    return "<BODY>" + str(x) + "</BODY>"


def Table(x):
    return "<TABLE>" + str(x) + "</TABLE>"


def UnderLine(x):
    return "<U>" + str(x) + "</U>"


def Big(x):
    return "<BIG>" + str(x) + "</BIG>"


def Bold(x):
    return "<B>" + str(x) + "</B>"


def White(x):
    return "<font color='#FFFFFF'>"+str(x)+"</font>"

def Black(x):
    return "<font color='#000000'>"+str(x)+"</font>"


def th(x):
    return "<th>" + str(x) + "</th>"


def tr(x):
    return "<tr>" + str(x) + "</tr>"


def td(x):
    return "<td>" + str(x) + "</td>"


def PastelOrangeText(x):
    return FontClr(x, MyColors["PASTEL_ORANGE"])


def FontClr(x, clr):
    return "<font color='{}'> {} </font>".format(clr, str(x))


def trWithPastelBlueBackground(x):
    return trWithThisBackground(x, clr=MyColors["PASTEL_BLUE"])


def trWithSolarizedGreyBackground(x):
    return trWithThisBackground(x, clr=MyColors["SOLARIZED_GREY"])


def trWithThisBackground(x, clr=MyColors["PASTEL_BLUE"]):
    return "<tr bgcolor={}> {} </tr>".format(clr, str(x))

def TableHeaderCol(fgClr, bgClr, dictHead):
    assert fgClr is not None, "Please provide a foreground/font color"
    assert bgClr is not None, "Please provide a background color"
    res = ""
    for eachKey, eachVal in dictHead.items():
        k=FontClr(eachKey, fgClr)
        res += """<tr><th bgcolor={bgcolor}>{key}</th>
        <td>{val}</td></tr>""".format(bgcolor=bgClr, key=k, val=eachVal)
    return res


def TableHeaderRow(fgClr, bgClr, *tags):
    assert fgClr is not None, "Please provide a foreground/font color"
    assert bgClr is not None, "Please provide a background color"
    res = ""
    for eachTag in tags:
        res += th(FontClr(eachTag, fgClr))
    return trWithThisBackground(res, bgClr)


def TableDataRow(fgClr, bgClr, *tds):
    res = ""
    for eachTableData in tds:
        res += td(FontClr(eachTableData, fgClr))
    return trWithThisBackground(res, bgClr)
