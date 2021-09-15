#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <bridge> <ethernet-if>"
    echo "eg: $0 br0 eth0"
    exit 1
fi

br_name=$1
if_name=$2

ip link show $br_name >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: $br_name does not exist, exit."
    exit 1
fi

ip link show $if_name >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: $if_name does not exist, exit."
    exit 1
fi

brctl show $br_name | grep $if_name >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: $if_name does not bridged to $br_name, exit."
    exit 1
fi


br_ipnet=$(ip addr show $br_name | grep 'inet[ ]' | awk '{print $2}')
# 172.24.119.254/24

br_ip=${br_ipnet%%/*}
# 172.24.119.254

br_mask=$(ipcalc -m $br_ipnet | cut -d= -f2 2>/dev/null)
# 255.255.255.0


if [[ -f /etc/sysconfig/network-scripts/ifcfg-${br_name} ]]; then
    rm -rf /etc/sysconfig/network-scripts/ifcfg-${br_name}
fi

cat <<EOF > /etc/sysconfig/network-scripts/ifcfg-${if_name}
DEVICE=${if_name}
TYPE=Ethernet
ONBOOT=yes
NM_CONTROLLED=no
BOOTPROTO=static
IPADDR=${br_ip}
NETMASK=${br_mask}
EOF

ifconfig ${br_name} down
brctl delif ${br_name} ${if_name}
brctl delbr ${br_name}

/etc/init.d/network restart
