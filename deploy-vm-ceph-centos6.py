#!/bin/env python

import sys
import os
import os.path
import time
import argparse
import uuid
import random
import datetime
import shutil
import logging
import subprocess
import ConfigParser
import tempfile
import netaddr
from lxml import etree

# Parse command options.

# Helper funtions to check the type and value of argument.


def check_negative(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            "%s must be an valid positive int value." % value
        )

    return ivalue


def check_time10(value):
    ivalue = int(value)

    if ivalue <= 0 or ivalue % 10 != 0:
        raise argparse.ArgumentTypeError(
            "%s must be positive and multiple of 10." % ivalue)

    return ivalue


def check_empty(value):
    svalue = str(value)
    if svalue == '':
        raise argparse.ArgumentTypeError(
            "Empty value is not allowed.")
    return svalue


# Factory function to make parser.
def make_parser():
    parser = argparse.ArgumentParser(
        description='Create a virtual machine',
        epilog='Author: xiaopan.h@gmail.com',
        # formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Options about VM's basic inforation.
    base_group = parser.add_argument_group('Basic information')
    base_group.add_argument(
        '--conf', help='specify the configuartion file',
        dest='conf_file', required=True)
    base_group.add_argument(
        '--name', help="vm's name.", dest='vmname',
        metavar='vmname', required=True)
    base_group.add_argument(
        '--pool', help='the ceph pool where to put the rbd '
        'disk image of the vm', dest='vmpool',
        metavar='vmpool', required=True)
    base_group.add_argument(
        '--tmpl', help='the template used to create the vm, '
        'ceph template:  <pool-name>/<image-name> , such as: '
        'rbd/vm.rbd@vm.rbd.snap',
        dest='vmtmpl', metavar='vmtmpl')

    # Options about VM's capacity.
    cap_group = parser.add_argument_group('Capacity (CPU and Memory)')
    cap_group.add_argument(
        '--cpu', help="vm's cpu number. "
        "Must be positive. (Default: %(default)s)",
        dest='vmcpunumber', metavar='vmcpunumber',
        default=1, type=check_negative)
    cap_group.add_argument(
        '--mem', help="vm's memory size. Unit: GB. "
        "Must be positive. (Default: %(default)s)",
        dest='vmmemsize', metavar='vmmemsize',
        default=1, type=check_negative)

    # Options about VM's disks.
    disk_group = parser.add_argument_group(
        'Disk (System Disk, Swap Disk, '
        'Data Disk)')
    disk_group.add_argument(
        '--sys', help="vm's root disk size. Unit: GB. "
        "Must be multiple of 10. (Default: %(default)s). "
        "Note this option has no meaning in Ceph environment, the "
        "root disk is fixed to the size of the source snapshot.",
        dest='vmsyssize', default=10,
        metavar='vmsyssize', type=check_time10)
    disk_group.add_argument(
        '--data', help="vm's data disk size. Unit: GB "
        "Must be multiple of 10.", dest='vmdatasize',
        metavar='vmdatasize', type=check_time10)
    disk_group.add_argument(
        '--swap', help="vm's swap disk size. Unit: GB. ",
        dest='vmswapsize', metavar='vmswapsize', type=check_negative)

    # Options about VM's network
    net_group = parser.add_argument_group(
        'Network (Nics, Gateway, Nameserver)')
    net_group.add_argument(
        '--net', help="vm network, this can be used many "
        "times. The format of vmnet is "
        "'<bridge>/<ipaddr>/<netmask>', "
        "as 'br0/172.30.0.3/255.255.255.0' or "
        "'virbr0/192.168.44.3/24'. You can use 'br1//' if "
        "you want to create an interface but do NOT want "
        "specify ip address. Each 'vmnet' becomes vm's "
        "network interface, like eth[0,1,2..]",
        dest='vmnet', metavar='vmnet', nargs='+', required=True)
    net_group.add_argument(
        '--gw', help="vm's gateway", dest='vmgateway',
        metavar='vmgateway')
    net_group.add_argument(
        '--ns', help="vm's name server. It accepts multiple"
        "name servers separated by comma, "
        "like 8.8.8.8,114.114.114.114",
        dest='vmnameserver', metavar='vmnameserver')

    # Other options.
    other_group = parser.add_argument_group('Others')
    other_group.add_argument(
        '--vncpass', help="Password to access the "
        "console through vnc. Only 8 letters are "
        "significant for VNC passwords. It means NOT "
        "use password if this option is unspecified.",
        dest='vncpass', metavar='vncpassword',
        type=check_empty)
    other_group.add_argument(
        '--crsv', help="whether to use cpu reservation. "
        "Default is NOT use cpu reservation, specify "
        "this option means to use cpu reservation. "
        "CPU Reservation allows you to increase cpu "
        "number online. It actually allocate twice the "
        "number of 'vmcpunumber' derived from option "
        "'--cpu'.",
        dest='vmcpuresv', action='store_true',
        default=False)
    other_group.add_argument(
        '--mrsv', help="whether to use mem reservation. "
        "Default is NOT use mem reservation, specify "
        "this option means to use mem reservation. "
        "Memory Reservation allows you to increase "
        "memory size online. It actually allocate twice "
        "the number of 'vmmemsize' derived from option "
        "'--mem'.",
        dest='vmmemresv', action='store_true',
        default=False)
    other_group.add_argument(
        '--pubkey', help="ssh public key files. It "
        "accepts multiple files separated by comma. "
        "The file can be absolute path name or relative "
        "path name (relative to current directory). "
        "Like '/root/id_rsa.pub,other_key_file'. "
        "Those public key files's content will be added "
        "to vm's /root/.ssh/authorized_keys.",
        dest='pubkey', metavar='pubkeyfile')

    return parser


# Print help messages.
make_parser().parse_args()
if len(sys.argv) == 1:
    make_parser().print_help()
    sys.exit(1)


parser = argparse.ArgumentParser()
parser.add_argument('--conf', help='specify the configuartion file',
                    dest='conf_file', required=True)

# By default, the argument strings are taken from sys.argv.
# Until now, only one argument '--conf' are added to parser, so
# parse_known_args() just return the populated namespace (args) and
# the list of remaining argument.
args, remaining_argv = parser.parse_known_args()
# 'args' only contain 'conf_file'


# Get complete parser from factory function.
parser = make_parser()

# Use options read from conf_file to set default values to parser.
if args.conf_file:
    config = ConfigParser.ConfigParser()
    config.read([args.conf_file])

    # Function items() return a list of (name, value) pairs for each option
    # in the given section of the configuration file.
    options_default = dict(config.items('DEFAULT'))

    # Translate 'vmnet' from string (separated by comma) to list.
    if 'vmnet' in options_default:
        options_default['vmnet'] = options_default['vmnet'].split(',')

    parser.set_defaults(**options_default)

# Parse command line arguments.
args = parser.parse_args()


# if args.vmswapsize is None:
#    args.vmswapsize = args.vmmemsize
args.vmswapsize = 0

if args.vmmemresv is False:
    vmmemsize_max = args.vmmemsize
else:
    vmmemsize_max = args.vmmemsize * 2

if args.vmcpuresv is False:
    vmcpunumber_max = args.vmcpunumber
else:
    vmcpunumber_max = args.vmcpunumber * 2


vmtmplfile = args.vmtmpl
vmuuid = str(uuid.uuid4())
vmdir = os.path.join(args.vmdeploypath, args.vmname)
vmxmlfile = os.path.join(vmdir, args.vmname + '.xml')
vmsysfile = args.vmpool + '/' + args.vmname + '.rbd'  # fio/vmtest.rbd
vmdatafile = args.vmpool + '/' + args.vmname + \
    '-export.rbd'  # fio/vmtest-export.rbd

# Generate six-bits random number.
taskid = str(random.random()).split('.')[1][0:6]
# The log file likes /repo/logs/539658_create_vm1.log
vmcreatelog = os.path.join(
    args.vmcreatelogdir, taskid + '_create_' +
    args.vmname + '.log')

print(args)
print("=" * 20)

if not os.path.exists(args.vmcreatelogdir):
    os.mkdir(args.vmcreatelogdir, 0755)

open(vmcreatelog, 'a').close()
os.chmod(vmcreatelog, 0640)

# Set log setting.
logformatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] "
    "[%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

