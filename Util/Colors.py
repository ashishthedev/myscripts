'''
File: Colors.py
Author: Ashish Anand
Description: This file contains helper dictonary for color codes in hex
'''

"""
SOLARIZED HEX     16/8 TERMCOL  XTERM/HEX   L*A*B      RGB         HSB
--------- ------- ---- -------  ----------- ---------- ----------- -----------
base03    #002b36  8/4 brblack  234 #1c1c1c 15 -12 -12   0  43  54 193 100  21
base02    #073642  0/4 black    235 #262626 20 -12 -12   7  54  66 192  90  26
base01    #586e75 10/7 brgreen  240 #585858 45 -07 -07  88 110 117 194  25  46
base00    #657b83 11/7 bryellow 241 #626262 50 -07 -07 101 123 131 195  23  51
base0     #839496 12/6 brblue   244 #808080 60 -06 -03 131 148 150 186  13  59
base1     #93a1a1 14/4 brcyan   245 #8a8a8a 65 -05 -02 147 161 161 180   9  63
base2     #eee8d5  7/7 white    254 #e4e4e4 92 -00  10 238 232 213  44  11  93
base3     #fdf6e3 15/7 brwhite  230 #ffffd7 97  00  10 253 246 227  44  10  99
yellow    #b58900  3/3 yellow   136 #af8700 60  10  65 181 137   0  45 100  71
orange    #cb4b16  9/3 brred    166 #d75f00 50  50  55 203  75  22  18  89  80
red       #dc322f  1/1 red      160 #d70000 50  65  45 220  50  47   1  79  86
magenta   #d33682  5/5 magenta  125 #af005f 50  65 -05 211  54 130 331  74  83
violet    #6c71c4 13/5 brmagenta 61 #5f5faf 50  15 -45 108 113 196 237  45  77
blue      #268bd2  4/4 blue      33 #0087ff 55 -10 -45  38 139 210 205  82  82
cyan      #2aa198  6/6 cyan      37 #00afaf 60 -35 -05  42 161 152 175  74  63
green     #859900  2/2 green     64 #5f8700 60 -20  65 133 153   0  68 100  60
"""
"""
http://ethanschoonover.com/solarized
"""
_Solarized = {

"base03"    :"#002b36",
"base02"    :"#073642",
"base01"    :"#586e75",
"base00"    :"#657b83",
"base0"     :"#839496",
"base1"     :"#93a1a1",
"base2"     :"#eee8d5",
"base3"     :"#fdf6e3",
"yellow"    :"#b58900",
"orange"    :"#cb4b16",
"red"       :"#dc322f",
"magenta"   :"#d33682",
"violet"    :"#6c71c4",
"blue"      :"#268bd2",
"cyan"      :"#2aa198",
"green"     :"#859900",
}

def GetSolarizedColor(name):
  if name in _Solarized:
    return _Solarized[name]
  raise Exception("{} not defined in solarized panel".format(name))

MyColors = {
    "GOOGLE_NEW_INBOX_BASE"         : "#737373",
    "GOOGLE_NEW_INBOX_FOREGROUND"   : "#F6F6Dc",
    "FACEBOOK_BLUE"                 : "#3b5998",
    "OAUTH_FLUROSCENT_GREEN"        : "#c8f417",
    "GMAIL_PASTEL_RED"              : "#D64937",
    "GMAIL_BLUE_SIGN_IN"            : "#4c8efa",
    "GOOGLE_SEARCH_BORDER_COLOR"    : "#3079ED",
    "GOOGLE_SEARCH_BACKGROUNDCOLOR" : "#4D90FE",
    "CONSOLE_BLUE"                  : "#183040",
    "WHITE"                         : "#FFFFFF",
    "BLACK"                         : "#000000",
    "PASTEL_BLUE"                   : "#6C7A95",
    "TRELLO_BLUE"                   : "#164b69",
    "SOLARIZED_BACKGROUND_BLUE"     : "#002B36",
    "SOLARIZED_GREY"                : "#838468",
    "PASTEL_ORANGE"                 : "#DD472F",
    "HEADER_EXCEL_BLUE"             : "#4F81BD",
    "HEADER_EXCEL_DBL_LIGHT_BLUE"   : "#DBEF51",
    "HEADER_EXCEL_LIGHT_BLUE"       : "#B8CCE4",
    "HEADER_EXCEL_PURPLE"           : "#8064A2",
    "ROW_EXCEL_GREY"                : "#D8D8D8",
    "ROW_EXCEL_PEACH"               : "#fde9d9",
    "GREY_GIT_SCM_TEXT"             : "#4E443C",
    "PASTEL_ORANGE_SACHAGRIEF"      : "#EB5F3A",
    "GOOGLE_TASKBAR_ICON_COLOR"     : "#4185F4",
    }
