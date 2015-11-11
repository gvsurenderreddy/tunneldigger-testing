#!/usr/bin/env python3

import lxc
from random import randint
from subprocess import check_call
from time import sleep


GIT_URL = "https://github.com/wlanslovenija/tunneldigger"
GIT_REV = "4e4f13cdc630c46909d47441093a5bdaffa0d67f"

GIT_URL = "https://github.com/lynxis/tunneldigger"
SERVER_REV = "b8b496b6b965769de898f21622f74ab3fc56ddc7"
CLIENT_REV = "b8b496b6b965769de898f21622f74ab3fc56ddc7"

def setup():
    container = lxc.Container("tunneldigger-base")

    if not container.defined:
        if not container.create("download", lxc.LXC_CREATE_QUIET, {"dist": "debian",
                                                                   "release": "squeeze",
                                                                   "arch": "amd64"}):
            raise RuntimeError("failed to create container")

    if not container.running:
        if not container.start():
            raise RuntimeError("failed to start container")

    container.attach_wait(lxc.attach_run_command, ["dhclient", "eth0"])
    container.attach_wait(lxc.attach_run_command, ["apt-get", "update"])
    container.attach_wait(lxc.attach_run_command, ["apt-get", "dist-upgrade", "-y"])

    # tunneldigger requirements
    pkg_to_install = [
        "iproute",
        "bridge-utils",
        "libnetfilter-conntrack3",
        "python-dev",
        "libevent-dev",
        "ebtables",
        "python-virtualenv",
        "build-essential",
        "libnl-dev",
        ]
    pkg_to_install += [
        "wget",
        "curl",
        "git",
        "iputils-ping"
        ]
    # for testing the connection
    pkg_to_install += [
        "lighttpd"
        ]

    container.attach_wait(lxc.attach_run_command, ["apt-get", "install", "-y"] + pkg_to_install)
    container.shutdown(30)

def get_random_context():
    """ return a random hex similiar to mktemp, but do not check is already used """
    hexi = randint(0, 2**32)
    hexi = hex(hexi)[2:]
    return hexi

def configure_network(container, bridge, is_server):
    """ configure the container and connect them to the bridge 
    container is a lxc container
    hexi is the hex for the bridge """
    config = [
        ('lxc.network.1.type', 'veth'),
        ('lxc.network.1.link', bridge),
        ('lxc.network.1.flags', 'up'),
        ]
    if is_server:
        config.append(
            ('lxc.network.1.ipv4', '172.16.16.1/24'),
            )
    else:
        config.append(
            ('lxc.network.1.ipv4', '172.16.16.2/24'),
            )

    for item in config:
        print(item)
        container.set_config_item(item[0], item[1])

def configure_mounts(container):
    mnt = c.get_config_item('lxc.mount.entry')
    mnt.append('/usr/src usr/src none bind,ro 0 0')

def create_bridge(name):
    """ setup a linux bridge device """
    check_call(["brctl", "addbr", name], timeout=10)
    check_call(["ip", "link", "set", name, "up"], timeout=10)

    # FIXME: lxc_container: confile.c: network_netdev: 474 no network device defined for 'lxc.network.1.link' = 'br-46723922' option
    sleep(3)

def check_internet(container, tries):
    for i in range(0, tries):
        ret = container.attach_wait(lxc.attach_run_command, "ping -c 1 -W 1 8.8.8.8".split())
        if ret == 0:
            return True
        sleep(1)
    return False

def check_container():
    base = lxc.Container("tunneldigger-base")
    if not base.defined:
        raise RuntimeError("Setup first the base container")

    hexi = get_random_context()
    print("generate a run for %s" % hexi) 
    server_name = "%s_server" % hexi
    client_name = "%s_client" % hexi
    bridge_name = "br-%s" % hexi
    server = lxc.Container(server_name)
    client = lxc.Container(client_name)

    if base.running:
        raise RuntimeError("base container %s is still running. Please run lxc-stop --name %s -t 5" % (base.name, base.name))

    if server.defined or client.defined:
        raise RuntimeError("server or client container already exist")

    create_bridge(bridge_name)

    server = base.clone(server_name, None,lxc.LXC_CLONE_SNAPSHOT)
    client = base.clone(client_name, None,lxc.LXC_CLONE_SNAPSHOT)

    if not server:
        if client:
            client.destroy()
        raise RuntimeError("could not create server container %s" % server_name)
    if not client:
        if server:
            server.destroy()
        raise RuntimeError("could not create client container %s" % client_name)

    configure_network(server, bridge_name, True)
    configure_network(client, bridge_name, False)

    configure_mounts(client)

    for cont in [client, server]:
        if not check_internet(cont, 5):
            raise RuntimeError("Container doesn't have an internet connection")

    spid = run_server(server)
    cpid = run_client(client)

    sleep(10)

    run_tests(server, client)

def run_server(server):
    """ run_server(server)
    server is a container
    """
    server.start()
    # wait until it has an ip via dhcp
    sleep(5)

    server.attach_wait(lxc.attach_run_command, ["git", "clone", GIT_URL, '/srv/tunneldigger/'])
    server.attach_wait(lxc.attach_run_command, ["git", "--git-dir", "/srv/tunneldigger/.git", "--work-tree", "/srv/tunneldigger/", "checkout", SERVER_REV, '/srv/tunneldigger/'])
    spid = server.attach(lxc.attach_run_command, ['/srv/tunneldigger/broker/contrib/testrun'])
    return spid

def run_client(client):
    """ run_client(client)
    client is a container
    """
    client.start()
    # wait until it has an ip via dhcp
    sleep(5)

    client.attach_wait(lxc.attach_run_command, ["git", "clone", GIT_URL, '/srv/tunneldigger/'])
    client.attach_wait(lxc.attach_run_command, ["git", "--git-dir", "/srv/tunneldigger/.git", "--work-tree", "/srv/tunneldigger/", "checkout", CLIENT_REV, '/srv/tunneldigger/'])
    cpid = client.attach(lxc.attach_run_command, ['/srv/tunneldigger/client/contrib/testrun'])
    return cpid

def run_tests(server, client):
    """ the client should be already connect to the server """
    ret = client.attach_wait(lxc.attach_run_command, ["wget", "-t", "2", "-T", "4", "http://192.168.254.1:8080/test-data", '-O', '/dev/null'])
    if ret != 0:
        raise RuntimeError("failed to run the tests")

check_container()
