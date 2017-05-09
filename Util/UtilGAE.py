import sys
import os

gae_sdk_path = os.path.join(os.environ["ProgramFiles"], "Google", "google_appengine")
def FixSysPath():
    if gae_sdk_path not in sys.path:
        sys.path.insert(0, gae_sdk_path)
    #import dev_appserver
    #dev_appserver.fix_sys_path()
