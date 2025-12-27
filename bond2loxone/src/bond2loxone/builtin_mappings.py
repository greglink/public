from __future__ import annotations

from typing import Any, Dict, List

# Built-in mappings for common device types
BUILTIN_MAPPINGS = [
    # Motorized Shades (MS)
    {
        "match": {"device_type": "MS", "action": "Open"},
        "loxone": {"type": "digital", "description": "Open shade"}
    },
    {
        "match": {"device_type": "MS", "action": "Close"},
        "loxone": {"type": "digital", "description": "Close shade"}
    },
    {
        "match": {"device_type": "MS", "action": "Stop"},
        "loxone": {"type": "digital", "description": "Stop shade"}
    },
    {
        "match": {"device_type": "MS", "action": "Hold"},
        "loxone": {"type": "digital", "description": "Hold shade"}
    },
    {
        "match": {"device_type": "MS", "action": "Preset"},
        "loxone": {"type": "digital", "description": "Go to preset"}
    },
    {
        "match": {"device_type": "MS", "action": "SetPosition"},
        "loxone": {
            "type": "analog", 
            "range": {"min": 0, "max": 100}, 
            "unit": "%", 
            "description": "Set position (0=open, 100=closed)",
            "query_device_range": True
        }
    },
    
    # Ceiling Fans (CF)
    {
        "match": {"device_type": "CF", "action": "TurnOn"},
        "loxone": {"type": "digital", "description": "Turn fan on"}
    },
    {
        "match": {"device_type": "CF", "action": "TurnOff"},
        "loxone": {"type": "digital", "description": "Turn fan off"}
    },
    {
        "match": {"device_type": "CF", "action": "SetSpeed"},
        "loxone": {
            "type": "analog", 
            "range": {"min": 1, "max": 3}, # Default, usually overridden by max_speed property
            "description": "Set fan speed",
            "query_device_range": True
        }
    },
    {
        "match": {"device_type": "CF", "action": "IncreaseSpeed"},
        "loxone": {"type": "digital", "description": "Increase speed"}
    },
    {
        "match": {"device_type": "CF", "action": "DecreaseSpeed"},
        "loxone": {"type": "digital", "description": "Decrease speed"}
    },

    # Lights (LT)
    {
        "match": {"device_type": "LT", "action": "TurnLightOn"},
        "loxone": {"type": "digital", "description": "Turn light on"}
    },
    {
        "match": {"device_type": "LT", "action": "TurnLightOff"},
        "loxone": {"type": "digital", "description": "Turn light off"}
    },
    {
        "match": {"device_type": "LT", "action": "SetBrightness"},
        "loxone": {
            "type": "analog", 
            "range": {"min": 1, "max": 100}, 
            "unit": "%", 
            "description": "Set brightness"
        }
    },

    # Fireplaces (FP)
    {
        "match": {"device_type": "FP", "action": "TurnOn"},
        "loxone": {"type": "digital", "description": "Turn fireplace on"}
    },
    {
        "match": {"device_type": "FP", "action": "TurnOff"},
        "loxone": {"type": "digital", "description": "Turn fireplace off"}
    },
    {
        "match": {"device_type": "FP", "action": "SetFlame"},
        "loxone": {
            "type": "analog", 
            "range": {"min": 1, "max": 100}, 
            "description": "Set flame level"
        }
    }
]

# Default state mappings
BUILTIN_STATE_MAPPINGS = [
    {
        "match": {"device_type": "MS", "state_key": "open"},
        "loxone": {"type": "digital", "description": "Shade open state"}
    },
    {
        "match": {"device_type": "MS", "state_key": "position"},
        "loxone": {"type": "analog", "unit": "%", "description": "Shade position state"}
    },
    {
        "match": {"device_type": "CF", "state_key": "power"},
        "loxone": {"type": "digital", "description": "Fan power state"}
    },
    {
        "match": {"device_type": "CF", "state_key": "speed"},
        "loxone": {"type": "analog", "description": "Fan speed state"}
    },
    {
        "match": {"device_type": "LT", "state_key": "light"},
        "loxone": {"type": "digital", "description": "Light power state"}
    },
    {
        "match": {"device_type": "LT", "state_key": "brightness"},
        "loxone": {"type": "analog", "unit": "%", "description": "Light brightness state"}
    },
    {
        "match": {"device_type": "FP", "state_key": "power"},
        "loxone": {"type": "digital", "description": "Fireplace power state"}
    },
    {
        "match": {"device_type": "FP", "state_key": "flame"},
        "loxone": {"type": "analog", "description": "Fireplace flame state"}
    }
]
