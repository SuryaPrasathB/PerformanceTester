from abc import ABC, abstractmethod
from typing import List
from core.test_engine.test_step import TestStep
from core.test_engine.test_builder import TestBuilder

class BaseTest(ABC):
    """
    Abstract base class for all test definitions using the modular TestBuilder pattern.
    """

    def __init__(self):
        self._builder = TestBuilder()
        # Allows tests to define their sequence on initialization
        self.build(self._builder)

    def get_steps(self) -> List[TestStep]:
        """ Returns a list of TestStep metadata objects defining the test sequence from the builder. """
        return self._builder.get_steps()

    @abstractmethod
    def build(self, builder: TestBuilder):
        """ 
        Define the sequence of the test using the TestBuilder API.
        Example: builder.set_source(...).turn_on_load().wait(5)
        """
        pass

    def setup(self, context):
        """ Optional: Prepare test environment, initalize devices, set up test parameters """
        pass

    def run(self, context):
        """ Executes the builder sequence. """
        self._builder.execute(context)

    def verify(self, context):
        """ Optional: Verify the results of the test run, perform checks against expected values """
        pass

    def cleanup(self, context):
        """ 
        Optional: Clean up resources, disconnect if necessary, reset environment to stable state.
        This must be called even if the test fails.
        """
        pass