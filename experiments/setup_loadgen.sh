#!/bin/bash

RANGE=(1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 20000)
RETRIES=10
LABEL="rate-100mpps"

ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml hw_loadgen_setup.yml

for i in "${RANGE[@]}"; do
    for j in $(seq 1 $RETRIES); do
        echo $i $j
        ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ansible/loadgen_test.yml -e measure_id=$j -e range=$i -e label=$LABEL
     done
done

ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml vpp_teardown.yml
