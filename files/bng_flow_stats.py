import stl_path
from trex.stl.api import *

import time
import pprint
from ipaddress import ip_address, ip_network

import argparse
import configparser
import os
import json

NUM_SUBSCRIBERS = 200
MAX_VLAN = 4096
TREX_VERSION = "v3.02"
TREX_DIR = f"/opt/trex/{TREX_VERSION}/"
TRAFFIC_PROFILE = "traffic_profiles.ini"


def get_packet(dst_ip, tos, size):
    # pkt = Ether(src="02:00:00:00:00:01",dst="00:00:00:01:00:01") / IP(src="10.0.0.2", tos=tos) / UDP(sport=4444, dport=4444)
    pkt = (
        Ether(src="02:00:00:00:00:01", dst="00:00:00:01:00:01")
        / IP(src="10.0.0.2", dst=ip_address(dst_ip), tos=tos)
        / UDP(sport=4444, dport=4444)
    )
    pad = max(0, size - len(pkt)) * "x"

    return pkt / pad


class Subscribers:
    def __init__(self, total=1):
        self.total = total
        self.current = -1
        self.base_ip = int(ip_address("192.168.0.0"))

    def __iter__(self):
        return self

    def __next__(self):
        if self.current == self.total - 1:
            raise StopIteration

        self.current += 1
        # hex_num = hex(self.current)[2:].zfill(6)
        return (self.current, self.base_ip + self.current)



def output_results(c, measurement_id):
    stats = c.get_stats()
    stats_dict = json.dumps(
        {
            0: stats[0],
            1: stats[1],
        },
        indent=4,
        separators=(",", ": "),
        sort_keys=True,
    )

    output_dir = f"{TREX_VERSION}/results/{measurement_id}/"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    file_path = output_dir + "trex_results.json"
    with open(file_path, "w") as results_file:
        results_file.write(stats_dict)


# RX one iteration
def rx_iteration(c, tx_port, rx_port, duration):
    c.clear_stats()

    # c.set_service_mode(ports = 0)
    # capture_id = c.start_capture(rx_ports=0)

    c.start(ports=[tx_port], duration=duration)
    c.wait_on_traffic(ports=[tx_port, rx_port])
    # c.stop_capture(capture_id["id"], "/tmp/port_0.pcap")


def get_args(argv=None):
    """
    Get Arguments for the script.
    Args:
        argv (list, optional): List of strings to parse. The default is taken from sys.argv. Defaults to None.
    Returns:
        dict: Dictionary with arguments as keys and the user chosen options as values.
    """
    parser = argparse.ArgumentParser(description="BNG Test Argument Parser")

    parser.add_argument("--pps", type=int, default=1, help="Packets per second")
    parser.add_argument("--burst-size", type=int, default=5, help="Burst Size")
    parser.add_argument("--qinq", action="store_true", help="Add a QinQ tag")
    parser.add_argument(
        "--vlans",
        type=int,
        default=10,
        help="Num of Vlans to add starting from 1. If this is big, errors can happen.",
    )
    parser.add_argument("--ncustomer", type=int, default=1, help="Num customers")
    parser.add_argument("--verbose", action="store_true", help="Be verbose")
    parser.add_argument(
        "--ignore-seq-err", action="store_true", help="Ignore Sequence errors."
    )
    parser.add_argument(
        "--direction", default="downlink", help="Traffic direction (uplink/ downlink)"
    )

    parser.add_argument("--duration", type=int, default=10, help="Test duration")

    parser.add_argument(
        "--tos",
        action="append",
        nargs="+",
        help="TOS parameters. Specify as <DSCP code>:<start in seconds>:<stream load pps>",
    )
    parser.add_argument(
        "--results_label", type=int, help="Measurement ID, used for results path."
    )
    parser.add_argument("--subscribers", type=int, help="Num of subscribers")

    args = parser.parse_args(argv)
    if args.vlans >= MAX_VLAN:
        raise Exception("Vlan can't be greater or equal {}".format(MAX_VLAN))
    return vars(args)


class BNGProfile(object):
    def __init__(self, **kwargs):
        self.config = configparser.ConfigParser()
        self.config.read(TREX_DIR + TRAFFIC_PROFILE)

    def _make_streams(self, **kwargs):
        subscribers = int(kwargs['subscribers'])
        print(subscribers)

        try:
            streams = []
            it_sub = Subscribers(subscribers)

            for sub in it_sub:
                for section in self.config.sections():

                        param_tos = int(self.config[section]['tos'])
                        param_packet_size = int(self.config[section]['packet_size'])
                        param_pps = int(self.config[section]['pps'])
                        param_start = int(self.config[section]['start'])

                        if sub[0] == 0:
                            s = STLStream(
                                packet=STLPktBuilder(
                                    pkt=get_packet(sub[1], param_tos, param_packet_size)
                                ),
                                isg = param_start * 1000000,
                                mode = STLTXCont(pps=param_pps),
                                # flow_stats = STLFlowStats(pg_id=param_tos),
                            )
                        else:
                            s = STLStream(
                                packet=STLPktBuilder(
                                    pkt=get_packet(sub[1], param_tos, param_packet_size)
                                ),
                                isg = param_start * 1000000,
                                mode = STLTXCont(pps=param_pps),
                            )

                streams.append(s)

            return streams

        except STLError as e:
            passed = False
            print(e)

    def pre_iteration(self, finding_max_rate, run_results, **kwargs):
        pass

    def get_streams(self, tunables, **kwargs):
        return self._make_streams(**kwargs)


def register():
    return BNGProfile()


def rx_example(tx_port, rx_port, **kwargs):
    duration = kwargs['duration']
    results_label = kwargs['results_label']

    # create client
    c = STLClient()

    # connect to server
    c.connect()

    # prepare our ports
    c.reset(ports=[tx_port, rx_port])

    profile = BNGProfile()
    streams = profile._make_streams(**kwargs)

    # add streams to port
    c.add_streams(streams, ports=[tx_port])

    rx_iteration(c, tx_port, rx_port, duration)

    output_results(c, results_label)


def main():
    """ """
    args = get_args()
    rx_example(
        tx_port=0,
        rx_port=1,
        direction=args["direction"],
        burst_size=args["burst_size"],
        pps=args["pps"],
        qinq=args["qinq"],
        vlans=args["vlans"],
        verbose=args["verbose"],
        ignore_seq_err=args["ignore_seq_err"],
        tos=args["tos"],
        results_label=args["results_label"],
        duration=args["duration"],
        subscribers=args["subscribers"],
    )


if __name__ == "__main__":
    main()
