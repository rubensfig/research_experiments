#!/bin/bash

RANGE=(4096)
RETRIES=3
MULT="30gbpsl1"
LABEL="batch_size_0"

for i in "${RANGE[@]}"; do
    for measure in $(seq 1 $RETRIES); do
        for k in 512; do
            echo $i $j $k;
            ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_setup.yml -e measure_id=${measure} -e range=${i} -e label=$LABEL -e packet_size=$k -e mult=$MULT;
            ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_test.yml -e measure_id=${measure} -e range=$i -e label=$LABEL -e packet_size=$k -e mult=$MULT;
            ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/vpp_teardown.yml -e measure_id=${measure} -e range=${i} -e label=$LABEL -e packet_size=$k -e mult=$MULT;
        done;
     done
done
