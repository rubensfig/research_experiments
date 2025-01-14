from ixnetwork_restpy import SessionAssistant, Files, TestPlatform, StatViewAssistant
import os
import time
import json
import numpy as np

START_TRAFFIC = True
GENERATE_TRAFFIC = True
COLLECT_STATS = True
STORE_STATS = True

TEST_INTERVAL = 60
EXPSET = "LS2"
EXP = "e1_1"
SAVE_DIR = r"C:\Users\Administrator\Documents\rubens\load_strategies"

apiServerIP = "127.0.0.1"
chassisIP = "172.30.20.132"
# MAX_FLOWS = 65536
MAX_FLOWS = 16384

json_file_path = "./load_strategies.json"

with open(json_file_path, "r") as j:
    config = json.loads(j.read())


def topology_setup(ixnetwork, traffic_items):
    ixnetwork.info("Add HQoS Topology")
    topo = ixnetwork.Topology.add(Name="HQoS Topology 1", Ports=port)

    for i in range(0, len(traffic_items)):
        traffic_item_name = traffic_items[i]

        BASE_UPSTREAM_MAC = f"00:{i}:01:00:00:01"
        BASE_UPSTREAM_GATEWAY_MAC = f"00:11:22:33:44:{i+1}"
        BASE_DOWNSTREAM_MAC = f"01:{i}:00:00:00:01"
        BASE_DOWNSTREAM_GATEWAY_MAC = f"00:FF:22:33:44:{i+1}"

        UPSTREAM_IP = f"10.{i}.0.0"
        DOWNSTREAM_IP = f"192.16{i}.0.0"

        ixnetwork.info("Add US Device Group")
        us_dg = topo.DeviceGroup.add(Name="Upstream-" + traffic_item_name, Multiplier=1)
        us_mac = us_dg.Ethernet.add()
        us_mac.Mac.Single(BASE_UPSTREAM_MAC)
        us_mac.UseVlans = "true"
        us_vlan1 = us_mac.Vlan.find()[0]
        us_vlan1.VlanId.Single(1)

        # v4 Address
        us_v4 = us_mac.Ipv4.add()
        us_v4.Address.Single(UPSTREAM_IP)
        us_v4.Prefix.Single(24)

        us_v4.ResolveGateway.Single(False)  # Disable ARP Resolution
        us_v4.ManualGatewayMac.Single(BASE_UPSTREAM_GATEWAY_MAC)

        ixnetwork.info("Add DS Device Group")
        ds_dg = topo.DeviceGroup.add(
            Name="Downstream-" + traffic_item_name, Multiplier=MAX_FLOWS
        )
        ds_mac = ds_dg.Ethernet.add()
        ds_mac.Mac.Increment(
            start_value=BASE_DOWNSTREAM_MAC, step_value="00:00:00:00:00:01"
        )
        ds_mac.UseVlans = "true"
        ds_vlan1 = ds_mac.Vlan.find()[0]
        ds_vlan1.VlanId.Single(1)

        # v4 Address
        ds_v4 = ds_mac.Ipv4.add()
        ds_v4.Address.Increment(start_value=DOWNSTREAM_IP, step_value="0.0.0.1")
        ds_v4.Prefix.Single(16)

        ds_v4.ResolveGateway.Single(False)  # Disable ARP Resolution
        ds_v4.ManualGatewayMac.Single(BASE_DOWNSTREAM_GATEWAY_MAC)

    return topo


def config_foreground(topology, traffic_item):
    fg_config = config[EXPSET][EXP]["traffic_profiles"]["foreground"]

    upstream_src = ""
    downstream_src = ""

    for devicegroup in topology.DeviceGroup.find():
        if ("Upstream-" + fg_config["traffic_items"][0]) == devicegroup.Name:
            upstream_src = devicegroup
        elif ("Downstream-" + fg_config["traffic_items"][0]) == devicegroup.Name:
            downstream_src = devicegroup.href
        else:
            pass

    endpoint = traffic_item.EndpointSet.add(
        Name=fg_config["flow_groups"][0],
        Sources=upstream_src,
    )
    endpoint.ScalableDestinations = [
        {
            # "arg1": "/api/v1/sessions/1/ixnetwork/topology/1/deviceGroup/2/ethernet/1/ipv4/1",
            "arg1": downstream_src + "/ethernet/1/ipv4/1",  # Very hacky
            "arg2": 1,
            "arg3": 1,
            "arg4": 1,
            "arg5": 1,
        }
    ]  # Number of endpoints = arg5

    fg_config_element = traffic_item.ConfigElement.find()[0]

    fg_config_element.FrameRate.Type = "bitsPerSecond"
    fg_config_element.FrameRate.BitRateUnitsType = "bitsPerSec"
    fg_config_element.FrameRate.Rate = fg_config["data_rate"][0]
    fg_config_element.FrameSize.FixedSize = fg_config["frame_size"][0]

    v4 = fg_config_element.Stack.find()[2]
    prio = v4.Field.find()[2]
    prio.SingleValue = hex(fg_config["priority"][0])
    prio.ActiveFieldChoice = True


