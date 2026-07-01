"""safety_engine -- Phase 5: the Safety & Trust red-team gate for ms-agent-app.

Wires three red-team stages (garak, AgentDojo, PyRIT) into a single CI gate that
maps findings to EU AI Act Art. 15, DORA, and FCA PS21/3 controls and emits an
auditable evidence artifact. See README.md.
"""

from .stages import ProbeResult, StageResult, run_garak, run_agentdojo, run_pyrit
from .report import SafetyReport, build_report, write_json, write_markdown
from .compliance import CONTROLS, Control
from .providers import build_target

__all__ = [
    "ProbeResult", "StageResult", "run_garak", "run_agentdojo", "run_pyrit",
    "SafetyReport", "build_report", "write_json", "write_markdown",
    "CONTROLS", "Control",
    "build_target",
]
