# kvm-virt-repo

## Quick Guide

```bash
python deploy-vm.py --conf deploy-vm.conf --name vm-centos6 --tmpl centos-6.8-x64 --net br0/192.168.1.100/24
python deploy-vm-centos7.py --conf deploy-vm.conf --name vm-centos7 --tmpl centos-7.2-x64 --net virbr1/172.18.28.226/24
```

## Deploy and manager KVM virtual machines

```bash
    kvm-virt-repo
    |-- deploy-vm.conf            # configuration file used by deploy-vm.py
    |-- deploy-vm.py              # script used to create a vm
    |-- deploy-vm-ceph.py         # script used to create a vm in ceph environtment
    |-- keys                      # stores public key files
    |   |-- id_rsa.pub
    |-- logs                      # log files generated when creating vm would be put in this dir
    |-- README.md
    |-- requirements              # python library dependencies that are required by deploy-vm.py
    |-- scripts                   # some scripts to ease the steps of configure KVM host
    |   |-- ch-nat-network.sh     # changes default NAT network to subnet 192.168.0.0/24
    |   |-- disk-sum.sh
    |   |-- kvm-iptables.txt
    |   |-- mkbridge.sh           # creates bridge device
    |   |-- mkkvmhost.sh          # KVM installation script
    |   |-- net-default.xml
    |-- templates                 # directory used to store templates images
    |   |-- centos5.11_x64.raw.tar.gz
    |   |-- centos6.5_x86_64.raw
    |   |-- centos6.5_x86_64.raw.tar.gz
    |-- vmimages                  # directory used to store disk image file of the vm
        |-- vm1
            |-- vm1.xml           # libvirt xml file used to define a vm
            |-- vm1.sys           # sys disk of vm: vda
            |-- vm1.data          # data disk of vm: vdb
            |-- vm1.swap          # swap disk of vm: vdc
```

## deploy-vm.py Help

```bash
    $ python deploy-vm.py  -h
    usage: deploy-vm.py [-h] --conf CONF_FILE --name vmname [--tmpl vmtmpl]
                        [--cpu vmcpunumber] [--mem vmmemsize] [--sys vmsyssize]
                        [--swap vmswapsize] [--data vmdatasize] --net vmnet
                        [vmnet ...] [--gw vmgateway] [--ns vmnameserver]
                        [--vncpass vncpassword] [--crsv] [--mrsv]
                        [--pubkey pubkeyfile]

    Create a virtual machine

    optional arguments:
      -h, --help            show this help message and exit

    Basic information:
      --conf CONF_FILE      specify the configuartion file
      --name vmname         vm's name.
      --tmpl vmtmpl         the template used to create the vm

    Capacity (CPU and Memory):
      --cpu vmcpunumber     vm's cpu number. Must be positive. (Default: 1)
      --mem vmmemsize       vm's memory size. Unit: GB. Must be positive.
                            (Default: 1)

    Disk (System Disk, Swap Disk, Data Disk):
      --sys vmsyssize       vm's root disk size. Unit: GB. Must be multiple of 10.
                            (Default: 20)
      --swap vmswapsize     vm's swap disk size. Unit: GB. Equals to size of
                            'vmmemsize' if unspecified. Must be positive.
      --data vmdatasize     vm's data disk size. Unit: GB Must be multiple of 10.

    Network (Nics, Gateway, Nameserver):
      --net vmnet [vmnet ...]
                            vm network, this can be used many times. The format of
                            vmnet is '<bridge>/<ipaddr>/<netmask>', as
                            'br0/172.30.0.3/255.255.255.0' or
                            'virbr0/192.168.44.3/24'. You can use 'br1//' if you
                            want to create an interface but do NOT want specify ip
                            address. Each 'vmnet' becomes vm's network interface,
                            like eth[0,1,2..]
      --gw vmgateway        vm's gateway
      --ns vmnameserver     vm's name server. It accepts multiplename servers
                            separated by comma, like 8.8.8.8,114.114.114.114

    Others:
      --vncpass vncpassword
                            Password to access the console through vnc. Only 8
                            letters are significant for VNC passwords. It means
                            NOT use password if this option is unspecified.
      --crsv                whether to use cpu reservation. Default is NOT use cpu
                            reservation, specify this option means to use cpu
                            reservation. CPU Reservation allows you to increase
                            cpu number online. It actually allocate twice the
                            number of 'vmcpunumber' derived from option '--cpu'.
      --mrsv                whether to use mem reservation. Default is NOT use mem
                            reservation, specify this option means to use mem
                            reservation. Memory Reservation allows you to increase
                            memory size online. It actually allocate twice the
                            number of 'vmmemsize' derived from option '--mem'.
      --pubkey pubkeyfile   ssh public key files. It accepts multiple files
                            separated by comma. The file can be absolute path name
                            or relative path name (relative to current directory).
                            Like '/root/id_rsa.pub,other_key_file'. Those public
                            key files's content will be added to vm's
                            /root/.ssh/authorized_keys.

    Author: bougou@126.com
```
