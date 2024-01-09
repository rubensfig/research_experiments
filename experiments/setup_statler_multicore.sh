#!/bin/bash

RANGE=(1 2 4 8 16 32 64 128 256 512 1024 2048)
RETRIES=10
OFFERED_LOAD=("1gbpsl1" "2gbpsl1" "3gbpsl1" "4gbpsl1" "5gbpsl1" "6gbpsl1")
FREQ=2200

for load in "${OFFERED_LOAD[@]}"; do
	LABEL="multicore-${load}-${FREQ}"
	for i in "${RANGE[@]}"; do
	    for j in $(seq 1 $RETRIES); do
		# for k in 64 256 512; do
		for k in 1500; do
		    echo $i $j $k;
		    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_setup.yml -e packet_size=$k -e mult=$load;
		    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_test.yml -e measure_id=$j -e range=$i -e label=$LABEL -e packet_size=$k -e mult=$load;
		    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/vpp_teardown.yml;
		done;
	     done
	done
done
