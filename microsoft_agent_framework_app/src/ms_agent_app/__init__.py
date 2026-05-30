"""Microsoft Agent Framework demo: Foundry agent + local MCP tools + Azure AI Evaluation."""

from __future__ import annotations

import warnings

# Keep warnings output readable by filtering two known noisy experimental notices
# from upstream agent_framework internals.
warnings.filterwarnings(
	"ignore",
	message=r".*\[SKILLS\] SkillResource is experimental.*",
	category=Warning,
	module=r"agent_framework\._skills",
)
warnings.filterwarnings(
	"ignore",
	message=r".*\[HARNESS\] MemoryStore is experimental.*",
	category=Warning,
	module=r"agent_framework\._harness\._memory",
)
