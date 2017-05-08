
"""
Tb
2017-Apr-28 Fri 03:31 PM
"""

import urllib, urllib2
import logging

ANANDS_ID = "-159201567"
ASHISH_ID = "281750744"

def SendMessage(chatID, message) :
    bToken = "243518155:AAHnQ8hv5dDpVIFUy4A3q0mUDj2A7rwHaLc"
    apiUrl = "https://api.telegram.org/bot" + bToken + "/SendMessage"
    params = urllib.urlencode({
        "chat_id": chatID,
        "text":message,
        })
    req = urllib2.Request(apiUrl, params)
    try:
        response = urllib2.urlopen(req)
        logging.info(message)
        return response.read()
    except Exception:
        pass

def SendToAshish(message):
    SendMessage(ASHISH_ID, message)

def SendToAnands(message):
    SendMessage(ANANDS_ID, message)

import argparse
def ParseOptions():
    parser = argparse.ArgumentParser()

    parser.add_argument("--anands", dest='sendToAnands', action="store_true", default=False,
        help="Send to ashish.")

    parser.add_argument("--ashish", dest='sendToAshish', action="store_true", default=False,
        help="Send to ashish.")

    parser.add_argument("--message", dest='message', type=str, default=None,
        help="Take new snapshot for docket")

    return parser.parse_args()


if __name__ == "__main__":
  args = ParseOptions()
  if not args.message:
      raise("Expected a message got nothing")

  if args.sendToAshish:
      SendToAshish(args.message)

  if args.sendToAnands:
      SendToAnands(args.message)
