#!/bin/bash

RANGE=(0.1 1 2 3 4 5 6)
RETRIES=10
LABEL="vpp-rate"

for i in "${RANGE[@]}"; do
    for j in $(seq 1 $RETRIES); do
        echo $i $j
        ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/hw_loadgen_vpp_setup.yml -e stream2_rate=$i
        ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/hw_loadgen_vpp_test.yml -e measure_id=$j -e range=$i -e label=$LABEL
        ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml vpp_teardown.yml
     done
done

