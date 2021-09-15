#!/bin/bash

#vmname="cps"
#vmuuid="b3248d27-a63e-48d3-b466-738c35c20952"
#vmmem="4"
#vmcpu="2"

vmname=$1
vmuuid=$2
vmmem=$3
vmcpu=$4

vmbr0='br0'
vmbr1='br1'
vmbr2=''
vmnat='virbr0'


cd /var/lib/nova/instances/
#生成xml文件
mkdir ${vmuuid}/${vmname}

cat > ${vmuuid}/${vmname}/${vmname}.xml <<EOF
<domain type="kvm">
  <name>${vmname}</name>
  <uuid>${vmuuid}</uuid>
  <memory unit="GiB">${vmmem}</memory>
  <currentMemory unit="GiB">${vmmem}</currentMemory>
  <vcpu current="${vmcpu}">${vmcpu}</vcpu>
  <os>
    <type>hvm</type>
    <boot dev="hd"/>
    <boot dev="network"/>
  </os>
  <features>
    <acpi/>
    <apic/>
    <pae/>
  </features>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <clock offset="localtime"/>
  <devices>
    <emulator>/usr/libexec/qemu-kvm</emulator>
    <disk device="disk" type="file">
      <driver name='qemu' type='raw'/>
      <source file="/web/repo/vmimages/${vmname}/${vmname}.sys"/>
      <target bus="virtio" dev="vda"/>
    </disk>
    <disk device="disk" type="file">
      <driver name='qemu' type='raw'/>
      <source file="/web/repo/vmimages/${vmname}/${vmname}.data"/>
      <target bus="virtio" dev="vdb"/>
    </disk>
    <disk device="disk" type="file">
      <driver name='qemu' type='raw'/>
      <source file="/web/repo/vmimages/${vmname}/${vmname}.swap"/>
      <target bus="virtio" dev="vdc"/>
    </disk>
    <interface type="bridge">
      <source bridge="br0"/>
      <model type="virtio"/>
    </interface>
EOF

if [[ ${vmbr1} != '' ]]; then
cat >> ${vmuuid}/${vmname}/${vmname}.xml <<EOF
    <interface type="bridge">
      <source bridge="${vmbr1}"/>
      <model type="virtio"/>
    </interface>
EOF
fi

if [[ ${vmbr2} != '' ]]; then
cat >> ${vmuuid}/${vmname}/${vmname}.xml <<EOF
    <interface type="bridge">
      <source bridge="${vmbr1}"/>
      <model type="virtio"/>
    </interface>
EOF
fi

if [[ ${vmnat} != '' ]]; then
cat >> ${vmuuid}/${vmname}/${vmname}.xml <<EOF
    <interface type='bridge'>
      <source bridge="${vmnat}"/>
      <model type='virtio'/>
    </interface>
EOF
fi

cat >> ${vmuuid}/${vmname}/${vmname}.xml <<EOF
    <serial type="pty"/>
    <console type="pty"/>
    <graphics passwd="12345678" autoport="yes" type="vnc">
      <listen type="address" address="0.0.0.0"/>
    </graphics>
  </devices>
</domain>
EOF
