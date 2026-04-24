from abc import ABC, abstractmethod
from typing import List
from core.test_engine.test_step import TestStep

class BaseTest(ABC):
    """
    Abstract base class for all test definitions.
    Defines the structure that tests must follow.
    """

    def get_steps(self) -> List[TestStep]:
        """ Returns a list of TestStep metadata objects defining the test sequence. """
        return []

    @abstractmethod
    def setup(self, context):
        """ Prepare test environment, initalize devices, set up test parameters """
        pass

    @abstractmethod
    def run(self, context):
        """ Execute core test logic. Check pause/cancel events from context periodically """
        pass

    @abstractmethod
    def verify(self, context):
        """ Verify the results of the test run, perform checks against expected values """
        pass

    @abstractmethod
    def cleanup(self, context):
        """ 
        Clean up resources, disconnect if necessary, reset environment to stable state.
        This must be called even if the test fails.
        """
        pass