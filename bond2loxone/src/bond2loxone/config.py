from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.mappings = data.get("mappings", [])
        self.overrides = data.get("overrides", [])
        self.state_mappings = data.get("state_mappings", [])
        self.global_settings = data.get("global_settings", {})

    @classmethod
    def load(cls, path: Optional[str]) -> Config:
        if not path:
            return cls({})
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Loaded configuration from {path}")
                return cls(data)
        except Exception as e:
            logger.error(f"Failed to load configuration from {path}: {e}")
            return cls({})

    def get_mapping(self, device_type: str, action: str) -> Optional[Dict[str, Any]]:
        for m in self.mappings:
            match = m.get("match", {})
            
            # Check action match
            if match.get("action") != action:
                continue
            
            # Check device_type match (if specified in config)
            if "device_type" in match and match["device_type"] != device_type:
                continue
                
            # Match found
            result = m.get("loxone", {}).copy()
            if m.get("ignore"):
                result["ignore"] = True
            return result
        return None

    def get_override(self, device_id: str, action: str) -> Optional[Dict[str, Any]]:
        for o in self.overrides:
            match = o.get("match", {})
            
            # Check action match
            if match.get("action") != action:
                continue
                
            # Check device_id match
            if match.get("device_id") != device_id:
                continue
                
            # Match found
            result = o.get("loxone", {}).copy()
            if o.get("ignore"):
                result["ignore"] = True
            return result
        return None

    def get_state_mapping(self, device_type: str, state_key: str) -> Optional[Dict[str, Any]]:
        for m in self.state_mappings:
            match = m.get("match", {})
            
            # Check state_key match
            if match.get("state_key") != state_key:
                continue
                
            # Check device_type match (if specified)
            if "device_type" in match and match["device_type"] != device_type:
                continue
                
            # Match found
            result = m.get("loxone", {}).copy()
            if m.get("ignore"):
                result["ignore"] = True
            return result
        return None
    
    def get_state_override(self, device_id: str, state_key: str) -> Optional[Dict[str, Any]]:
        # Check overrides for state mappings too (using state_key in match)
        for o in self.overrides:
            match = o.get("match", {})
            
            # Check state_key match
            if match.get("state_key") != state_key:
                continue
                
            # Check device_id match
            if match.get("device_id") != device_id:
                continue
                
            # Match found
            result = o.get("loxone", {}).copy()
            if o.get("ignore"):
                result["ignore"] = True
            return result
        return None
