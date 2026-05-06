from pathlib import PurePosixPath

from multi_agent.agents.sr_dev.tools.constants import (
    SENSITIVE_FILENAME_KEYWORDS,
    SENSITIVE_FILENAME_PREFIXES,
    SENSITIVE_FILENAME_SUFFIXES,
)


def sr_dev_sensitive_path_is_blocked(path):
    filename = PurePosixPath(str(path or '')).name.lower()
    if not filename:
        return False
    if any(filename.startswith(prefix) for prefix in SENSITIVE_FILENAME_PREFIXES):
        return True
    if any(filename.endswith(suffix) for suffix in SENSITIVE_FILENAME_SUFFIXES):
        return True
    return any(keyword in filename for keyword in SENSITIVE_FILENAME_KEYWORDS)
