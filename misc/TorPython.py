##################################################################
##
## To browse all pages of certain website by TOR
##
#################################################################
import urllib2

def logger(l):
    print(l)

def StartTorAndRegisterProxy():
    import stem.process
    tor_process = stem.process.launch_tor_with_config(
      config = {
        'ControlPort': '9151',
        'SocksPort': '9050',
        'SocksListenAddress': '127.0.0.1',
        'HashedControlPassword': '16:F0275C72E32D423860FB64BC27F51BA879EAC16729C31E31D3D183E6DA', #test
        'Log': [
          'NOTICE stdout',
          #'ERR file /tmp/tor_error_log',
        ],
      },
      tor_cmd = "B:\\Tools\\Tor\\App\\tor.exe",
      init_msg_handler = logger,
    )

    proxy = urllib2.ProxyHandler({'http': '127.0.0.1:8118'})
    opener = urllib2.build_opener(proxy)
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib2.install_opener(opener)
    return tor_process

def StopTor(tor_process):
    tor_process.kill()

def newIdentity():
    print("Requesting a new identity")
    from stem import Signal
    from stem.control import Controller
    from stem import CircStatus

    with Controller.from_port(port = 9151) as controller:
        controller.authenticate(password="test")
        controller.signal(Signal.NEWNYM)

        for circ in controller.get_circuits():
            if circ.status != CircStatus.BUILT:
              continue

            exit_fp, exit_nickname = circ.path[-1]

            exit_desc = controller.get_network_status(exit_fp, None)
            exit_address = exit_desc.address if exit_desc else 'unknown'

            print "Exit relay"
            print "  fingerprint: %s" % exit_fp
            print "  nickname: %s" % exit_nickname
            print "  address: %s" % exit_address
            print


        for circ in controller.get_circuits():
            if circ.status != CircStatus.BUILT:
              continue  # skip circuits that aren't yet usable

            entry_fingerprint = circ.path[0][0]
            entry_descriptor = controller.get_network_status(entry_fingerprint, None)

            if entry_descriptor:
              print "Circuit %s starts with %s" % (circ.id, entry_descriptor.address)
            else:
              print "Unable to determine the address belonging to circuit %s" % circ.id
    print("Got a new identity")


import argparse

def ParseArguments():
    p = argparse.ArgumentParser()
    p.add_argument("--url", dest='url', type=str, default=None, help="Url To Access")
    p.add_argument("-t", "--interval", dest='intervalInSecs', type=int, default=60, help="Interval between accesses")
    args = p.parse_args()
    return args

def main():
    args = ParseArguments()

    from time import sleep
    #PRIVOXY should be running with following configuration
    #    forward-socks5   /               127.0.0.1:9050 .
    #    forward-socks4   /               127.0.0.1:9050 .
    #whether its 9050 or 9150 depends upon how the tor is setup. Look at the tor's message log for socks port.
    # Tor should also be running preferably through vidalia
    #TODO: Check if it is running programatically

    #b:\Tools\PrivoxyInstalled\privoxy.exe
    #t for tor

    i = 10
    while i:
        try:
            tor_process = StartTorAndRegisterProxy()
            urllib2.urlopen(args.url)
            print("Sleeping for {} seconds".format(args.intervalInSecs))
            sleep(args.intervalInSecs)
            #newIdentity()
        finally:
            if tor_process:
                StopTor(tor_process)
                i-=1
    return


if __name__ == "__main__":
    main()
