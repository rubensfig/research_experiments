#!/usr/bin/env python3

import os

def read_df(output_dir):

    for direc, sub_direc, files in os.walk(output_dir):
        if "discarded" in direc:
            continue

        if files == []:
            continue

        if "old" in direc:
            continue

        t = dict()
        misses = 0
        drops = 0
        vectors = 0
        calls = 0
        no_buf = 0
        vector_rate = 0.0

        for file in files:
            none, label, packet_size, repeat = direc.replace(output_dir, "").split("/")

            if "vpp" in file:
                with open(
                    direc + "/" + file, "r", encoding="utf8", errors="ignore"
                ) as f:
                    for line in f.readlines():
                        p = line.strip().split()
                        if (
                            "/interfaces/dev0/rx-miss" in p[-1]
                            and "0" in p[2]
                            and "0" in p[0]
                        ):
                            misses = int(p[3])

                        if (
                            "/interfaces/dev0/rx-no-buf" in p[-1]
                            and "0" in p[2]
                            and "0" in p[0]
                        ):
                            no_buf = int(p[3])

                        if "/err/dev1-tx/Tx" in p and "2]:" in p[2] and "[0" in p[0]:
                            drops = int(p[3])

                        if (
                            "/nodes/dev1-output/vectors" in p
                            and "2]:" in p[2]
                            and "[0" in p[0]
                        ):
                            vectors = int(p[3])

                        if "/sys/vector_rate" in p:
                            vector_rate = float(p[0])

                        if (
                            "/nodes/dev1-output/calls" in p
                            and "2]:" in p[2]
                            and "[0" in p[0]
                        ):
                            calls = int(p[3])

            if "trex" in file:
                with open(direc + "/" + file, "r") as f:
                    contents = f.read().replace("\n", "").replace("'", '"')
                    try:
                        t = json.loads(contents)
                    except SyntaxError:
                        print(direc + "/" + files[0])
                        continue

        total_errors = misses + drops + no_buf

        measurements.append(
            {
                "total_rx_L1": t["results"]["total_tx_L1"],
                "total_tx_L1": int(t["results"]["total_rx_L1"]),
                "total_tx_pps": int(t["results"]["tx_pps"]),
                "total_rx_pps": int(t["results"]["rx_pps"]),
                "VNF": label,
                "packet_size": int(packet_size),
                "misses": misses,
                "drops": drops,
                "misses_normalized": misses
                / (1 if total_errors == 0 else total_errors)
                * 100,
                "drops_normalized": drops
                / (1 if total_errors == 0 else total_errors)
                * 100,
                "no_buf": no_buf,
                "total_errors": total_errors,
                "units": repeat,
                "vectors": vectors,
                "vector_rate": vector_rate,
                "call": calls,
            }
        )

    return pd.DataFrame(measurements)
