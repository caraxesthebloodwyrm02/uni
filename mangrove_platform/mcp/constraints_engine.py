import os
import re


class ConstraintsEngine:
    """
    Engine for discovering systemic constraints and rules across the codebase.
    Uses a tiered regex strategy to identify textual, programmatic, and numerical constraints.
    """

    # Regex patterns for different types of constraints
    PATTERNS = {
        "natural_language": re.compile(
            r"(?i)(must|should|shall|require|constraint|limit|forbidden|denied|block)\s+[^.?!]*[.?!]"
        ),
        "programmatic": re.compile(
            r"re\.(match|search|compile)\s*\(\s*r?(['\"])(.*?)\2", re.DOTALL
        ),
        "numerical": re.compile(r"(?i)(THRESHOLD|LIMIT|MAX|MIN)\s*=\s*[^#\n]+"),
    }

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def search(self, query: str | None = None) -> list[dict]:
        """
        Search for constraints across the root directory.
        If a query is provided, it acts as a filter on the findings.
        """
        results = []

        # Walk through the directory
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith((".py", ".md", ".txt")):
                    file_path = os.path.join(root, file)
                    findings = self._scan_file(file_path)
                    results.extend(findings)

        # If query is provided, filter the results
        if query:
            try:
                filter_re = re.compile(query, re.IGNORECASE)
                results = [r for r in results if filter_re.search(r["content"])]
            except re.error:
                # If invalid regex provided, return empty or treat as literal search
                results = [r for r in results if query.lower() in r["content"].lower()]

        return results

    def _scan_file(self, file_path: str) -> list[dict]:
        """Scans a single file for constraint patterns."""
        findings = []
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                for category, pattern in self.PATTERNS.items():
                    if pattern.search(stripped_line):
                        findings.append(
                            {
                                "file": os.path.relpath(file_path, self.root_dir),
                                "line": i + 1,
                                "content": stripped_line,
                                "category": category,
                            }
                        )
        except (UnicodeDecodeError, PermissionError):
            pass

        return findings
