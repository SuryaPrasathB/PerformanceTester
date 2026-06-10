from dataclasses import dataclass

@dataclass
class TestStep:
    """
    Metadata defining a single phase of a test.
    """
    name: str
    weight: float = 10.0           # Relative importance (for % calculation)
    estimated_duration: float = 5.0 # Seconds (for flow speed)
    requires_input: bool = False   # True if this step waits for user
    details: str = ""              # Extra context for the UI (like prompt message)
    device: str = ""               # Hardware or software device involved
