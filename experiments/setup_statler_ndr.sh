#!/bin/bash

RANGE=(64)
RETRIES=10
FREQ=2200

LABEL="ndr-bypass-single"
for i in "${RANGE[@]}"; do
    for j in $(seq 1 $RETRIES); do
	# for k in 64 256 512; do
	for k in 1500; do
	    echo $i $j $k;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_setup.yml -e packet_size=$k;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_ndr_vpp_test.yml -e measure_id=$j -e range=$i -e label=$LABEL -e packet_size=$k -e mult=$load;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/vpp_teardown.yml;
	done;
     done
done
