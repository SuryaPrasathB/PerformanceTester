import enum
import logging

class TestState(enum.Enum):
    IDLE = "IDLE"
    INIT = "INIT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    VERIFY = "VERIFY"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

class InvalidStateTransitionError(Exception):
    pass

class StateMachine:
    """
    Manages and strictly enforces state transitions for the Test Execution Engine.
    """
    
    # Define valid transitions for each state
    VALID_TRANSITIONS = {
        TestState.IDLE: [TestState.INIT],
        TestState.INIT: [TestState.RUNNING, TestState.ERROR],
        TestState.RUNNING: [TestState.PAUSED, TestState.VERIFY, TestState.ERROR],
        TestState.PAUSED: [TestState.RUNNING, TestState.ERROR, TestState.IDLE], # IDLE allows cancelling
        TestState.VERIFY: [TestState.COMPLETE, TestState.ERROR],
        TestState.COMPLETE: [TestState.IDLE],
        TestState.ERROR: [TestState.IDLE]
    }

    def __init__(self):
        self._state = TestState.IDLE
        self.logger = logging.getLogger(__name__)

    def get_state(self) -> TestState:
        """Returns the current state."""
        return self._state

    def validate_transition(self, new_state: TestState) -> bool:
        """
        Validates whether transitioning to new_state is allowed from the current state.
        """
        return new_state in self.VALID_TRANSITIONS[self._state]

    def set_state(self, new_state: TestState):
        """
        Attempts to transition to a new state.
        Raises InvalidStateTransitionError if the transition is invalid.
        """
        if not self.validate_transition(new_state):
            error_msg = f"Invalid state transition from {self._state.name} to {new_state.name}"
            self.logger.error(error_msg)
            raise InvalidStateTransitionError(error_msg)
            
        self.logger.info(f"State transitioned: {self._state.name} -> {new_state.name}")
        self._state = new_state
