#!/bin/bash

TEST=("full" "nofull")
RANGE=(1 2 3 4)
RETRIES=10

for test_type in "${TEST[@]}"; do
	for i in "${RANGE[@]}"; do
	    LABEL="multicore-${test_type}-$i"
	    for j in $(seq 1 $RETRIES); do
		    for k in 1500; do
                ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_setup.yml -e packet_size=$k -e test_type=$test_type;
                ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_test.yml -e measure_id=$j -e range=$i -e label=$LABEL -e packet_size=$k -e test_type=$test_type;
                ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/vpp_teardown.yml;
		    done;
	     done
	done
done
