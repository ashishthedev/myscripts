

import stem

def MyInitMsgHandler(lines):
    print(lines)

def main():

    import stem.process
    SLEEP_TIME = 5
    tor_process = stem.process.launch_tor_with_config(
      config = {
        'ControlPort': '9151',
        'SocksPort': '9050',
        'SocksListenAddress': '127.0.0.1',
        'HashedControlPassword': '16:F0275C72E32D423860FB64BC27F51BA879EAC16729C31E31D3D183E6DA',
        'Log': [
          'NOTICE stdout',
          #'ERR file /tmp/tor_error_log',
        ],
      },
      tor_cmd = "B:\\Tools\\Tor\\App\\tor.exe",
      init_msg_handler = MyInitMsgHandler,
    )

    print("sleeping")
    from time import sleep
    sleep(SLEEP_TIME)

    tor_process.kill()
    return

if __name__ == "__main__":
    main()








import StringIO
import socket
import urllib

import socks  # SocksiPy module
import stem.process

from stem.util import term

SOCKS_PORT = 7000

# Set socks proxy and wrap the urllib module

socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', SOCKS_PORT)
socket.socket = socks.socksocket

# Perform DNS resolution through the socket

def getaddrinfo(*args):
  return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]

socket.getaddrinfo = getaddrinfo


def query(url):
  """
  Uses urllib to fetch a site using SocksiPy for Tor over the SOCKS_PORT.
  """

  try:
    return urllib.urlopen(url).read()
  except:
    return "Unable to reach %s" % url


# Start an instance of tor configured to only exit through Russia. This prints
# tor's bootstrap information as it starts. Note that this likely will not
# work if you have another tor instance running.

def print_bootstrap_lines(line):
  if "Bootstrapped " in line:
    print term.format(line, term.Color.BLUE)


print term.format("Starting Tor:\n", term.Attr.BOLD)

tor_process = stem.process.launch_tor_with_config(
  config = {
    'SocksPort': str(SOCKS_PORT),
    'ExitNodes': '{ru}',
  },
  init_msg_handler = print_bootstrap_lines,
)

print term.format("\nChecking our endpoint:\n", term.Attr.BOLD)
print term.format(query("https://www.atagar.com/echo.php"), term.Color.BLUE)

tor_process.kill() 

