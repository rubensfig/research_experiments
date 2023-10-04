#!/bin/bash

RANGE=(1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 20000)
RETRIES=10
LABEL="8core-loadgen-ht"

ansible-playbook -i inventories/labshared-setup.bisdn.de.yaml loadgen_setup.yml

for i in "${RANGE[@]}"; do
    for j in $(seq 1 $RETRIES); do
        echo $i $j
        ansible-playbook -i inventories/labshared-setup.bisdn.de.yaml loadgen_test.yml -e measure_id=$j -e range=$i -e label=$LABEL
     done
done
