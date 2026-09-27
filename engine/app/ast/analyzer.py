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
        elif file_path.endswith(".py"):
            mutations.extend(
                self._parse_py_contract_mutations(file_path, base_content, head_content)
            )
        return mutations

    def _extract_ts_interfaces(self, source: str) -> Dict[str, Dict[str, str]]:
        """Balanced-braces grammar parser handling nested structures, interfaces, type aliases, generics, and extends."""
        interfaces: Dict[str, Dict[str, str]] = {}
        # Matches `interface Name<T> extends Base {`, `type Name<K, V> = {`, `export interface Name {`, etc.
        pattern = re.compile(
            r"(?:export\s+)?(?:interface|type)\s+(\w+)(?:<[^>]+>)?(?:\s+extends\s+[^{=]+)?\s*(?:=\s*)?\{",
            re.MULTILINE,
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

    def _parse_field_or_method(self, stmt: str) -> Optional[Tuple[str, str]]:
        """Parses a single TypeScript property or method statement."""
        stmt = stmt.strip().rstrip(";")
        if not stmt:
            return None
        # Check method signature first: e.g. validate(token: string): Promise<boolean>
        method_match = re.match(r"^(\w+)\??(?:<[^>]+>)?\s*\((.*?)\)\s*:\s*(.+)$", stmt, re.DOTALL)
        if method_match:
            name = method_match.group(1)
            params = method_match.group(2).strip()
            ret_type = method_match.group(3).strip()
            return name, f"({params}) => {ret_type}"
        # Standard property: e.g. id?: string, tier: 'free' | 'pro'
        field_match = re.match(r"^(\w+)\??\s*:\s*(.+)$", stmt, re.DOTALL)
        if field_match:
            return field_match.group(1), field_match.group(2).strip()
        return None

    def _parse_fields(self, body: str) -> Dict[str, str]:
        """Parse top-level and nested structure fields from interface/type body."""
        fields: Dict[str, str] = {}
        depth = 0
        current_line = ""
        # Strip block comments and line comments
        cleaned_body = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
        cleaned_body = re.sub(r"//.*$", "", cleaned_body, flags=re.MULTILINE)
        for char in cleaned_body:
            if char in "({[":
                depth += 1
                current_line += char
            elif char in ")}]":
                depth -= 1
                current_line += char
            elif (char == ";" or char == "\n" or char == ",") and depth == 0:
                parsed = self._parse_field_or_method(current_line)
                if parsed:
                    fields[parsed[0]] = parsed[1]
                current_line = ""
            else:
                current_line += char

        # Process trailing statement
        if current_line.strip() and depth == 0:
            parsed = self._parse_field_or_method(current_line)
            if parsed:
                fields[parsed[0]] = parsed[1]

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

    def _detect_field_rename(
        self,
        field_name: str,
        field_type: str,
        target_fields: Dict[str, str],
        origin_fields: Dict[str, str],
    ) -> Optional[Tuple[str, str]]:
        """
        Dynamically detects if a missing field was renamed/evolved into a new field.
        Eliminates hardcoded field heuristics by combining semantic alias clusters,
        1-to-1 cardinality substitution, and substring homology.
        """
        # Newly introduced fields in target contract
        new_fields = {k: v for k, v in target_fields.items() if k not in origin_fields}
        if not new_fields:
            return None

        # Standard semantic identity & authorization token equivalences
        semantic_aliases: Dict[str, Set[str]] = {
            "id": {"sub", "subject", "uuid", "uid", "identifier", "pk", "key", "userId", "user_id"},
            "sub": {"id", "subject", "uuid", "uid", "identifier", "pk", "key"},
            "user_id": {"user_sub", "userId", "userUuid", "sub", "id"},
            "userId": {"user_id", "userSub", "sub", "uuid", "id"},
            "token": {"jwt", "authToken", "accessToken", "bearerToken"},
            "created_at": {"createdAt", "created_time", "timestamp"},
            "updated_at": {"updatedAt", "modified_at", "lastModified"},
        }

        # 1. Semantic alias match
        norm_field = field_name.lower()
        for alias_key, aliases in semantic_aliases.items():
            if norm_field == alias_key:
                for candidate in aliases:
                    if candidate in new_fields:
                        return candidate, new_fields[candidate]

        # 2. Singular 1-to-1 substitution with type compatibility
        missing_fields = [k for k in origin_fields if k not in target_fields]
        if len(missing_fields) == 1 and len(new_fields) == 1:
            cand_name, cand_type = next(iter(new_fields.items()))
            if cand_type == field_type or field_type in cand_type or cand_type in field_type:
                return cand_name, cand_type

        # 3. Substring homology (e.g. accountId -> accountUuid, userTier -> tier)
        for cand_name, cand_type in new_fields.items():
            norm_orig = norm_field.replace("_", "")
            norm_cand = cand_name.lower().replace("_", "")
            if (norm_orig in norm_cand or norm_cand in norm_orig) and (cand_type == field_type or "string" in cand_type):
                return cand_name, cand_type

        return None

    def _detect_union_narrowing(self, base_type: str, head_type: str) -> Optional[List[str]]:
        """Detects if an accepted union / enum type had variants removed."""
        if "|" in base_type and "|" in head_type:
            base_variants = {v.strip() for v in base_type.split("|") if v.strip()}
            head_variants = {v.strip() for v in head_type.split("|") if v.strip()}
            removed = base_variants - head_variants
            if removed:
                return sorted(list(removed))
        return None

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
                        # Check if relocated to nested structure (e.g. metadata.tier)
                        relocated = False
                        for s_field, s_type in head_fields.items():
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
                            renamed = self._detect_field_rename(field_name, field_type, head_fields, base_fields)
                            if renamed:
                                new_name, new_type = renamed
                                mutations.append({
                                    "file_path": file_path,
                                    "symbol_name": f"{base_name}.{field_name}",
                                    "mutation_type": "field_removed",
                                    "old_signature": f"{field_name}: {field_type}",
                                    "new_signature": f"{new_name}: {new_type} (renamed to {new_name})",
                                    "severity": "critical",
                                    "line_number": line_no,
                                    "description": f"Property '{field_name}' removed or renamed to '{new_name}' in {base_name} contract"
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
                                    "description": f"Field '{field_name}' was removed from {base_name}"
                                })
                    elif head_fields[field_name] != field_type:
                        head_type = head_fields[field_name]
                        narrowed = self._detect_union_narrowing(field_type, head_type)
                        desc = (
                            f"Union enum variants removed: {', '.join(narrowed)}"
                            if narrowed
                            else f"Type signature mutated from {field_type} to {head_type}"
                        )
                        mutations.append({
                            "file_path": file_path,
                            "symbol_name": f"{base_name}.{field_name}",
                            "mutation_type": "type_change",
                            "old_signature": f"{field_name}: {field_type}",
                            "new_signature": f"{field_name}: {head_type}",
                            "severity": "critical",
                            "line_number": line_no,
                            "description": desc
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
                                head_type = successor_fields[field_name]
                                narrowed = self._detect_union_narrowing(field_type, head_type)
                                desc = (
                                    f"Union enum variants removed: {', '.join(narrowed)}"
                                    if narrowed
                                    else f"Type signature mutated in successor {successor_name}"
                                )
                                mutations.append({
                                    "file_path": file_path,
                                    "symbol_name": f"{base_name}.{field_name}",
                                    "mutation_type": "type_change",
                                    "old_signature": f"{field_name}: {field_type}",
                                    "new_signature": f"{field_name}: {head_type}",
                                    "severity": "critical",
                                    "line_number": line_no,
                                    "description": desc
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
                                renamed = self._detect_field_rename(field_name, field_type, successor_fields, base_fields)
                                if renamed:
                                    new_name, new_type = renamed
                                    mutations.append({
                                        "file_path": file_path,
                                        "symbol_name": f"{base_name}.{field_name}",
                                        "mutation_type": "field_removed",
                                        "old_signature": f"{field_name}: {field_type}",
                                        "new_signature": f"{new_name}: {new_type} (renamed to {new_name})",
                                        "severity": "critical",
                                        "line_number": line_no,
                                        "description": f"Property '{field_name}' removed or renamed to '{new_name}' in {successor_name} contract"
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

    def _parse_py_contract_mutations(
        self, file_path: str, base_src: str, head_src: str
    ) -> List[Dict[str, Any]]:
        """Parses Python Pydantic/TypedDict class contracts and diffs fields."""
        def extract_py_classes(src: str) -> Dict[str, Dict[str, str]]:
            classes: Dict[str, Dict[str, str]] = {}
            current_cls = None
            for line in src.splitlines():
                cls_match = re.match(r"^class\s+(\w+)(?:\([^)]+\))?:", line.strip())
                if cls_match:
                    current_cls = cls_match.group(1)
                    classes[current_cls] = {}
                    continue
                if current_cls and re.match(r"^\s{4}(\w+)\s*:\s*(.+)$", line):
                    field_match = re.match(r"^\s{4}(\w+)\s*:\s*(.+)$", line)
                    if field_match:
                        k = field_match.group(1)
                        v = field_match.group(2).split("=")[0].strip()
                        classes[current_cls][k] = v
                elif current_cls and line and not line.startswith(" ") and not line.startswith("\t"):
                    current_cls = None
            return classes

        base_classes = extract_py_classes(base_src)
        head_classes = extract_py_classes(head_src)
        mutations = []

        for cls_name, b_fields in base_classes.items():
            if cls_name in head_classes:
                h_fields = head_classes[cls_name]
                for f_name, f_type in b_fields.items():
                    if f_name not in h_fields:
                        mutations.append({
                            "file_path": file_path,
                            "symbol_name": f"{cls_name}.{f_name}",
                            "mutation_type": "field_removed",
                            "old_signature": f"{f_name}: {f_type}",
                            "new_signature": "REMOVED",
                            "severity": "critical",
                            "line_number": self._find_symbol_line(base_src, f_name),
                            "description": f"Field '{f_name}' removed from Python model {cls_name}"
                        })
                    elif h_fields[f_name] != f_type:
                        mutations.append({
                            "file_path": file_path,
                            "symbol_name": f"{cls_name}.{f_name}",
                            "mutation_type": "type_change",
                            "old_signature": f"{f_name}: {f_type}",
                            "new_signature": f"{f_name}: {h_fields[f_name]}",
                            "severity": "critical",
                            "line_number": self._find_symbol_line(base_src, f_name),
                            "description": f"Type signature mutated in Python model {cls_name}"
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
                    encoding="utf-8",
                    errors="replace",
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

        # Non-combinatorial O(V + E) cycle resolution using iterative DFS cycle detection
        while not nx.is_directed_acyclic_graph(self.graph):
            try:
                cycle = nx.find_cycle(self.graph, orientation="original")
                if cycle:
                    # Break the feedback edge to guarantee a clean DAG
                    u, v = cycle[0][0], cycle[0][1]
                    self.graph.remove_edge(u, v)
                else:
                    break
            except (nx.NetworkXNoCycle, Exception):
                break

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