filehandler = logging.FileHandler(vmcreatelog)
filehandler.setFormatter(logformatter)
logger.addHandler(filehandler)

consolehandler = logging.StreamHandler()
consolehandler.setFormatter(logformatter)
logger.addHandler(consolehandler)

# Helper function to clean vm directory when error occured.


def cleanfailedcreate():
    logger.debug("Cleaning failed create.")
    shutil.rmtree(vmdir)
    sys.exit(1)


##############################
#         Create VM          #
##############################

# Exit when can't create vm directory, reason as: vmname already exist.
try:
    os.mkdir(vmdir)
except Exception:
    logger.error("Failed to create vm directory. " + str(sys.exc_info()[1]))
    sys.exit(1)
else:
    logger.debug("Suceeded to create vm directory.")


##############################
#      Create XML file       #
##############################

# All xml element variable name start with 'x_' to avoid name conflict.
x_domain = etree.Element('domain', type='kvm')

x_name = etree.SubElement(x_domain, 'name')
x_name.text = args.vmname

x_uuid = etree.SubElement(x_domain, 'uuid')
x_uuid.text = vmuuid

x_memory = etree.SubElement(x_domain, 'memory', unit='GiB')
x_memory.text = str(vmmemsize_max)

x_currentMemory = etree.SubElement(x_domain, 'currentMemory', unit='GiB')
x_currentMemory.text = str(args.vmmemsize)

