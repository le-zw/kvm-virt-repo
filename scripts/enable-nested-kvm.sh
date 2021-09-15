#!/bin/bash

check_nested_kvm () {
  nested=$(cat /sys/module/kvm_intel/parameters/nested)

  if [[ $nested == "N" ]]; then
    echo "KVM Nested not enabled."
    return 1
  else
    echo "KVM Nested already enabled, exit."
    return 0
  fi
}

enable_nested_kvm() {
  echo "Enabling KVM Nested."

  ## Intel
  cat <<EOF > /etc/modprobe.d/kvm_intel.conf
options kvm_intel nested=1
EOF
  rmmod kvm_intel
  modprobe kvm_intel

  ## AMD
  cat <<EOF > /etc/modprobe.d/kvm_amd.conf
options kvm_amd nested=1
EOF
  rmmod kvm_amd
  modprobe kvm_amd
}

if ! check_nested_kvm; then
  enable_nested_kvm && check_nested_kvm
fi

cat <<EOF
Note:
  After enable kvm nested features.
  The VM started on the KVM Hypervisor should use the following cpu definition.
  <cpu mode='host-passthrough'>
  </cpu>
EOF
