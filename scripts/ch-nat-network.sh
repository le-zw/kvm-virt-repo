#!/bin/bash

read -p 'Do you want to change nat network range to 192.168.0.0/24[Yy/Nn]' ANSWER
case $ANSWER in
    Y | y)
        CHANGE=1
	;;
    N | n)
        CHANGE=0
        ;;
    *)
        echo "Wrong answer. Exit."; exit
        ;;
esac

if [[ $CHANGE -eq 1 ]]; then
    echo "Changing nat network range to 192.168.0.0/24..."
    sed -i 's/192.168.122/192.168.0/g' /etc/libvirt/qemu/networks/default.xml
    /etc/init.d/libvirtd restart
    virsh net-destroy default
    virsh net-start default
else
    echo "Nothing changed. Exit."; exit
fi