x_vcpu = etree.SubElement(x_domain, 'vcpu', current=str(args.vmcpunumber))
x_vcpu.text = str(vmcpunumber_max)

x_os = etree.SubElement(x_domain, 'os')
x_type = etree.SubElement(x_os, 'type', arch='x86_64')
x_type.text = 'hvm'
# 'hvm' means full virtualization

x_boot = etree.SubElement(x_os, 'boot', dev='hd')
etree.SubElement(x_os, 'boot', dev='network')

# Define hypervisor features.
x_features = etree.SubElement(x_domain, 'features')
x_acpi = etree.SubElement(x_features, 'acpi')
x_apic = etree.SubElement(x_features, 'apic')
x_pae = etree.SubElement(x_features, 'pae')

# Define events configuration.
x_on_poweroff = etree.SubElement(x_domain, 'on_poweroff')
x_on_poweroff.text = 'destroy'

x_on_reboot = etree.SubElement(x_domain, 'on_reboot')
x_on_reboot.text = 'restart'

x_on_crash = etree.SubElement(x_domain, 'on_crash')
x_on_crash.text = 'restart'

# Define time keeping.
x_clock = etree.SubElement(x_domain, 'clock', offset='localtime')
# localtime: guest clock will be synchronized to the host's configured
# timezone when booted.

# Define devices provided to the guest domain.
x_devices = etree.SubElement(x_domain, 'devices')

x_emulator = etree.SubElement(x_devices, 'emulator')
x_emulator.text = '/usr/libexec/qemu-kvm'

# Helper function to define disk info to xml file.


def defdiskxml(parent, disk_source, disk_device):
    x_disk = etree.SubElement(parent, 'disk', type='network', device='disk')
    x_driver = etree.SubElement(x_disk, 'driver', name='qemu', discard='unmap')
    x_auth = etree.SubElement(x_disk, 'auth', username='admin')
    x_secret = etree.SubElement(x_auth, 'secret', type='ceph',
                                uuid='848f89f7-71a0-4b28-a625-902a4d5f3219')
    x_source = etree.SubElement(
        x_disk, 'source', protocol='rbd', name=disk_source)
    x_host = etree.SubElement(
        x_source, 'host', name='172.16.0.11', port='6789')
    x_host = etree.SubElement(
        x_source, 'host', name='172.16.0.12', port='6789')
    x_host = etree.SubElement(
        x_source, 'host', name='172.16.0.13', port='6789')
    x_target = etree.SubElement(x_disk, 'target', dev=disk_device, bus='scsi')


