import json
import time
from typing import Any
from uuid import uuid4


def sse_event(event: str, payload: Any) -> dict[str, str]:
    """Build a structured dict consumed by EventSourceResponse.

    Returns {event, data} where data is a pre-serialised JSON string
    containing the AgentEvent envelope {id, timestamp, payload}.
    """
    envelope = {
        "id": str(uuid4()),
        "timestamp": int(time.time() * 1000),
        "payload": payload,
    }
    return {
        "event": event,
        "data": json.dumps(envelope, ensure_ascii=False),
    }