def get_background_loops():
    background = config[EXPSET][EXP]["traffic_profiles"]["background"]

    # Check if the background config has direct levels or is divided into priorities
    if "levels" in bg_config:
        # Handle the flat structure with direct `levels`
        prio_configs = {"default": bg_config}
    else:
        # Handle nested priority levels
        prio_configs = {key: value for key, value in bg_config.items() if key.startswith("prio_")}

    print(prio_configs)
    return prio_configs[list(prio_configs)[0]]["frame_size"], prio_configs[list(prio_configs)[0]]["levels"]


def config_background(topology, traffic_items, level_id, packet_size):
    bg_config = config[EXPSET][EXP]["traffic_profiles"]["background"]

    # Check if the background config has direct levels or is divided into priorities
    if "levels" in bg_config:
        # Handle the flat structure with direct `levels`
        prio_configs = {"default": bg_config}
    else:
        # Handle nested priority levels
        prio_configs = {key: value for key, value in bg_config.items() if key.startswith("prio_")}

    for prio_level, prio_config in prio_configs.items():
        for item in prio_config["traffic_items"]:

            upstream_src = ""
            downstream_src = ""

            for devicegroup in topology.DeviceGroup.find():
                if ("Upstream-" + item) == devicegroup.Name:
                    upstream_src = devicegroup
                elif ("Downstream-" + item) == devicegroup.Name:
                    downstream_src = devicegroup.href
                else:
                    pass

            for i in range(0, len(prio_config["flow_groups"])):

                endpoint = traffic_item.EndpointSet.find(
                    Name=item + prio_config["flow_groups"][i]
                )
                if not endpoint:
                    endpoint = traffic_item.EndpointSet.add(
                        Name=item + prio_config["flow_groups"][i], Sources=upstream_src
                    )

                endpoint.ScalableDestinations = [
                    {
                        # "arg1": "/api/v1/sessions/1/ixnetwork/topology/1/deviceGroup/2/ethernet/1/ipv4/1",
                        "arg1": downstream_src + "/ethernet/1/ipv4/1",  # Very hacky
                        "arg2": 1,
                        "arg3": 1,
                        "arg4": 2,  # Start
                        "arg5": prio_config["levels"][level_id],
                    }
                ]  # Number of endpoints = arg5

                bg_config_element = traffic_item.ConfigElement.find()[-1]

                bg_config_element.FrameRate.Type = "bitsPerSecond"
                bg_config_element.FrameRate.BitRateUnitsType = "bitsPerSec"
                bg_config_element.FrameRate.Rate = prio_config["data_rate"][level_id]
                bg_config_element.FrameSize.FixedSize = packet_size

                v4 = bg_config_element.Stack.find()[2]
                prio = v4.Field.find()[2]
                prio.SingleValue = hex(prio_config["priority"][i])
                prio.ActiveFieldChoice = True


# create a test tool session
session = SessionAssistant(
    IpAddress=apiServerIP,
    UserName="admin",
    Password="admin",
    LogLevel=SessionAssistant.LOGLEVEL_INFO,
    ClearConfig=True,
)

ixnetwork = session.Ixnetwork
chassis = ixnetwork.AvailableHardware.Chassis.add(Hostname=chassisIP)

ixnetwork.info("Assign ports")
portMap = session.PortMapAssistant()
port = portMap.Map(Location=chassisIP + ";5;13", Name="Port 1")
portMap.Connect(ForceOwnership=True, HostReadyTimeout=20, LinkUpTimeout=60)

# Setup Topology
prio_configs = None
bg_config = config[EXPSET][EXP]["traffic_profiles"]["background"]
# Check if the background config has direct levels or is divided into priorities
if "levels" in bg_config:
    # Handle the flat structure with direct `levels`
    prio_configs = {"default": bg_config}
else:
    # Handle nested priority levels
    prio_configs = {key: value for key, value in bg_config.items() if key.startswith("prio_")}

traffic_items = [prio_configs[i]["traffic_items"] for i in prio_configs]
traffic_items = [item for sublist in traffic_items for item in (sublist if isinstance(sublist, list) else [sublist])] # flatten list

print(traffic_items)
topology = topology_setup(ixnetwork, traffic_items)
ixnetwork.StartAllProtocols(Arg1="sync")

# Setup Traffic Item
traffic_item = ixnetwork.Traffic.TrafficItem.add(
    Name="TE1",
    TrafficType="ipv4",
    TrafficItemType="l2L3",
    AllowSelfDestined=True,
)
traffic = ixnetwork.Traffic.find()[0]
traffic.Statistics.Latency.Mode = "cutThrough"

if "foreground" in config[EXPSET][EXP]["traffic_profiles"]:
    config_foreground(topology, traffic_item)
packet_sizes, levels = get_background_loops()

