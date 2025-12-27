from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .bond import BondObject, iter_action_items
from .config import Config
from .builtin_mappings import BUILTIN_MAPPINGS, BUILTIN_STATE_MAPPINGS

logger = logging.getLogger(__name__)

@dataclass
class LoxoneEndpoint:
    kind: str  # DEVICE or GROUP
    obj_id: str
    obj_name: str
    obj_location: str
    action_key: str           # as in Bond
    action_canon: str         # endpoint name suffix
    
    # Loxone properties
    type: str                 # digital, analog, text
    description: str
    unit: Optional[str] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    invert: bool = False
    
    # For unknown actions
    is_unknown: bool = False
    unknown_test_type: Optional[str] = None # "digital" or "analog"

@dataclass
class LoxoneInput:
    kind: str
    obj_id: str
    obj_name: str
    obj_location: str
    state_key: str
    
    type: str
    description: str
    unit: Optional[str] = None
    poll_interval: int = 30

class Mapper:
    def __init__(self, config: Config):
        self.config = config

    def map_object(self, obj: BondObject) -> Tuple[List[LoxoneEndpoint], List[LoxoneInput]]:
        endpoints = []
        inputs = []
        
        # Map Actions -> Virtual Outputs
        for action_key, action_meta in iter_action_items(obj.actions_raw):
            # Check for overrides first
            mapping = self.config.get_override(obj.obj_id, action_key)
            
            # Then check config mappings
            if not mapping:
                mapping = self.config.get_mapping(obj.obj_type, action_key)
                
            # Then check built-ins
            if not mapping:
                for m in BUILTIN_MAPPINGS:
                    match = m.get("match", {})
                    if match.get("device_type") == obj.obj_type and match.get("action") == action_key:
                        mapping = m.get("loxone")
                        break
            
            if mapping:
                if mapping.get("ignore"):
                    continue
                ep = self._create_endpoint(obj, action_key, mapping)
                endpoints.append(ep)
            else:
                # Unknown action - generate test cases
                logger.warning(f"Unknown action '{action_key}' for {obj.kind} {obj.obj_id} ({obj.obj_type})")
                
                # Test case A: Digital
                ep_dig = self._create_endpoint(obj, action_key, {"type": "digital", "description": f"Unknown Action {action_key} (Digital Test)"})
                ep_dig.is_unknown = True
                ep_dig.unknown_test_type = "digital"
                ep_dig.action_canon = f"{ep_dig.action_canon}_digital"
                endpoints.append(ep_dig)
                
                # Test case B: Analog
                ep_ana = self._create_endpoint(obj, action_key, {"type": "analog", "range": {"min": 0, "max": 100}, "description": f"Unknown Action {action_key} (Analog Test)"})
                ep_ana.is_unknown = True
                ep_ana.unknown_test_type = "analog"
                ep_ana.action_canon = f"{ep_ana.action_canon}_analog"
                endpoints.append(ep_ana)

        # Map State -> Virtual Inputs
        if obj.state:
            for key, value in obj.state.items():
                if key == "_": continue
                
                # Check overrides
                mapping = self.config.get_state_override(obj.obj_id, key)
                
                # Check config mappings
                if not mapping:
                    mapping = self.config.get_state_mapping(obj.obj_type, key)
                    
                # Check built-ins
                if not mapping:
                    for m in BUILTIN_STATE_MAPPINGS:
                        match = m.get("match", {})
                        if match.get("device_type") == obj.obj_type and match.get("state_key") == key:
                            mapping = m.get("loxone")
                            break
                
                # Default fallback if readable state but no mapping
                if not mapping:
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                         mapping = {"type": "analog", "description": f"State {key}"}
                    else:
                         mapping = {"type": "digital" if isinstance(value, bool) or value in (0, 1) else "text", "description": f"State {key}"}

                if mapping:
                    if mapping.get("ignore"):
                        continue
                    inp = self._create_input(obj, key, mapping)
                    inputs.append(inp)

        return endpoints, inputs

    def _create_endpoint(self, obj: BondObject, action_key: str, mapping: Dict[str, Any]) -> LoxoneEndpoint:
        # Determine range
        min_val = 0
        max_val = 100
        
        if mapping.get("type") == "analog":
            rng = mapping.get("range", {})
            min_val = rng.get("min", 0)
            max_val = rng.get("max", 100)
            
            # Query device properties if requested
            if mapping.get("query_device_range"):
                if action_key == "SetSpeed" and "max_speed" in obj.properties:
                    max_val = obj.properties["max_speed"]
                    min_val = 1
                # Add other property queries here as needed

        return LoxoneEndpoint(
            kind=obj.kind,
            obj_id=obj.obj_id,
            obj_name=obj.name,
            obj_location=obj.location,
            action_key=action_key,
            action_canon=self._canon_action_name(action_key),
            type=mapping.get("type", "digital"),
            description=mapping.get("description", ""),
            unit=mapping.get("unit"),
            min_val=min_val,
            max_val=max_val,
            invert=mapping.get("invert", False)
        )

    def _create_input(self, obj: BondObject, state_key: str, mapping: Dict[str, Any]) -> LoxoneInput:
        return LoxoneInput(
            kind=obj.kind,
            obj_id=obj.obj_id,
            obj_name=obj.name,
            obj_location=obj.location,
            state_key=state_key,
            type=mapping.get("type", "text"),
            description=mapping.get("description", ""),
            unit=mapping.get("unit"),
            poll_interval=mapping.get("poll_interval", 30)
        )

    def _canon_action_name(self, action: str) -> str:
        import re
        s = str(action).strip()
        if not s: return s
        # If already mixed-case, trust it.
        if any(c.isupper() for c in s):
            return s
        # Split on non-alnum and TitleCase parts
        parts = re.split(r"[^0-9A-Za-z]+", s)
        parts = [p for p in parts if p]
        if not parts:
            return s[:1].upper() + s[1:]
        return "".join(p[:1].upper() + p[1:].lower() for p in parts)
