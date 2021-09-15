#!/bin/bash

echo "Total memory allocated for all domains: "
virsh list --all --uuid \
    | xargs -I {} virsh dumpxml {} --inactive \
    | grep memory | awk -F'[<>]' '{print $3}' \
    | awk '{sum+=$1}END{print sum}'


echo "Total memory allocated for running domains: "
virsh list --state-running --uuid \
    | xargs -I {} virsh dumpxml {} --inactive \
    | grep memory | awk -F'[<>]' '{print $3}' \
    | awk '{sum+=$1}END{print sum}'
