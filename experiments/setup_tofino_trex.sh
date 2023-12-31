#!/bin/bash

RANGE=(1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192)
RETRIES=1
LABEL="tofino-flows-25gbps"

for i in "${RANGE[@]}"; do
    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_tofino_setup.yml
    for j in $(seq 1 $RETRIES); do
        echo $i $j
        ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_tofino_test.yml -e measure_id=$j -e range=$i -e label=$LABEL
        ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/tofino_teardown.yml
     done
done

