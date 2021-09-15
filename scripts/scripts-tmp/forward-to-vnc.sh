#!/bin/bash

color_red="\033[1;31m"
color_blue="\033[1;34m"
color_no="\033[0;0m"

print_usage() {
echo -e $color_blue
cat <<EOF
This script will open listen port 15900 on your machine.
And this port will be forwarded to the target(specified VNC port on the KVM host).
So you can access <your-machine>:15900 to access virtual machine's console.
Make sure no firewall problems block you.
EOF
echo -e $color_no

cat <<EOF
Usage: $0 -j <jump1-ip> -j <jump2-ip> -t <target>

Options:
  -h                 Print this help message.

  -t <target>        The target is in format <kvm-host-ip>:<vnc-port>
                    The <kvm-host-ip> is where the virtual machine resides.
                    The <vnc-port> is a port listened on the KVM host for the virtual machine's console.
                    This vnc port can be obtained on KVM host through 'virsh vncdisplay <vm>'

  -j <jump-ip>       The ip of the intermidiate machine.
                    You can specify this option many times if there are more than one intermediate machine.
EOF

echo -e $color_red
cat <<EOF
Examples:

  $ $0 -j root@10.3.254.100 -j root@12.13.14.15 -j root@16.17.18.19 -t 192.168.8.29:5903
EOF
echo -e $color_no
}




if [[ $# == 0 ]]; then
    print_usage
    exit
fi

jump_index=0
while [[ -n $1 ]]
do
    case $1 in
        -h) print_usage; exit ;;
        -t) TARGET=$2; shift 2 ;;
        -j) jump_index=$((jump_index+1)); eval JUMP${jump_index}=$2; shift 2;;
        *) echo -e "${color_red}Wrong options.${color_no}"; exit 1 ;;
    esac
done


# handle the first jump host.
cmd_str="ssh -tL 0.0.0.0:15900:localhost:15900 $JUMP1"

# handle 'the scecond' to 'the second last' jump host.
i=2
j=$((jump_index-1))
while [[ $i -le $j ]]; do
    var_tmp="JUMP$i"
    JUMP_HOST=$(eval echo \$$var_tmp)
    cmd_str=${cmd_str}" ssh -L localhost:15900:localhost:15900 $JUMP_HOST "
    let i++
done

# handle the last jump host.
var_tmp="JUMP${jump_index}"
JUMP_HOST=$(eval echo \$$var_tmp)
cmd_str=${cmd_str}" ssh -L localhost:15900:${TARGET} $JUMP_HOST"

echo $cmd_str

eval $cmd_str
echo -e "${color_red}!!! Remember 'exit' the terminal to close connection when finished.${color_no}"
