"""
backend/app/ast/dag_crawler.py
==============================
Autonomous Static Dependency Crawler for VECTIS
IBM Bob 2.0 Hackathon -- Autonomous Release Safety

Scans real TypeScript/JavaScript monorepos, parses ES module import declarations,
resolves target file paths and aliases (@/), and constructs a directed NetworkX
dependency DAG (producer_file -> consumer_file).
Includes heuristic node metadata calculation and seamless fallback to sample topology.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import networkx as nx

# Extensions to discover
SUPPORTED_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx")

# Candidate extensions for resolution
CANDIDATE_EXTENSIONS = [
    "",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    "/index.ts",
    "/index.tsx",
    "/index.js",
    "/index.jsx",
]

# Directories ignored during traversal
IGNORED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    ".bob",
    "__pycache__",
    ".next",
    ".turbo",
    "coverage",
    ".pytest_cache",
    ".venv",
    "venv",
    ".output",
    "out",
}

# Regex patterns for ES module and dynamic imports
IMPORT_PATTERNS = [
    re.compile(r"""(?:import|export)\s+(?:(?:[\w*\s{},$]+from\s+)?['"]([^'"]+)['"])"""),
    re.compile(r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
]


def normalize_posix_path(path_str: str) -> str:
    """Normalize path separators to forward slashes and strip redundant prefixes."""
    normalized = path_str.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


class DynamicWorkspaceCrawler:
    """
    Autonomous Static Dependency Crawler for TypeScript/JavaScript codebases.
    Constructs a directed NetworkX graph where edges flow:
        producer_file -> consumer_file
    representing data and contract dependencies.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.getcwd()

    def crawl_workspace(self, workspace_root: Optional[str] = None) -> nx.DiGraph:
        """
        Walks workspace directories (ignoring node_modules, .git, dist, build, etc.),
        finds .ts, .tsx, .js, .jsx files, extracts imports, resolves targets,
        and constructs the directed NetworkX graph with heuristic node metadata.
        """
        root = os.path.abspath(workspace_root or self.workspace_root)
        graph = nx.DiGraph()

        if not os.path.isdir(root):
            return graph

        discovered_files: List[str] = []

        # 1. Walk directories and find source files
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune ignored directories in-place
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]

            for filename in filenames:
                if filename.endswith(SUPPORTED_EXTENSIONS) and not filename.endswith(".d.ts"):
                    full_path = os.path.join(dirpath, filename)
                    discovered_files.append(full_path)

        if not discovered_files:
            return graph

        # 2. Add all discovered files as nodes with heuristic metadata
        file_node_map: Dict[str, str] = {}  # full_path -> relative_posix_path
        for full_path in discovered_files:
            rel_path = normalize_posix_path(os.path.relpath(full_path, root))
            file_node_map[full_path] = rel_path
            meta = self._assign_heuristic_metadata(rel_path)
            graph.add_node(
                rel_path,
                label=rel_path,
                criticality=meta["criticality"],
                traffic=meta["traffic"],
                traffic_weight=meta["traffic"],
                service=meta["service"],
            )

        # 3. Parse imports from each file and resolve dependencies
        for consumer_full_path in discovered_files:
            consumer_node = file_node_map[consumer_full_path]
            try:
                with open(consumer_full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            import_specifiers = self._extract_import_specifiers(content)

            for spec in import_specifiers:
                producer_full_path = self._resolve_import(
                    specifier=spec,
                    importer_path=consumer_full_path,
                    workspace_root=root,
                )
                if producer_full_path and producer_full_path in file_node_map:
                    producer_node = file_node_map[producer_full_path]
                    if producer_node != consumer_node:
                        # Edge: producer -> consumer (breaking change in producer impacts consumer)
                        graph.add_edge(producer_node, consumer_node)

        return graph

    def merge_with_fallback(self, crawled_graph: nx.DiGraph) -> nx.DiGraph:
        """
        Integrates crawled graph with fallback logic:
        Falls back to standard enterprise 7-node topology if workspace is empty
        or has only a single file.
        """
        if crawled_graph is None or crawled_graph.number_of_nodes() <= 1:
            return self.build_sample_topology()
        return crawled_graph

    def build_sample_topology(self) -> nx.DiGraph:
        """Produces the canonical 7-node fintech topology fixture."""
        graph = nx.DiGraph()
        nodes = [
            ("models/user.ts", {"label": "models/user.ts", "criticality": 1.0, "traffic": 0.8, "traffic_weight": 0.8, "service": "Identity Core"}),
            ("auth/session.ts", {"label": "auth/session.ts", "criticality": 0.95, "traffic": 0.9, "traffic_weight": 0.9, "service": "Auth Gateway"}),
            ("payments/checkout.ts", {"label": "payments/checkout.ts", "criticality": 1.0, "traffic": 1.0, "traffic_weight": 1.0, "service": "Billing & Checkout"}),
            ("workers/settlement_worker.ts", {"label": "workers/settlement_worker.ts", "criticality": 0.85, "traffic": 0.6, "traffic_weight": 0.6, "service": "Settlement Cron"}),
            ("reporting/invoice_generator.ts", {"label": "reporting/invoice_generator.ts", "criticality": 0.7, "traffic": 0.3, "traffic_weight": 0.3, "service": "Invoicing"}),
            ("api/routes/user_profile.ts", {"label": "api/routes/user_profile.ts", "criticality": 0.5, "traffic": 0.7, "traffic_weight": 0.7, "service": "Public API"}),
            ("api/routes/admin_dashboard.ts", {"label": "api/routes/admin_dashboard.ts", "criticality": 0.6, "traffic": 0.4, "traffic_weight": 0.4, "service": "Internal Ops"}),
        ]
        for node_id, meta in nodes:
            graph.add_node(node_id, **meta)

        edges = [
            ("models/user.ts", "auth/session.ts"),
            ("auth/session.ts", "payments/checkout.ts"),
            ("auth/session.ts", "workers/settlement_worker.ts"),
            ("payments/checkout.ts", "reporting/invoice_generator.ts"),
            ("auth/session.ts", "api/routes/user_profile.ts"),
            ("models/user.ts", "api/routes/admin_dashboard.ts"),
        ]
        graph.add_edges_from(edges)
        return graph

    def _extract_import_specifiers(self, source_code: str) -> List[str]:
        """Extracts relative and alias import specifiers from file content."""
        specifiers: Set[str] = set()
        for pattern in IMPORT_PATTERNS:
            for match in pattern.finditer(source_code):
                spec = match.group(1).strip()
                # Only include local relative and alias paths
                if spec.startswith(("./", "../", "@/")) or (spec.startswith("@") and "/" in spec):
                    specifiers.add(spec)
        return list(specifiers)

    def _resolve_import(
        self, specifier: str, importer_path: str, workspace_root: str
    ) -> Optional[str]:
        """
        Resolves an import specifier to an absolute file path on disk.
        Supports:
          - Relative imports: `./foo`, `../bar/baz`
          - Alias imports: `@/components/Button` -> `src/components/Button` or root
        """
        candidate_bases: List[str] = []

        if specifier.startswith(("./", "../")):
            importer_dir = os.path.dirname(importer_path)
            candidate_bases.append(os.path.normpath(os.path.join(importer_dir, specifier)))

        elif specifier.startswith("@/"):
            rel_alias = specifier[2:]
            # Priority 1: workspace_root/src/<path>
            candidate_bases.append(os.path.normpath(os.path.join(workspace_root, "src", rel_alias)))
            # Priority 2: workspace_root/<path>
            candidate_bases.append(os.path.normpath(os.path.join(workspace_root, rel_alias)))

        elif specifier.startswith("@") and "/" in specifier:
            # e.g., @components/Button
            parts = specifier.split("/", 1)
            if len(parts) == 2:
                alias_name, rest = parts
                candidate_bases.append(os.path.normpath(os.path.join(workspace_root, "src", rest)))
                candidate_bases.append(os.path.normpath(os.path.join(workspace_root, rest)))

        for base in candidate_bases:
            for ext in CANDIDATE_EXTENSIONS:
                candidate_file = base + ext
                if os.path.isfile(candidate_file):
                    return os.path.abspath(candidate_file)

        return None

    def _assign_heuristic_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Auto-assigns heuristic metadata based on naming and directory context.
        Files with auth, payment, checkout, session -> criticality 0.9, traffic 0.85
        Utility/helper files -> criticality 0.4, traffic 0.5
        """
        lower = file_path.lower()

        if any(k in lower for k in ("auth", "payment", "checkout", "session", "billing", "token")):
            return {
                "criticality": 0.9,
                "traffic": 0.85,
                "service": "Auth & Payment Gateway",
            }
        elif any(k in lower for k in ("util", "helper", "common", "tool", "shared", "lib")):
            return {
                "criticality": 0.4,
                "traffic": 0.5,
                "service": "Utility & Helpers",
            }
        elif any(k in lower for k in ("model", "schema", "entity", "user", "type")):
            return {
                "criticality": 1.0,
                "traffic": 0.8,
                "service": "Core Data Models",
            }
        elif any(k in lower for k in ("worker", "settlement", "cron", "job", "queue")):
            return {
                "criticality": 0.85,
                "traffic": 0.6,
                "service": "Background Worker",
            }
        elif any(k in lower for k in ("route", "api", "controller", "endpoint", "handler")):
            return {
                "criticality": 0.6,
                "traffic": 0.7,
                "service": "Public API",
            }
        else:
            return {
                "criticality": 0.6,
                "traffic": 0.6,
                "service": "Application Module",
            }
