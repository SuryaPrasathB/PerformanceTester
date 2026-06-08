from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class TestStepConfig:
    """
    Configuration for a single step in a test suite.
    """
    id: Optional[int] = None
    step_type: str = "" # SET_SOURCE, READ_METER, WAIT, PROMPT_USER, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    weight: float = 10.0
    estimated_duration: float = 5.0
    sequence_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "step_type": self.step_type,
            "parameters": self.parameters,
            "weight": self.weight,
            "estimated_duration": self.estimated_duration,
            "sequence_order": self.sequence_order
        }

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'TestStepConfig':
        params = row.get("parameters_json", "{}")
        if isinstance(params, str):
            params = json.loads(params)
            
        return cls(
            id=row.get("id"),
            step_type=row.get("step_type"),
            parameters=params,
            weight=float(row.get("weight", 10.0)),
            estimated_duration=float(row.get("estimated_duration", 5.0)),
            sequence_order=row.get("sequence_order", 0)
        )

@dataclass
class TestSuiteModel:
    """
    Represents a full test suite composed of multiple steps.
    """
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    steps: List[TestStepConfig] = field(default_factory=list)
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at
        }
