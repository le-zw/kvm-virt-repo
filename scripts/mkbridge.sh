#!/bin/bash

color_red="\033[1;31m"
color_blue="\033[1;34m"
color_no="\033[0;0m"

if [ $# -ne 2 ]; then
    echo -e "${color_blue}Usage: $0 <bridge> <ethernet-if>${color_no}"
    echo "   eg: $0 br0 eth0"
    echo -e "${color_red}Warn: This script will override ifcfg-<ethN> file, \nso make sure gateway is configured on /etc/sysconfig/network.${color_no}"
    exit 1
fi

br_name=$1
if_name=$2

ip link show $br_name >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "ERROR: $br_name already exist, exit."
    exit 1
fi

ip link show $if_name >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: $if_name does not exist, exit."
    exit 1
fi


if_ipnet=$(ip addr show $if_name | grep 'inet[ ]' | awk '{print $2}')
# 172.24.119.254/24

if_ip=${if_ipnet%%/*}
# 172.24.119.254

if_mask=$(ipcalc -m $if_ipnet | cut -d= -f2 2>/dev/null)
# 255.255.255.0

cat <<EOF > /etc/sysconfig/network-scripts/ifcfg-${if_name}
DEVICE=${if_name}
TYPE=Ethernet
BRIDGE=${br_name}
ONBOOT=yes
NM_CONTROLLED=no
BOOTPROTO=none
EOF

cat <<EOF > /etc/sysconfig/network-scripts/ifcfg-${br_name}
DEVICE=${br_name}
TYPE=Bridge
ONBOOT=yes
NM_CONTROLLED=no
BOOTPROTO=static
IPADDR=${if_ip}
NETMASK=${if_mask}
EOF

/etc/init.d/network restart
