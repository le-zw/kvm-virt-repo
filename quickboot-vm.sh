#!/bin/bash

# Note. This scripts is just my TEST environment.
# You should modify it to suite your own environment.

set -u

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <tmpl> <vmname> <vmip> [<vmcpu>] [<vmmem>] [<vmpath>]"
  exit 1
fi

vmtmpl=$1
vmname=$2
vmip=$3
vmcpu=${4:-2}
vmmem=${5:-4}
vmpath=${6:-''}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"&& pwd)"

_args=" \
  --conf ${SCRIPT_DIR}/deploy-vm.conf \
  --tmpl "$vmtmpl" \
  --name "$vmname" \
  --cpu "$vmcpu" \
  --mem "$vmmem" \
  --sys 100 \
  --net virbr1/${vmip}/24 \
  --gw 172.18.28.1 "

if [[ "X$vmpath" != "X" ]]; then
  _args="${_args} --path ${vmpath}"
fi

echo $_args

python ${SCRIPT_DIR}/deploy-vm-centos7.py $_args
