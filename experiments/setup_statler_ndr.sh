#!/bin/bash

RANGE=(1 2 4 8 16 32 64 128 256 512 1024 2048 4096)
# RANGE=(1)
RETRIES=3

LABEL="l3fwd-1th-no_membuf-max-ndr"
for i in "${RANGE[@]}"; do
    for measure in $(seq 1 $RETRIES); do
	# for k in 64 256 512 1500; do
	for k in 64; do
	    echo $i $j $k;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_setup.yml -e measure_id=${measure} -e range=${i} -e label=$LABEL -e packet_size=$k -e mult=$load;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_ndr_vpp_test.yml -e measure_id=${measure} -e range=${i} -e label=$LABEL -e packet_size=$k -e mult=$load;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/vpp_teardown.yml -e measure_id=${measure} -e range=${i} -e label=$LABEL -e packet_size=$k -e mult=$load;
	done;
     done
done
