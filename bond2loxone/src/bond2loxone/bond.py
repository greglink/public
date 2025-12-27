from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import requests
import logging

logger = logging.getLogger(__name__)

@dataclass
class BondObject:
    kind: str  # DEVICE or GROUP
    obj_id: str
    name: str
    obj_type: str
    location: str
    actions_raw: Any
    members: List[str]
    raw: Dict[str, Any]
    state: Dict[str, Any]
    properties: Dict[str, Any]

def is_hex(s: str) -> bool:
    try:
        int(s, 16)
        return True
    except Exception:
        return False

def looks_like_id(k: str) -> bool:
    return len(k) >= 8 and is_hex(k)

def _get(base: str, path: str, token: str, timeout: float) -> Dict[str, Any]:
    url = f"{base}{path}"
    logger.debug(f"GET {url}")
    r = requests.get(
        url,
        headers={"Content-Type": "application/json"},
        json={"_token": token},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()

def get_sys_version(base: str, token: str, timeout: float) -> Dict[str, Any]:
    return _get(base, "/v2/sys/version", token, timeout)

def get_index(base: str, kind: str, token: str, timeout: float) -> Dict[str, Any]:
    path = "/v2/devices" if kind == "DEVICE" else "/v2/groups"
    return _get(base, path, token, timeout)

def get_object(base: str, kind: str, obj_id: str, token: str, timeout: float) -> Dict[str, Any]:
    path = f"/v2/{'devices' if kind == 'DEVICE' else 'groups'}/{obj_id}"
    return _get(base, path, token, timeout)

def get_state(base: str, kind: str, obj_id: str, token: str, timeout: float) -> Dict[str, Any]:
    path = f"/v2/{'devices' if kind == 'DEVICE' else 'groups'}/{obj_id}/state"
    try:
        return _get(base, path, token, timeout)
    except Exception as e:
        logger.debug(f"Failed to get state for {kind} {obj_id}: {e}")
        return {}

def get_properties(base: str, kind: str, obj_id: str, token: str, timeout: float) -> Dict[str, Any]:
    path = f"/v2/{'devices' if kind == 'DEVICE' else 'groups'}/{obj_id}/properties"
    try:
        return _get(base, path, token, timeout)
    except Exception as e:
        logger.debug(f"Failed to get properties for {kind} {obj_id}: {e}")
        return {}

def extract_actions(j: Dict[str, Any]) -> Any:
    return j.get("actions")

def extract_members(j: Dict[str, Any]) -> List[str]:
    m = j.get("devices")
    if isinstance(m, list):
        return [str(x) for x in m]
    return []

def iter_action_items(actions_raw: Any) -> List[tuple[str, Any]]:
    if isinstance(actions_raw, dict):
        return [(str(k), v) for k, v in actions_raw.items()]
    if isinstance(actions_raw, list):
        return [(str(x), None) for x in actions_raw]
    return []
