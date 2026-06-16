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
        
        # Dynamically infer test_identifier from concrete class name
        class_name = self.__class__.__name__.lower()
        if "g2" in class_name:
            self.test_identifier = "g2"
        elif "g3" in class_name:
            self.test_identifier = "g3"
        elif "g5" in class_name:
            self.test_identifier = "g5"
        elif "g6" in class_name:
            self.test_identifier = "g6"
        elif "g7" in class_name:
            self.test_identifier = "g7"
        else:
            self.test_identifier = "unknown"
            
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
        Cleans up resources, disconnects if necessary, and resets environment/hardware to stable state.
        This must be called even if the test fails.
        """
        hw = context.hardware_service
        if hw:
            context.logger.info("BaseTest: Performing proper closure/cleanup. Disabling ACB, SCR and Load Controller...")
            try:
                from core.hardware_mapping import PLCCoil
                
                # Turn OFF ACB and SCR coils
                if hasattr(hw, "plc") and hw.plc:
                    try:
                        hw.plc.write_coil(PLCCoil.ACB_COIL_ADDR.value, False)
                        context.logger.info("BaseTest Cleanup: ACB coil set to OFF")
                    except Exception as e:
                        context.logger.error(f"Failed to turn OFF ACB coil during cleanup: {e}")
                        
                    try:
                        hw.plc.write_coil(PLCCoil.SCR_COIL_ADDR.value, False)
                        context.logger.info("BaseTest Cleanup: SCR coil set to OFF")
                    except Exception as e:
                        context.logger.error(f"Failed to turn OFF SCR coil during cleanup: {e}")

                    try:
                        hw.plc.write_coil(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR.value, False)
                        context.logger.info("BaseTest Cleanup: 120A Contactor coil set to OFF")
                    except Exception as e:
                        context.logger.error(f"Failed to turn OFF 120A contactor coil during cleanup: {e}")

                    try:
                        hw.plc.write_coil(PLCCoil.CONTACTOR_100mA_LOAD_BANK_COIL_ADDR.value, False)
                        context.logger.info("BaseTest Cleanup: 100mA Contactor coil set to OFF")
                    except Exception as e:
                        context.logger.error(f"Failed to turn OFF 100mA contactor coil during cleanup: {e}")
                
                # Turn OFF load controller
                if hasattr(hw, "control_load"):
                    try:
                        hw.control_load(False)
                        context.logger.info("BaseTest Cleanup: Load set to OFF")
                    except Exception as e:
                        context.logger.error(f"Failed to turn OFF load during cleanup: {e}")
            except Exception as e:
                context.logger.error(f"Error during base cleanup: {e}")