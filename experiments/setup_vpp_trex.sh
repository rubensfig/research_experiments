#!/bin/bash

RANGE=(1 2 4 8 16 32 64 128 256 512 1024 2048 4096)
RETRIES=10
MULT="3gbpsl1"
LABEL="vpp-flow-${MULT}"

for i in "${RANGE[@]}"; do
    for j in $(seq 1 $RETRIES); do
        for k in 1500; do
            echo $i $j $k;
            ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_setup.yml -e packet_size=$k;
            ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_test.yml -e measure_id=$j -e range=$i -e label=$LABEL -e packet_size=$k;
            ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/vpp_teardown.yml;
        done;
     done
done

