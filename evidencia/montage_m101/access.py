"""Temporary SSH path scoped to the same client and coordinator."""

from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import subprocess
import sys
import time

import cloud
from control_plane import invoke


SESSION = Path(__file__).resolve().parent / "session01"
RECEIPT = SESSION / "ALT_SSH.json"
RULE = "SSH-m101-temporary"
RESOURCE_GROUP = cloud.CFG["resourceGroup"]


def remove():
    if not RECEIPT.exists():
        return
    rule = json.loads(RECEIPT.read_text())
    listing = cloud.az("network", "nsg", "rule", "list", "-g", RESOURCE_GROUP, "--nsg-name", rule["nsg"])
    if any(item["name"] == RULE for item in listing):
        cloud.az("network", "nsg", "rule", "delete", "-g", RESOURCE_GROUP, "--nsg-name", rule["nsg"], "--name", RULE)
    (SESSION / "ALT_SSH_REMOVED.json").write_text(json.dumps({"removed": True, "at": cloud.now().isoformat()}))


def guard():
    rule = json.loads(RECEIPT.read_text())
    deadline = datetime.fromisoformat(rule["deleteAt"])
    (SESSION / "ALT_SSH_GUARD_READY").touch()
    while cloud.now() < deadline and not (SESSION / "SESSION_CLOSED.json").exists():
        time.sleep(5)
    if not (SESSION / "ALT_SSH_REMOVED.json").exists():
        remove()


def enable():
    original = json.loads((SESSION / "SSH_RULE_BEFORE.json").read_text())
    rules = cloud.az("network", "nsg", "rule", "list", "-g", RESOURCE_GROUP, "--nsg-name", original["nsg"])
    active = next(r for r in rules if r["name"] == original["name"])
    source = active.get("sourceAddressPrefix")
    assert source and source.endswith("/32") and not RECEIPT.exists()
    priority = next(i for i in range(110, 200) if i not in {r["priority"] for r in rules})
    delete_at = min(cloud.now() + timedelta(minutes=45),
                    datetime.fromisoformat(json.loads((SESSION / "SESSION_START.json").read_text())["deadlineUtc"]) - timedelta(minutes=11))
    RECEIPT.write_text(json.dumps(dict(nsg=original["nsg"], deleteAt=delete_at.isoformat())))
    with (SESSION / "ALT_SSH_GUARD.log").open("w") as log:
        subprocess.Popen([sys.executable, str(Path(__file__)), "guard"], stdout=log,
                         stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(20):
        if (SESSION / "ALT_SSH_GUARD_READY").exists():
            break
        time.sleep(0.25)
    assert (SESSION / "ALT_SSH_GUARD_READY").exists()
    try:
        invoke("systemd-run --unit=dme-m101-alt-ssh --property=RuntimeMaxSec=2700 "
               "/usr/sbin/sshd -D -e -p 443 -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no "
               "-o PermitRootLogin=no -o AllowUsers=dmeadmin -o PidFile=/run/dme-m101-alt-sshd.pid",
               "ss -ltn 'sport = :443'")
        cloud.az("network", "nsg", "rule", "create", "-g", RESOURCE_GROUP, "--nsg-name", original["nsg"],
                 "--name", RULE, "--priority", str(priority), "--direction", "Inbound", "--access", "Allow",
                 "--protocol", "Tcp", "--source-address-prefixes", source,
                 "--destination-address-prefixes", "10.42.0.4/32", "--destination-port-ranges", "443")
        cfg = SESSION / "ssh_config"
        (SESSION / "ssh_config_port22").write_bytes(cfg.read_bytes())
        config = cfg.read_text().replace("  BatchMode yes", "  BatchMode yes\n  Port 443")
        cfg.write_text(config, encoding="ascii", newline="\n")
        (SESSION / "DATA_ROOT.txt").write_text("/mnt/montage_m101_20261111", encoding="ascii")
        print("Temporary source-restricted SSH path configured.")
    except Exception:
        remove()
        raise


if __name__ == "__main__":
    {"enable": enable, "remove": remove, "guard": guard}[sys.argv[1]]()