# Define disk info to xml file.
defdiskxml(x_devices, vmsysfile, 'sda')
if args.vmdatasize > 0:
    defdiskxml(x_devices, vmdatafile, 'sdb')


# Helper function to define network interface info to xml file.
def defnetxml(parent, net_source):
    x_interface = etree.SubElement(parent, 'interface', type='bridge')
    x_source = etree.SubElement(x_interface, 'source', bridge=net_source)
    x_model = etree.SubElement(x_interface, 'model', type='virtio')


# Define network info to xml file.
# vmnet = ['br0/172.30.0.3/255.255.255.0', 'virbr0/192.168.44.3/24']
for netitem in args.vmnet:
    br_if = netitem.split('/')[0]
    defnetxml(x_devices, br_if)

# Define other devices.
x_serial = etree.SubElement(x_devices, 'serial', type='pty')
x_console = etree.SubElement(x_devices, 'console', type='pty')

if args.vncpass:
    x_graphics = etree.SubElement(
        x_devices, 'graphics', type='vnc',
        autoport='yes', passwd=args.vncpass)
else:
    x_graphics = etree.SubElement(
        x_devices, 'graphics', type='vnc',
        autoport='yes')

x_listen = etree.SubElement(
    x_graphics, 'listen',
    type='address', address='0.0.0.0')


# Write the xml infomation to file.
f = open(vmxmlfile, 'w')
f.write(etree.tostring(x_domain, pretty_print=True))
f.close()

logger.debug("Suceeded to generate the xml file for guest domain.")


##############################
#     Prepare VM's Disks     #
##############################

# Prepare the sys disk.
# Clone from template file.

try:
    subprocess.call(['rbd', 'clone', vmtmplfile, vmsysfile],
                    stdout=open(os.devnull, 'wb'))
except Exception:
    logger.error(
        "Failed to clone from " + vmtmplfile + " to " + vmsysfile
        + ". " + str(sys.exc_info()[1]))
    cleanfailedcreate()
else:
    logger.debug("Succeed to clone from " + vmtmplfile + " to " + vmsysfile)


# Prepare the data disk.
if args.vmdatasize > 0:
    try:
        subprocess.call(['rbd', 'create', '--image-format', '2',
                         '--size', str(args.vmdatasize * 1024), vmdatafile],
                        stdout=open(os.devnull, 'wb'))
    except Exception:
        logger.error(
            "Failed to create data disk: " + vmdatafile
            + ". " + str(sys.exc_info()[1]))
        cleanfailedcreate()
    else:
        logger.debug("Suceeded to create data disk: " + vmdatafile)


# Prepare the swap disk.
# We disabled swap.


#####################################
#    Manipulate file's content      #
#####################################

# Mount sys disk to a temporary directory.
try:
    logger.debug("Mount sys disk to a temporary directory.")

    pobj = subprocess.Popen(['rbd', 'map', vmsysfile], stdout=subprocess.PIPE)
    rbddev = pobj.communicate()[0].strip()
    rbdmap = rbddev + "p1"

    mountpoint = tempfile.mkdtemp(dir='/tmp', prefix='kvm-mount-')
    subprocess.call(['mount', rbdmap, mountpoint],
                    stdout=open(os.devnull, 'wb'))
except Exception:
    subprocess.call(['rbd', 'unmap', rbddev], stdout=open(os.devnull, 'wb'))
    sys.exit(1)

