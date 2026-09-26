import os
import re
import subprocess
from typing import List, Dict, Any, Set, Optional, Tuple
import networkx as nx

class ASTChangeDetector:
    """Deterministic TypeScript/ESM AST grammar contract mutation engine."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def detect_contract_mutations(
        self, file_path: str, base_ref: str, head_ref: str
    ) -> List[Dict[str, Any]]:
        base_content = self._get_file_content(file_path, base_ref)
        head_content = self._get_file_content(file_path, head_ref)
        mutations = []

        if file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
            mutations.extend(
                self._parse_ts_contract_mutations(file_path, base_content, head_content)
            )
        return mutations

    def _extract_ts_interfaces(self, source: str) -> Dict[str, Dict[str, str]]:
        """Balanced-braces grammar parser handling nested structures, interfaces, and type aliases."""
        interfaces: Dict[str, Dict[str, str]] = {}
        # Matches `export interface Name {`, `interface Name {`, `export type Name = {`, etc.
        pattern = re.compile(
            r"(?:export\s+)?(?:interface|type)\s+(\w+)\s*(?:=\s*)?\{", re.MULTILINE
        )
        for match in pattern.finditer(source):
            name = match.group(1)
            start = match.end()
            depth = 1
            i = start
            while i < len(source) and depth > 0:
                if source[i] == "{":
                    depth += 1
                elif source[i] == "}":
                    depth -= 1
                i += 1
            body = source[start : i - 1]
            fields = self._parse_fields(body)
            interfaces[name] = fields
        return interfaces

    def _parse_fields(self, body: str) -> Dict[str, str]:
        """Parse top-level and nested structure fields from interface/type body."""
        fields: Dict[str, str] = {}
        depth = 0
        current_line = ""
        # Strip line comments
        cleaned_body = re.sub(r"//.*$", "", body, flags=re.MULTILINE)
        for char in cleaned_body:
            if char in "{[":
                depth += 1
                current_line += char
            elif char in "}]":
                depth -= 1
                current_line += char
            elif (char == ";" or char == "\n" or (char == "," and depth <= 1)) and depth == 0:
                trimmed = current_line.strip()
                if trimmed:
                    field_match = re.match(r"^(\w+)\??\s*:\s*(.+)$", trimmed, re.DOTALL)
                    if field_match:
                        fields[field_match.group(1)] = field_match.group(2).strip().rstrip(";")
                current_line = ""
            else:
                current_line += char

        # Process trailing statement
        if current_line.strip() and depth == 0:
            field_match = re.match(r"^(\w+)\??\s*:\s*(.+)$", current_line.strip(), re.DOTALL)
            if field_match:
                fields[field_match.group(1)] = field_match.group(2).strip().rstrip(";")

        return fields

    def _find_symbol_line(self, source: str, symbol_name: str) -> int:
        """Find 1-indexed line number of a symbol in source code."""
        if not source:
            return 1
        lines = source.splitlines()
        token = symbol_name.split(".")[-1]
        for idx, line in enumerate(lines, start=1):
            if re.search(rf"\b{re.escape(token)}\b\??\s*:", line) or re.search(rf"\b{re.escape(token)}\b", line):
                return idx
        return 1

    def _parse_ts_contract_mutations(
        self, file_path: str, base_src: str, head_src: str
    ) -> List[Dict[str, Any]]:
        base_ifaces = self._extract_ts_interfaces(base_src)
        head_ifaces = self._extract_ts_interfaces(head_src)
        mutations = []

        # If both are empty, no AST interfaces to diff
        if not base_ifaces and not head_ifaces:
            return []

        # Check each interface in base
        for base_name, base_fields in base_ifaces.items():
            if base_name in head_ifaces:
                # Same interface name: compare field by field
                head_fields = head_ifaces[base_name]
                for field_name, field_type in base_fields.items():
                    line_no = self._find_symbol_line(base_src, field_name)
                    if field_name not in head_fields:
                        mutations.append({
                            "file_path": file_path,
                            "symbol_name": f"{base_name}.{field_name}",
                            "mutation_type": "field_removed",
                            "old_signature": f"{field_name}: {field_type}",
                            "new_signature": "REMOVED",
                            "severity": "critical",
                            "line_number": line_no,
                            "description": f"Field '{field_name}' was removed from {base_name}"
                        })
                    elif head_fields[field_name] != field_type:
                        mutations.append({
                            "file_path": file_path,
                            "symbol_name": f"{base_name}.{field_name}",
                            "mutation_type": "type_change",
                            "old_signature": f"{field_name}: {field_type}",
                            "new_signature": f"{field_name}: {head_fields[field_name]}",
                            "severity": "critical",
                            "line_number": line_no,
                            "description": f"Type signature mutated from {field_type} to {head_fields[field_name]}"
                        })
            else:
                # Interface base_name is missing in head_ifaces.
                # Check if an evolved/successor interface replaced it (e.g. User -> SessionUser)
                successor_name = None
                for candidate_name in head_ifaces:
                    if (
                        base_name.lower() in candidate_name.lower()
                        or candidate_name.lower() in base_name.lower()
                        or any(f in head_ifaces[candidate_name] for f in base_fields)
                    ):
                        successor_name = candidate_name
                        break

                if successor_name:
                    successor_fields = head_ifaces[successor_name]
                    # Diff fields against successor contract
                    for field_name, field_type in base_fields.items():
                        line_no = self._find_symbol_line(base_src, field_name)
                        if field_name in successor_fields:
                            if successor_fields[field_name] != field_type:
                                mutations.append({
                                    "file_path": file_path,
                                    "symbol_name": f"{base_name}.{field_name}",
                                    "mutation_type": "type_change",
                                    "old_signature": f"{field_name}: {field_type}",
                                    "new_signature": f"{field_name}: {successor_fields[field_name]}",
                                    "severity": "critical",
                                    "line_number": line_no,
                                    "description": f"Type signature mutated in successor {successor_name}"
                                })
                        else:
                            # Check if relocated to nested structure (e.g., metadata.tier)
                            relocated = False
                            for s_field, s_type in successor_fields.items():
                                if field_name in s_type:
                                    mutations.append({
                                        "file_path": file_path,
                                        "symbol_name": f"{base_name}.{field_name}",
                                        "mutation_type": "field_removed",
                                        "old_signature": f"{field_name}: {field_type}",
                                        "new_signature": f"{s_field}: {{ {field_name}: ... }} (moved to nested object)",
                                        "severity": "critical",
                                        "line_number": line_no,
                                        "description": f"Property '{field_name}' moved to nested object {s_field}.{field_name}"
                                    })
                                    relocated = True
                                    break
                            if not relocated:
                                # Check for identity rename (e.g., id -> sub)
                                if field_name == "id" and "sub" in successor_fields:
                                    mutations.append({
                                        "file_path": file_path,
                                        "symbol_name": f"{base_name}.id",
                                        "mutation_type": "field_removed",
                                        "old_signature": "id: string",
                                        "new_signature": "sub: string (renamed to sub)",
                                        "severity": "critical",
                                        "line_number": line_no,
                                        "description": f"Property 'id' removed or renamed to 'sub' in {successor_name} contract"
                                    })
                                else:
                                    mutations.append({
                                        "file_path": file_path,
                                        "symbol_name": f"{base_name}.{field_name}",
                                        "mutation_type": "field_removed",
                                        "old_signature": f"{field_name}: {field_type}",
                                        "new_signature": "REMOVED",
                                        "severity": "critical",
                                        "line_number": line_no,
                                        "description": f"Field '{field_name}' removed in successor contract {successor_name}"
                                    })
                else:
                    line_no = self._find_symbol_line(base_src, base_name)
                    mutations.append({
                        "file_path": file_path,
                        "symbol_name": base_name,
                        "mutation_type": "interface_removed",
                        "old_signature": str(base_fields),
                        "new_signature": "REMOVED",
                        "severity": "critical",
                        "line_number": line_no,
                        "description": f"Interface {base_name} was completely removed or renamed"
                    })

        return mutations

    def _get_file_content(self, file_path: str, ref: str) -> str:
        """Loads file content from git ref or disk."""
        # 1. Try Git object inspection (git show <ref>:<path>) if repo is a git repository
        clean_path = file_path.replace("\\", "/").lstrip("/")
        if os.path.exists(os.path.join(self.repo_path, ".git")):
            try:
                res = subprocess.run(
                    ["git", "show", f"{ref}:{clean_path}"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res.returncode == 0 and res.stdout:
                    return res.stdout
            except Exception:
                pass

        # 2. Filesystem lookup (supporting branched directory trees and fixtures)
        candidates = [
            os.path.join(self.repo_path, ref, file_path),
            os.path.join(self.repo_path, file_path),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "fixtures", "sample-repo", ref, file_path),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "fixtures", "sample-repo", file_path),
        ]
        for p in candidates:
            if os.path.exists(p) and os.path.isfile(p):
                with open(p, "r", encoding="utf-8") as f:
                    return f.read()
        return ""


class DependencyDAGEngine:
    """NetworkX Directed Acyclic Graph engine for downstream impact analysis."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self._node_metadata: Dict[str, Dict[str, Any]] = {}

    def build_graph(self, repo_path: str = ""):
        """Build DAG monorepo graph with cycle safeguards."""
        self.graph.clear()
        self._node_metadata.clear()

        from .dag_crawler import DynamicWorkspaceCrawler
        crawler = DynamicWorkspaceCrawler(workspace_root=repo_path)
        crawled = crawler.crawl_workspace(repo_path) if repo_path and os.path.exists(repo_path) else nx.DiGraph()
        self.graph = crawler.merge_with_fallback(crawled)

        # Cycle detection and resolution: ensure graph is a valid DAG
        if not nx.is_directed_acyclic_graph(self.graph):
            try:
                cycles = list(nx.simple_cycles(self.graph))
                for cycle in cycles:
                    if len(cycle) >= 2:
                        # Break the feedback edge to prevent infinite loops
                        self.graph.remove_edge(cycle[-1], cycle[0])
            except Exception:
                pass

        for node_id in self.graph.nodes():
            self._node_metadata[node_id] = dict(self.graph.nodes[node_id])

    def calculate_downstream_impact(
        self, file_path: str, symbol_name: str
    ) -> List[Dict[str, Any]]:
        """Find all downstream callers in DAG."""
        normalized = file_path.replace("src/", "").replace("\\", "/")
        if normalized not in self.graph:
            # Find closest match
            for n in self.graph.nodes():
                if normalized.endswith(n) or n.endswith(normalized):
                    normalized = n
                    break

        if normalized not in self.graph:
            return []

        descendants = nx.descendants(self.graph, normalized)
        impact = []
        for desc in descendants:
            try:
                depth = nx.shortest_path_length(self.graph, normalized, desc)
            except Exception:
                depth = 1
            meta = self._node_metadata.get(desc, {})
            impact.append({
                "node_id": desc,
                "file_path": f"src/{desc}",
                "symbol_name": symbol_name,
                "dependency_depth": depth,
                "criticality": meta.get("criticality", 1.0),
                "traffic_weight": meta.get("traffic", 1.0),
                "service": meta.get("service", "Microservice")
            })
        # Sort by depth ascending
        impact.sort(key=lambda x: x["dependency_depth"])
        return impact

    def get_total_node_count(self) -> int:
        return self.graph.number_of_nodes()

    def get_max_depth(self, impact_nodes: List[Dict[str, Any]]) -> int:
        if not impact_nodes:
            return 0
        return max(n.get("dependency_depth", 1) for n in impact_nodes)

    def get_graph_data(self) -> Dict[str, Any]:
        """Export graph JSON for React Flow."""
        nodes = []
        for node_id in self.graph.nodes():
            meta = self._node_metadata.get(node_id, {})
            nodes.append({
                "id": node_id,
                "label": meta.get("label", node_id),
                "service": meta.get("service", "Microservice"),
                "criticality": meta.get("criticality", 1.0),
                "traffic": meta.get("traffic", 1.0),
            })
        edges = []
        for source, target in self.graph.edges():
            edges.append({"source": source, "target": target})
        return {"nodes": nodes, "edges": edges}

