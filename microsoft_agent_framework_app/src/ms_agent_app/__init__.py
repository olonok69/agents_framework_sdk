"""Top-level package for the ms-agent-app demo application.

The package provides:
- chat runtime with pluggable model providers
- optional local MCP finance tooling
- evaluation and red-team workflows

It also applies targeted warning filters for known noisy experimental warnings
emitted by upstream `agent_framework` internals.
"""

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
