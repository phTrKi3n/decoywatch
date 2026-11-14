import collections
import datetime
import ipaddress
import json
import re
import subprocess
import sys
import time
import uuid

def event(line, now, state):
    if not line.startswith("LAB_WAN_BLOCK "):
        return None
    fields = dict(re.findall(r"(\w+)=([^\s]+)", line))
    if (fields.get("IN"), fields.get("PROTO"), fields.get("DST")) != ("ens37", "TCP", "192.168.100.20"):
        return None
    try:
        source = str(ipaddress.IPv4Address(fields["SRC"]))
        port = int(fields["DPT"])
    except (KeyError, ValueError):
        return None
    if not 1 <= port <= 65535:
        return None
    for key, (seen, last_alarm) in list(state.items()):
        for old in list(seen):
            if now - seen[old] >= 30:
                del seen[old]
        if not seen and now - last_alarm >= 30:
            del state[key]
    key = (source, fields["DST"])
    if key not in state and len(state) >= 256:
        state.popitem(last=False)
    seen, last_alarm = state.setdefault(key, ({}, float("-inf")))
    state.move_to_end(key)
    if len(seen) < 1024 or port in seen:
        seen[port] = now
    if len(seen) < 5 or now - last_alarm < 30:
        return None
    state[key] = (seen, now)
    return {"eventid": "lab.firewall.scan", "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "src_ip": source, "dest_ip": fields["DST"], "port_count": len(seen), "event_id": uuid.uuid4().hex}

def check():
    def row(port, source="192.0.2.10", device="ens37", target="192.168.100.20"):
        return f"LAB_WAN_BLOCK IN={device} SRC={source} DST={target} PROTO=TCP DPT={port}"
    state = collections.OrderedDict()
    for j, port in enumerate([20, 21, 20, 22, 23, 21]):
        assert event(row(port), j, state) is None
    assert event(row(24, source="192.0.2.11"), 6, state) is None
    assert event(row(24, target="192.0.2.20"), 6, state) is None
    assert event(row(24, device="ens33"), 6, state) is None
    assert event(row(24), 6, state)["port_count"] == 5
    assert event(row(25), 7, state) is None
    state.clear()
    for i in range(5):
        assert event(row(20+i), i*10, state) is None
    print("PASS: distinct ports, timing, sources, interface and dedup")

if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        check()
    else:
        state = collections.OrderedDict()
        with subprocess.Popen(["journalctl", "-k", "-f", "-n", "0", "-o", "cat"], stdout=subprocess.PIPE, text=True) as journal:
            for line in journal.stdout:
                result = event(line, time.monotonic(), state)
                if result:
                    print(json.dumps(result), flush=True)
        sys.exit(1)
