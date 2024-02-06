#!/bin/bash

RETRIES=10
LABEL="remote"

for measure in $(seq 1 $RETRIES); do
	ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_loadgen_vpp_setup.yml -e measure_id=${measure} -e range=1 -e label=$LABEL -e packet_size=512 -e mult=$MULT;
	ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/trex_latency_vpp_test.yml -e measure_id=${measure} -e range=1 -e label=$LABEL -e packet_size=512 -e mult=$MULT;
	ansible-playbook -i ../inventories/labshared-setup.bisdn.de.yaml ../ansible/vpp_teardown.yml -e measure_id=${measure} -e range=1 -e label=$LABEL -e packet_size=512 -e mult=$MULT;
done