# Test configurations
lb_config = config[EXPSET][EXP]["latency_bins"]
repetitions = config[EXPSET]["repetitions"] + 1  # Account for "warmup"


for level_id in range(0, len(levels)):
    for packet_size in packet_sizes:
        for repeat in range(0, repetitions):
            ixnetwork.info(
                f"Configuring background traffic, level={level_id},packet_size={packet_size}"
            )
            config_background(topology, traffic_item, level_id, packet_size)

            ixnetwork.info("Adding Tracking and Latency Bins Config")
            latency_bins = list(
                np.linspace(
                    start=lb_config["start"][level_id],
                    stop=lb_config["stop"][level_id],
                    num=lb_config["num"],
                )
            )
            tracking = traffic_item.Tracking.find()[0]
            tracking.TrackBy = ["ipv4Raw0", "flowGroup0"]
            tracking.LatencyBin.Enabled = True
            tracking.LatencyBin.BinLimits = latency_bins
            tracking.LatencyBin.NumberOfBins = len(latency_bins)

            td = traffic_item.TransmissionDistribution.find()[0]
            td.Distributions = ["ipv4Raw0"]

            traffic_item.Generate()
            ixnetwork.Traffic.Apply()

            latency_bins_view = ixnetwork.Statistics.View.find(Caption="Latency Bins")
            if not latency_bins_view:
                ixnetwork.info("Adding Statistics View")
                view = ixnetwork.Statistics.View.add(
                    Caption="Latency Bins",
                    TreeViewNodeName="Latency Bins",
                    Visible=True,
                    Type="layer23TrafficFlow",
                    EnableCsvLogging=True,
                    # CsvFileName="Latency Bins",
                )

                # Dynamically get the Traffic Item Filter ID
                availableTrafficItemFilterId = []
                for eachTrafficItemFilterId in view.AvailableTrafficItemFilter.find():
                    if eachTrafficItemFilterId.Name == "TE1":
                        availableTrafficItemFilterId.append(
                            eachTrafficItemFilterId.href
                        )

                l23_filter = view.Layer23TrafficFlowFilter.find()[0]
                l23_filter.EgressLatencyBinDisplayOption = "showLatencyBinStats"
                l23_filter.PortFilterIds = [
                    "/api/v1/sessions/1/ixnetwork/statistics/view/14/availablePortFilter/1"
                ]
                l23_filter.TrafficItemFilterId = availableTrafficItemFilterId[0]
                l23_filter.TrafficItemFilterIds = availableTrafficItemFilterId

                for eachEgressStatCounter in view.Statistic.find():
                    eachStatCounterName = eachEgressStatCounter.Caption
                    ixnetwork.info(
                        "Enabling egress stat counter: {}".format(eachStatCounterName)
                    )
                    if (
                        "Rx Frames per Bin" in eachStatCounterName
                        or "Tx Frames" in eachStatCounterName
                        or "Rx Frames" in eachStatCounterName
                        or "Loss %" in eachStatCounterName
                        or eachStatCounterName == "Tx Frame Rate"
                        or eachStatCounterName == "Rx Frame Rate"
                        or eachStatCounterName == "Tx Rate (bps)"
                        or eachStatCounterName == "Rx Rate (bps)"
                        or eachStatCounterName == "Cut-Through Avg Latency (ns)"
                        or eachStatCounterName == "Cut-Through Max Latency (ns)"
                        or eachStatCounterName == "Cut-Through Min Latency (ns)"
                    ):
                        eachEgressStatCounter.Enabled = True

                for eachTrackingFilterId in view.AvailableTrackingFilter.find():
                    l23_filter.EnumerationFilter.add(
                        TrackingFilterId=eachTrackingFilterId.href
                    )
                    # l23_filter.TrackingFilter.add(TrackingFilterId=eachTrackingFilterId.href)

                view.Enabled = True

            traffic_item.Generate()
            ixnetwork.Traffic.Apply()

            ixnetwork.info("Starting Traffic")

            ixnetwork.Traffic.Start()

            if repeat == 0:  # Deal with weird latency bins issue
                ixnetwork.Traffic.Stop()
                continue

            while ixnetwork.Traffic.ElapsedTransmitTime < TEST_INTERVAL * 10**3:
                continue
            ixnetwork.Traffic.Stop()

            level_data = levels[level_id]
            stats_save_dir = (
                SAVE_DIR + "\\" + EXP + "\\" + str(level_data) + "\\" + str(packet_size)
            )

            if not os.path.exists(stats_save_dir):
                os.makedirs(stats_save_dir)

            statistics = ixnetwork.Statistics
            csvsnapshot = statistics.CsvSnapshot
            csvsnapshot.update(
                CsvName="Latency Bins" + str(repeat),
                CsvLocation=stats_save_dir,
                SnapshotViewCsvGenerationMode="overwriteCSVFile",
                SnapshotViewContents="allPages",
                Views=statistics.View.find(Caption="Latency Bins"),
            )
            csvsnapshot.TakeCsvSnapshot()