# Change file's content
try:

    # grubcfg_file = mountpoint + "/boot/grub2/grub.cfg"
    # with open(grubcfg_file) as f:
    #    content = f.read()
    #    new_content = content.replace('vda', 'sda')
    # with open(grubcfg_file, 'w') as f:
    #    f.write(new_content)

    fstab_file = mountpoint + "/etc/fstab"
    if args.vmdatasize > 0:
        entry_string = (
            "#/dev/sdb\t\t/export\t\t\txfs\tdefaults,noatime,discard\t0 0\n"
        )
        with open(fstab_file, 'a') as f:
            f.write(entry_string)

    logger.debug("Modify network configuration.")
    # vmnet = ['br0/172.30.0.3/255.255.255.0', 'virbr0/192.168.44.3/24']
    for index, netitem in enumerate(args.vmnet):
        if_name = "eth" + str(index)
        if_file = (
            mountpoint + "/etc/sysconfig/network-scripts/ifcfg-" + if_name)

        if_ip = netitem.split('/')[1]
        if_mask = netitem.split('/')[2]

        if if_ip == '' or if_mask == '':
            if_ip = ''
            if_mask = ''
        else:
            # use IPNetwork to translate prefixlen to netmask
            if_network = netaddr.ip.IPNetwork(netitem.split('/', 1)[1])
            if_ip = if_network.ip
            if_mask = if_network.netmask
            # if_prefixlen = if_network.prefixlen

        if_file_content = (
            "DEVICE={0}\nTYPE=Ethernet\nONBOOT=yes\n"
            "BOOTPROTO=static\nIPADDR={1}\nNETMASK={2}\n")
        with open(if_file, 'w') as f:
            f.write(if_file_content.format(if_name, if_ip, if_mask))

    network_file = mountpoint + "/etc/sysconfig/network"
    network_file_content = ("NETWORKING=yes\nHOSTNAME={0}\nNOZEROCONF=yes\n")
    with open(network_file, 'w') as f:
        f.write(network_file_content.format(args.vmname))

    if args.vmgateway:
        with open(network_file, 'a') as f:
            f.write("GATEWAY={0}\n".format(args.vmgateway))

    resolv_file = mountpoint + "/etc/resolv.conf"
    if args.vmnameserver:
        for ns in args.vmnameserver.split(','):
            with open(resolv_file, 'a') as f:
                f.write("nameserver {0}\n".format(ns))

    ssh_dir = mountpoint + "/root/.ssh"
    auth_file = ssh_dir + "/authorized_keys"
    rclocal_file = mountpoint + "/etc/rc.local"

    if args.pubkey:
        if not os.path.exists(ssh_dir):
            os.mkdir(ssh_dir, 0700)

        for keyfile in args.pubkey.split(','):
            with open(auth_file, 'a') as f:
                f.write(open(keyfile, 'r').read() + '\n')

        # If authroized_keys does not exist, the security context of this file
        # created by this script is not corrected, so we need to restorecon it
        # after the start of system.
        with open(rclocal_file, 'a') as f:
            f.write("restorecon -R /root/.ssh\n"
                    "rm -rf /etc/udev/rules.d/70-persistent-net.rules\n")

finally:
    logger.debug("Umount the temporary directory.")
    subprocess.call(['umount', mountpoint])
    subprocess.call(['rbd', 'unmap', rbddev], stdout=open(os.devnull, 'wb'))


# Print summary description of this vm.
def end_desc_str(args):
    return(
        "\n{0:<20s}{vmname}\n"
        "{1:<20s}{vmtmpl}\n"
        "{2:<20s}{vmcpunumber}\n"
        "{3:<20s}{vmmemsize} GiB\n"
        "{4:<20s}{vmsyssize} GiB\n"
        "{5:<20s}{vmswapsize} GiB\n"
        "{6:<20s}{vmdatasize} GiB\n"
        "{7:<20s}{vmnet}\n"
        "{8:<20s}{vmcpuresv}\n"
        "{9:<20s}{vmmemresv}\n"
        "{10:<20s}{vncpass}\n"
        "{11:<20s}{vmcreatelog}\n"
        .format(
            "VM's Name:",
            "Template Image:",
            "CPU Number:",
            "Memory Size:",
            "System Disk Size:",
            "Swap Disk Size:",
            "Data Disk Size:",
            "Network:",
            "CPU Reservation:",
            "Memory Reservation:",
            "VNC Password:",
            "Log File:",
            **args))


# args are Namespace object, use vars to translate it to a dict.
all_vars = vars(args)
# 'vmcreatelog' exist in vars(), not in 'args'.
# Combine 'vars(args)' with vars()
all_vars.update(vars())

logger.debug("VM's summary information.")
logger.debug(end_desc_str(all_vars))

logger.debug(
    "Copy %s to the destination KVM HOST and start %s at there."
    % (vmxmlfile, args.vmname))
