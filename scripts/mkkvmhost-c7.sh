#!/bin/bash

color_red="\033[1;31m"
color_blue="\033[1;34m"
color_no="\033[0;0m"

if [ $# != 1 ]; then
    echo -e "${color_blue}Usage: $0 <ipaddr>${color_no}"
    echo "  <ipaddr> is the address on which the libvirtd daemon listen."
    echo "  0.0.0.0 means libvirtd binds to all network interface."
    echo "  But usually use INTERNAL network IP."
    exit 1
fi

LIBVIRT_LISTEN_IP=$1

# Install software packages related to kvm.

yum install -y kvm qemu-kvm bridge-utils libvirt libvirt-python virt-install
yum install -y kpartx
yum install -y python-argparse python-lxml python-netaddr


# You can install virt-manager if in GUI environment.

#yum install -y virt-manager


# Enable libvirtd listen.

sed -i -e "
/#LIBVIRTD_ARGS/s/#LIBVIRTD_ARGS/LIBVIRTD_ARGS/;
" /etc/sysconfig/libvirtd

# Modify libvirtd configuration.

sed -i -e "
/#listen_tls/s/#listen_tls/listen_tls/;
/#listen_tcp/s/#listen_tcp/listen_tcp/;
/#auth_tcp/s/#auth_tcp/auth_tcp/;
/auth_tcp/s/sasl/none/;
" /etc/libvirt/libvirtd.conf

sed -i -e "
/#listen_addr/c\listen_addr = \"$LIBVIRT_LISTEN_IP\"
" /etc/libvirt/libvirtd.conf

# Start libvirtd
systemctl restart libvirtd
