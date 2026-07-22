"""
Explicit registry of all test suite definitions.

In a frozen PyInstaller build, filesystem-based auto-discovery (scanning for .py files)
does not work because modules are compiled to bytecode inside the archive. This registry
provides a reliable, static list of all available test classes.

To add a new test suite:
  1. Create your test class in core/test_definitions/ extending BaseTest
  2. Import it below
  3. Append it to the REGISTERED_TESTS list
"""

from core.test_definitions.g2_normal_operation import G2NormalOperationTest
from core.test_definitions.g3_electrical_endurance import G3ElectricalEnduranceTest
from core.test_definitions.g5_fault_current_making import G5FaultCurrentMakingTest
from core.test_definitions.g6_short_circuit_current import G6ShortCircuitCurrentTest
from core.test_definitions.g7_minimum_switched_current import G7MinimumSwitchedCurrentTest
from core.test_definitions.manual_prospective_current import ManualProspectiveCurrentTest

REGISTERED_TESTS = [
    G2NormalOperationTest,
    G3ElectricalEnduranceTest,
    G5FaultCurrentMakingTest,
    G6ShortCircuitCurrentTest,
    G7MinimumSwitchedCurrentTest,
    ManualProspectiveCurrentTest,
]
