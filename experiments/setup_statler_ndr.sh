#!/bin/bash

RANGE=(1)
RETRIES=3
FREQ=3000

LABEL="ndr-bypass-2thread_non_sibling-ht"
for i in "${RANGE[@]}"; do
    for j in $(seq 1 $RETRIES); do
	for k in 64 256 512 1500; do
	    echo $i $j $k;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_setup.yml -e packet_size=$k;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_ndr_vpp_test.yml -e measure_id=$j -e range="L3FWD" -e label=$LABEL -e packet_size=$k -e mult=$load;
	    ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/vpp_teardown.yml;
	done;
     done
done
