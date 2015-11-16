#!/usr/bin/env python3

import os
import test_td

# random hash
CONTEXT = None

# lxc container
SERVER = None
CLIENT = None

# pids of tunneldigger client and server
SERVER_PID = None
CLIENT_PID = None

def setup_module():
    CONTEXT = test_td.get_random_context()
    CLIENT, SERVER = test_td.prepare_containers(CONTEXT, os.environ['CLIENT_REV'], os.environ['SERVER_REV'])
    SERVER_PID = test_td.run_server(SERVER)
    CLIENT_PID = test_td.run_client(CLIENT)
    # explicit no Exception when ping fails
    # it's better to poll the client for a ping rather doing a long sleep
    test_td.check_ping(CLIENT, '192.168.254.1', 20)

def teardown_module():
    for cont in [CLIENT, SERVER]:
        if cont and cont.running:
            cont.shutdown(5)

class TestTunneldigger(object):
    def test_ping_tunneldigger_server(self):
        # ping 192.168.254.1
        pass

    def test_wget_tunneldigger_server(self):
        # wget http://192.168.254.1
        pass

    def test_ensure_tunnel_up_for_5m(self):
        # get id of l2tp0 iface
        ## ip -o l | awk -F: '{ print $1 }'
        # sleep 5 minutes
        # get id of l2tp0 iface
        ## ip -o l | awk -F: '{ print $1 }'
        # assert early_id == later_id
        pass
