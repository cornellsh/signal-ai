# src/signal_assistant/enclave/serialization.py

import json
import base64
from typing import Any, Dict

# Marker to identify base64 encoded strings within JSON
BASE64_MARKER = "__base64__:"

class CommandSerializer:
    """
    Handles serialization and deserialization of commands between host and enclave.
    Uses JSON for simplicity, but acknowledges that more efficient formats
    like MessagePack or Protocol Buffers would be used in production.
    Handles bytes objects by encoding them to base64 strings with a special marker.
    """

    @staticmethod
    def _json_serial_encoder(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, bytes):
            return BASE64_MARKER + base64.b64encode(obj).decode('utf-8')
        # Allow default JSON encoder to handle other types or raise TypeError
        return obj # This line was missing or implicitly raising TypeError before

    @staticmethod
    def serialize(command: str, payload: Dict[str, Any]) -> bytes:
        """
        Serializes a command and its payload into a JSON bytes string.
        Bytes objects in the payload are base64 encoded.
        """
        data = {"command": command, "payload": payload}
        # Use custom encoder to handle bytes
        return json.dumps(data, default=CommandSerializer._json_serial_encoder).encode('utf-8')

    @staticmethod
    def _decode_hook(obj):
        """
        Hook for json.loads to decode base64 strings back to bytes,
        and recursively process dictionaries and lists.
        """
        if isinstance(obj, dict):
            return {k: CommandSerializer._decode_hook(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [CommandSerializer._decode_hook(elem) for elem in obj]
        elif isinstance(obj, str) and obj.startswith(BASE64_MARKER):
            return base64.b64decode(obj[len(BASE64_MARKER):])
        return obj

    @staticmethod
    def deserialize(data: bytes) -> Dict[str, Any]:
        """
        Deserializes a JSON bytes string into a command and its payload.
        Base64 encoded strings are decoded back to bytes.
        """
        decoded_data = json.loads(data.decode('utf-8'), object_hook=CommandSerializer._decode_hook)
        if not isinstance(decoded_data, dict) or "command" not in decoded_data or "payload" not in decoded_data:
            raise ValueError("Invalid command format")
        return decoded_data
