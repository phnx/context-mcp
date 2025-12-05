# independent counter class for tool usage
import json
from pathlib import Path
from typing import Dict, Any

from filelock import FileLock

COUNTER_FILE = "database/tool_analytic.json"


class ToolCounter:
    """Thread-safe counter with file locking."""

    def __init__(self):
        """
        Initialize counter.

        Args:
            json_file: Path to JSON counter file
        """
        self.json_file = Path(COUNTER_FILE)
        self.lock_file = Path(f"{COUNTER_FILE}.lock")
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create JSON file if it doesn't exist."""
        if not self.json_file.exists():
            self.json_file.write_text(json.dumps({}))

    def _read(self) -> Dict[str, Any]:
        """Read JSON file safely."""
        try:
            return json.loads(self.json_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write(self, data: Dict[str, Any]) -> None:
        """Write JSON file atomically."""
        temp_file = Path(f"{self.json_file}.tmp")
        temp_file.write_text(json.dumps(data, indent=2))
        temp_file.replace(self.json_file)

    def increment_tool(
        self, tool_name: str, calls: int = 1, tokens_in: int = 0, tokens_out: int = 0
    ) -> Dict[str, int]:
        """
        Increment tool call count and tokens.

        Args:
            tool_name: Name of the tool
            calls: Number of calls to add (default: 1)
            tokens_in: Input tokens to add
            tokens_out: Output tokens to add

        Returns:
            Updated tool stats
        """
        lock = FileLock(str(self.lock_file), timeout=10)

        with lock:
            data = self._read()

            # Initialize tool if not exists
            if tool_name not in data:
                data[tool_name] = {
                    "calls": 0,
                    "tokens_in": 0,
                    "tokens_out": 0,
                }

            # Increment values
            data[tool_name]["calls"] += calls
            data[tool_name]["tokens_in"] += tokens_in
            data[tool_name]["tokens_out"] += tokens_out

            self._write(data)

            return data[tool_name]

    def get_tool_stats(self, tool_name: str) -> Dict[str, int]:
        """Get stats for a specific tool."""
        lock = FileLock(str(self.lock_file), timeout=10)

        with lock:
            data = self._read()
            return data.get(
                tool_name,
                {
                    "calls": 0,
                    "tokens_in": 0,
                    "tokens_out": 0,
                },
            )

    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        """Get stats for all tools."""
        lock = FileLock(str(self.lock_file), timeout=10)

        with lock:
            return self._read()

    def reset_tool(self, tool_name: str) -> None:
        """Reset stats for a tool."""
        lock = FileLock(str(self.lock_file), timeout=10)

        with lock:
            data = self._read()
            if tool_name in data:
                data[tool_name] = {
                    "calls": 0,
                    "tokens_in": 0,
                    "tokens_out": 0,
                }
                self._write(data)
