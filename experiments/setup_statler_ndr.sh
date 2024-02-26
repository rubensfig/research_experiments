#!/bin/bash

RANGE=(4096)
# RANGE=(1)
RETRIES=1
LABEL="l3fwd-1thread-trex-pdr0.05"

for i in "${RANGE[@]}"; do
    for measure in $(seq 1 $RETRIES); do
	for k in 64 320 576 832 1088 1344; do
	# for k in 64; do
	    echo $i $j $k;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_setup.yml -e measure_id=${measure} -e range=${i} -e label=$LABEL -e packet_size=$k -e mult=$load;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_ndr_vpp_test.yml -e measure_id=${measure} -e range=${i} -e label=$LABEL -e packet_size=$k -e mult=$load;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/vpp_teardown.yml -e measure_id=${measure} -e range=${i} -e label=$LABEL -e packet_size=$k -e mult=$load;
	done;
     done
done
