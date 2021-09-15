#!/bin/bash

set -u

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <tmpl> <vmname> <vmip> [<vmcpu>] [<vmmem>]"
  exit 1
fi

vmtmpl=$1
vmname=$2
vmip=$3
vmcpu=${4-2}
vmmem=${5-4}

python ./deploy-vm-centos6.py \
  --conf ./deploy-vm.conf \
  --tmpl "$vmtmpl" \
  --name "$vmname" \
  --cpu "$vmcpu" \
  --mem "$vmmem" \
  --sys 100 \
  --net virbr1/${vmip}/24 \
  --gw 172.18.28.1

