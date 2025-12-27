from __future__ import annotations

import argparse
import logging
import sys
from typing import List

from . import bond
from .bond import BondObject
from .config import Config
from .generator import generate_lxaddon
from .mapper import Mapper

DEFAULT_TIMEOUT = 3.0
DEFAULT_POLL_INTERVAL = 30

def _setup_logging(verbosity: int, quiet: bool) -> None:
    if quiet:
        level = logging.ERROR
    elif verbosity == 0:
        level = logging.INFO
    elif verbosity == 1:
        level = logging.DEBUG
    else:
        level = logging.NOTSET  # Trace/Verbose

    logging.basicConfig(
        level=level,
        format="%(message)s" if level >= logging.INFO else "[%(levelname)s] %(message)s",
        stream=sys.stdout
    )

def _collect_objects(base: str, token: str, timeout: float, include_state: bool) -> List[BondObject]:
    objs: List[BondObject] = []

    # Devices
    try:
        dev_idx = bond.get_index(base, "DEVICE", token, timeout)
        dev_ids = sorted([k for k in dev_idx.keys() if bond.looks_like_id(k)])
        
        for did in dev_ids:
            try:
                dj = bond.get_object(base, "DEVICE", did, token, timeout)
                st = bond.get_state(base, "DEVICE", did, token, timeout) if include_state else {}
                props = bond.get_properties(base, "DEVICE", did, token, timeout)
                
                objs.append(BondObject(
                    kind="DEVICE",
                    obj_id=did,
                    name=str(dj.get("name", "(unnamed)")),
                    obj_type=str(dj.get("type", "(unknown)")),
                    location=str(dj.get("location", "-")),
                    actions_raw=bond.extract_actions(dj),
                    members=[],
                    raw=dj,
                    state=st,
                    properties=props
                ))
            except Exception as e:
                logging.error(f"Failed to fetch device {did}: {e}")
    except Exception as e:
        logging.error(f"Failed to fetch device index: {e}")

    # Groups
    try:
        grp_idx = bond.get_index(base, "GROUP", token, timeout)
        grp_ids = sorted([k for k in grp_idx.keys() if bond.looks_like_id(k)])
        
        for gid in grp_ids:
            try:
                gj = bond.get_object(base, "GROUP", gid, token, timeout)
                st = bond.get_state(base, "GROUP", gid, token, timeout) if include_state else {}
                
                # Determine group type
                group_types = gj.get("types", [])
                unique_types = sorted(list(set(group_types)))
                
                if len(unique_types) == 1:
                    obj_type = unique_types[0]
                elif len(unique_types) > 1:
                    logging.warning(f"Skipping group {gid} ({gj.get('name')}): Mixed types {unique_types} not supported")
                    continue
                else:
                    obj_type = "group"

                objs.append(BondObject(
                    kind="GROUP",
                    obj_id=gid,
                    name=str(gj.get("name", "(unnamed group)")),
                    obj_type=obj_type,
                    location=str(gj.get("location", "-")),
                    actions_raw=bond.extract_actions(gj),
                    members=bond.extract_members(gj),
                    raw=gj,
                    state=st,
                    properties={} # Groups don't have properties endpoint usually
                ))
            except Exception as e:
                logging.error(f"Failed to fetch group {gid}: {e}")
    except Exception as e:
        logging.error(f"Failed to fetch group index: {e}")

    # Stable sort to keep outputs deterministic
    objs.sort(key=lambda o: (0 if o.kind == "GROUP" else 1, o.location.lower(), o.name.lower(), o.obj_id))
    return objs

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a Loxone .LxAddon by scanning a Bond Bridge local API (v2).")
    ap.add_argument("--host", required=True, help="Bond Bridge IP/host, e.g. 192.168.1.13")
    ap.add_argument("--token", required=True, help="Bond local token")
    ap.add_argument("--out", default="bond2loxone.LxAddon", help="Output .LxAddon path")
    ap.add_argument("--config", help="Path to JSON configuration file")
    ap.add_argument("--include-state", action=argparse.BooleanOptionalAction, default=True, help="Query and include state information")
    ap.add_argument("--state-poll-interval", type=int, default=DEFAULT_POLL_INTERVAL, help=f"Polling interval for state updates (default: {DEFAULT_POLL_INTERVAL})")
    ap.add_argument("--emit-intermediate", default=None, help="Directory to write intermediate files (desc.json/template.xml/inventory.json) before zipping")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds (default: 3.0)")
    ap.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity")
    ap.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error output")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be generated without creating files")
    
    args = ap.parse_args()
    _setup_logging(args.verbose, args.quiet)

    base = f"http://{args.host}"
    
    logging.info(f"Discovering Bond Bridge at {args.host}...")
    
    try:
        sys_ver = bond.get_sys_version(base, args.token, args.timeout)
        bond_id = sys_ver.get("bondid", "UNKNOWN")
        firmware = sys_ver.get("fw_ver", "UNKNOWN")
        logging.info(f"Bond ID: {bond_id}")
        logging.info(f"Firmware: {firmware}")
    except Exception as e:
        logging.error(f"Failed to connect to Bond Bridge: {e}")
        return 1

    # Load config
    config = Config.load(args.config)
    
    # Discovery
    objs = _collect_objects(base, args.token, args.timeout, args.include_state)
    
    if not objs:
        logging.warning("No devices or groups found!")
        return 0

    # Mapping
    mapper = Mapper(config)
    all_endpoints = []
    all_inputs = []
    
    unknown_actions = []

    logging.info("")
    logging.info(f"Discovered {len([o for o in objs if o.kind == 'DEVICE'])} Devices, {len([o for o in objs if o.kind == 'GROUP'])} Groups:")
    
    for o in objs:
        endpoints, inputs = mapper.map_object(o)
        all_endpoints.extend(endpoints)
        all_inputs.extend(inputs)
        
        logging.info(f"  [{o.kind}] {o.name} ({o.obj_type})")
        logging.info(f"    ID: {o.obj_id}")
        logging.info(f"    Location: {o.location}")
        
        actions = [k for k, _ in bond.iter_action_items(o.actions_raw)]
        logging.info(f"    Actions: {', '.join(actions)}")
        
        logging.info(f"    → Mapped to {len(endpoints)} Virtual Outputs")
        if inputs:
            logging.info(f"    → State: {', '.join([i.state_key for i in inputs])} ({len(inputs)} Virtual Inputs)")
            
        # Check for unknown actions
        for ep in endpoints:
            if ep.is_unknown:
                unknown_actions.append((o, ep))

    # Report unknown actions
    if unknown_actions:
        logging.warning("")
        logging.warning("⚠ UNKNOWN ACTIONS DETECTED")
        
        # Group by action key to avoid spam
        reported = set()
        for o, ep in unknown_actions:
            key = (o.obj_id, ep.action_key)
            if key in reported: continue
            reported.add(key)
            
            if ep.unknown_test_type == "digital": # Only print once per action (digital is first)
                logging.warning(f"  Action '{ep.action_key}' on device {o.name} ({o.obj_id})")
                logging.warning(f"    Generated test cases:")
                logging.warning(f"      A) Digital output (momentary)")
                logging.warning(f"      B) Analog output (0-100)")
                logging.warning(f"    ")
                logging.warning(f"    Please test these in Loxone Config and update your mapping file:")
                logging.warning(f"    ")
                logging.warning(f"    If A works (digital):")
                logging.warning(f"    {{")
                logging.warning(f"      \"match\": {{\"device_id\": \"{o.obj_id}\", \"action\": \"{ep.action_key}\"}},")
                logging.warning(f"      \"loxone\": {{\"type\": \"digital\", \"description\": \"{ep.action_key}\"}}")
                logging.warning(f"    }}")
                logging.warning(f"    ")
                logging.warning(f"    If B works (analog):")
                logging.warning(f"    {{")
                logging.warning(f"      \"match\": {{\"device_id\": \"{o.obj_id}\", \"action\": \"{ep.action_key}\"}},")
                logging.warning(f"      \"loxone\": {{\"type\": \"analog\", \"range\": {{\"min\": 0, \"max\": 100}}, \"description\": \"{ep.action_key}\"}}")
                logging.warning(f"    }}")
                logging.warning("")

    logging.info("")
    logging.info("Summary:")
    logging.info(f"  Total Virtual Outputs: {len(all_endpoints)}")
    logging.info(f"  Total Virtual Inputs: {len(all_inputs)}")
    logging.info(f"  State Polling Interval: {args.state_poll_interval} seconds")
    
    if args.dry_run:
        logging.info("Dry run completed. No files written.")
        return 0

    # Generation
    info = generate_lxaddon(
        host=args.host,
        token=args.token,
        bond_id=bond_id,
        firmware=firmware,
        objs=objs,
        endpoints=all_endpoints,
        inputs=all_inputs,
        out_lxaddon_path=args.out,
        intermediate_dir=args.emit_intermediate,
        poll_interval=args.state_poll_interval
    )

    logging.info("")
    logging.info(f"Generated: {info['out']}")
    if info['intermediate_dir']:
        logging.info(f"Intermediate files: {info['intermediate_dir']}")
        
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
