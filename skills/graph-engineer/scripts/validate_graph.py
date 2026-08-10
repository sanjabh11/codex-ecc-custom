#!/usr/bin/env python3
"""Validator for graph-engineer skill.

Validates an AI agent graph definition against the Graph Engineer principles.
Exits 1 if any hard violation is found. Exits 0 with a summary report on success.

Usage:
    python3 validate_graph.py <graph-definition.json>
    python3 validate_graph.py --rules <validation-rules.json> [--runtime-root <repo>] [--review-report <report.json>] <graph-definition.json>
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

try:
    from referencing import Registry, Resource
    from referencing.exceptions import Unresolvable
    HAS_REFERENCING = True
except ImportError:  # pragma: no cover - covered by dependency gate
    Registry = Resource = None
    Unresolvable = RuntimeError
    HAS_REFERENCING = False

try:
    from runtime_policy import classify_tool, load_tool_policy, normalize_tool, executable_available
except ImportError:  # pragma: no cover - supports package-style imports
    from scripts.runtime_policy import classify_tool, load_tool_policy, normalize_tool, executable_available

try:
    from schema_utils import strict_format_checker
except ImportError:  # pragma: no cover - supports package-style imports
    try:
        from scripts.schema_utils import strict_format_checker
    except ImportError:  # pragma: no cover - dependency-gate path
        strict_format_checker = None

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RULES_PATH = os.path.join(SKILL_DIR, "validation-rules.json")
DEFAULT_SCHEMA_PATH = os.path.join(SKILL_DIR, "schemas", "graph-definition.schema.json")
MAX_GRAPH_BYTES = 5 * 1024 * 1024
MAX_GRAPH_NODES = 1000
MAX_GRAPH_EDGES = 5000

checks_passed = 0
checks_failed = 0
failures = []
warnings = []


def check(name, condition, detail=""):
    global checks_passed, checks_failed
    if condition:
        print(f"  [PASS] {name}")
        checks_passed += 1
    else:
        print(f"  [FAIL] {name} — {detail}")
        checks_failed += 1
        failures.append(name)


def warn(name, detail):
    global warnings
    print(f"  [WARN] {name} — {detail}")
    warnings.append(f"{name}: {detail}")


def load_rules(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            value = json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ERROR: Validation rules could not be loaded from {path}: {exc}")
        return None
    if not isinstance(value, dict):
        print(f"ERROR: Validation rules root must be an object, got {type(value).__name__}")
        return None
    return value


def load_schema_bundle(schema_path):
    """Load local schemas and resolve references without network access."""
    if not HAS_REFERENCING:
        raise ValueError("referencing package is required for local schema resolution")
    schema_path = os.path.abspath(schema_path)
    schema_dir = os.path.dirname(schema_path)
    documents = {}
    resources = []
    for filename in (
        "graph-definition.schema.json",
        "node-definition.schema.json",
        "review-report.schema.json",
        "evidence-record.schema.json",
    ):
        path = os.path.join(schema_dir, filename)
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
        documents[filename] = document
        documents[os.path.abspath(path)] = document
        documents[Path(path).as_uri()] = document
        if isinstance(document.get("$id"), str):
            documents[document["$id"]] = document
            resources.append((document["$id"], Resource.from_contents(document)))
    schema = documents.get(os.path.basename(schema_path))
    if schema is None:
        raise ValueError(f"schema not present in local bundle: {schema_path}")
    return schema, Registry().with_resources(resources)


def load_graph(path):
    if not os.path.exists(path):
        print(f"ERROR: Graph definition not found: {path}")
        sys.exit(1)
    try:
        if os.path.getsize(path) > MAX_GRAPH_BYTES:
            print(f"ERROR: Graph definition exceeds the {MAX_GRAPH_BYTES}-byte safety limit")
            sys.exit(1)
        with open(path, "r", encoding="utf-8") as f:
            graph = json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ERROR: Could not parse graph definition {path}: {exc}")
        sys.exit(1)
    if not isinstance(graph, dict):
        print(f"ERROR: Graph definition root must be an object, got {type(graph).__name__}")
        sys.exit(1)
    return graph


def check_graph_shape(graph):
    """Check the top-level graph contract before semantic checks run."""
    required = ("name", "description", "diagram", "nodes", "edges", "caps", "human_gates")
    for field in required:
        check(
            f"graph_has_{field}",
            field in graph,
            f"Graph is missing required field '{field}'",
        )

    check("graph_name_is_string", isinstance(graph.get("name"), str), "Graph name must be a string")
    check("graph_description_is_string", isinstance(graph.get("description"), str), "Graph description must be a string")
    check("graph_nodes_is_list", isinstance(graph.get("nodes"), list), "Graph nodes must be a list")
    check("graph_edges_is_list", isinstance(graph.get("edges"), list), "Graph edges must be a list")
    check("graph_caps_is_object", isinstance(graph.get("caps"), dict), "Graph caps must be an object")
    check("graph_human_gates_is_list", isinstance(graph.get("human_gates"), list), "Graph human_gates must be a list")
    if isinstance(graph.get("nodes"), list):
        check("graph_nodes_within_safety_limit", len(graph["nodes"]) <= MAX_GRAPH_NODES, f"Graph has more than {MAX_GRAPH_NODES} nodes")
    if isinstance(graph.get("edges"), list):
        check("graph_edges_within_safety_limit", len(graph["edges"]) <= MAX_GRAPH_EDGES, f"Graph has more than {MAX_GRAPH_EDGES} edges")


def check_json_schema(graph, schema_path=None):
    """Invoke JSON Schema validation and fail closed when unavailable."""
    if not HAS_JSONSCHEMA or strict_format_checker is None:
        check(
            "jsonschema_available",
            False,
            "jsonschema package is required; install skills/graph-engineer/requirements.txt before validating",
        )
        return
    if schema_path is None:
        schema_path = DEFAULT_SCHEMA_PATH
    if not os.path.isfile(schema_path):
        check("schema_file_present", False, f"Schema file not found at {schema_path} — validation is fail-closed")
        return
    try:
        schema, registry = load_schema_bundle(schema_path)
        # G13: Use a FormatChecker to enforce date-time and other format
        # constraints. Without this, jsonschema accepts "not-a-date" as valid.
        format_checker = strict_format_checker()
        validator = jsonschema.Draft7Validator(
            schema,
            registry=registry,
            format_checker=format_checker,
        )
        validator.validate(graph)
        check("json_schema_valid", True, "JSON Schema validation passed")
    except jsonschema.ValidationError as e:
        check("json_schema_valid", False, f"JSON Schema violation: {e.message} at path {list(e.absolute_path)}")
    except jsonschema.SchemaError as e:
        check("json_schema_valid", False, f"The graph schema itself is invalid: {e.message}")
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, ValueError, Unresolvable) as e:
        check("json_schema_valid", False, f"The graph schema could not be loaded: {e}")


def reviewed_worker_id(graph, reviewer_id):
    """Return the one exact worker bound to a reviewer.

    v1.1 requires reviewed_node_id. Legacy v1 graphs remain supported only
    when their topology identifies exactly one incoming worker.
    """
    nodes = {
        node.get("id"): node
        for node in graph.get("nodes", [])
        if isinstance(node, dict)
    }
    reviewer = nodes.get(reviewer_id)
    if not reviewer or reviewer.get("type") != "reviewer":
        return None
    explicit = reviewer.get("reviewed_node_id")
    if isinstance(explicit, str) and nodes.get(explicit, {}).get("type") == "worker":
        return explicit
    incoming_workers = sorted({
        edge.get("from")
        for edge in graph.get("edges", [])
        if isinstance(edge, dict)
        and edge.get("to") == reviewer_id
        and edge.get("type") in ("data", "control")
        and nodes.get(edge.get("from"), {}).get("type") == "worker"
    })
    return incoming_workers[0] if len(incoming_workers) == 1 else None


def reviewed_worker_ids(graph, reviewer_id):
    """Return all workers a reviewer explicitly or topologically covers."""
    exact = reviewed_worker_id(graph, reviewer_id)
    if exact is not None:
        return {exact}
    nodes = {
        node.get("id"): node
        for node in graph.get("nodes", [])
        if isinstance(node, dict)
    }
    return {
        edge.get("from")
        for edge in graph.get("edges", [])
        if isinstance(edge, dict)
        and edge.get("to") == reviewer_id
        and edge.get("type") in ("data", "control")
        and nodes.get(edge.get("from"), {}).get("type") == "worker"
    }


def check_review_reports(graph, report_paths):
    """Validate supplied reviewer artifacts and bind them to graph ownership."""
    if not report_paths:
        return
    if not HAS_JSONSCHEMA or strict_format_checker is None:
        check("review_report_jsonschema_available", False, "jsonschema is required to validate reviewer artifacts")
        return
    schema_path = os.path.join(SKILL_DIR, "schemas", "review-report.schema.json")
    try:
        with open(schema_path, encoding="utf-8") as handle:
            schema = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        check("review_report_schema_loads", False, f"Review report schema could not be loaded: {exc}")
        return

    nodes = {node.get("id"): node for node in graph.get("nodes", []) if isinstance(node, dict)}
    for index, report_path in enumerate(report_paths):
        try:
            with open(report_path, encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            check(f"review_report_{index}_parses", False, f"Could not parse reviewer report '{report_path}': {exc}")
            continue
        try:
            jsonschema.validate(
                instance=report,
                schema=schema,
                format_checker=strict_format_checker(),
            )
            schema_valid = True
        except (jsonschema.ValidationError, jsonschema.SchemaError) as exc:
            schema_valid = False
            check(f"review_report_{index}_schema_valid", False, f"Reviewer report '{report_path}' is invalid: {exc}")
        if not schema_valid:
            continue
        reviewer_id = report.get("reviewer_id")
        reviewed_id = report.get("reviewed_node_id")
        reviewer = nodes.get(reviewer_id, {})
        check(
            f"review_report_{index}_reviewer_exists",
            reviewer.get("type") == "reviewer",
            f"Reviewer report '{report_path}' names non-reviewer '{reviewer_id}'",
        )
        expected_reviewed_id = reviewed_worker_id(graph, reviewer_id)
        expected_reviewed_ids = reviewed_worker_ids(graph, reviewer_id)
        check(
            f"review_report_{index}_reviewed_node_matches",
            (
                expected_reviewed_id == reviewed_id
                if graph.get("schema_version") == "v1.1"
                else reviewed_id in expected_reviewed_ids
            ),
            f"Reviewer report '{report_path}' is not bound to the exact worker reviewed by '{reviewer_id}'",
        )
        questions = reviewer.get("review_questions", [])
        check(
            f"review_report_{index}_question_matches",
            isinstance(questions, list) and len(questions) == 1 and report.get("question") == questions[0],
            f"Reviewer report '{report_path}' question does not match the graph reviewer contract",
        )


def check_diagram_present(graph):
    diagram = graph.get("diagram", "")
    check(
        "diagram_present",
        diagram and diagram.strip(),
        "No diagram field present — 'draw first, code second' requires a graph diagram before implementation",
    )


def check_nodes_exist(graph):
    nodes = graph.get("nodes", [])
    check("nodes_exist", len(nodes) > 0, "Graph has no nodes")


def check_node_edge_contracts(graph, rules):
    """Validate IDs and make each data/control edge agree with node inputs."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = [node.get("id") for node in nodes]
    known_ids = {node_id for node_id in node_ids if isinstance(node_id, str)}

    check(
        "node_ids_unique",
        len(node_ids) == len(set(node_ids)),
        "Node IDs must be unique so edges and contracts are unambiguous",
    )

    valid_edge_types = set(rules.get("rules", {}).get("valid_edge_types", ["data", "control", "failure"])) if rules else {"data", "control", "failure"}
    structural_edges = set()
    for index, node in enumerate(nodes):
        node_id = node.get("id", f"node-{index}")
        for field in ("id", "type", "responsibility", "inputs", "outputs"):
            check(
                f"node_{node_id}_has_{field}",
                field in node,
                f"Node '{node_id}' is missing required field '{field}'",
            )
        check(f"node_{node_id}_id_is_string", isinstance(node.get("id"), str), "Node IDs must be strings")
        check(f"node_{node_id}_inputs_is_list", isinstance(node.get("inputs"), list), "Node inputs must be a list")
        check(f"node_{node_id}_outputs_is_list", isinstance(node.get("outputs"), list), "Node outputs must be a list")
        for input_id in node.get("inputs", []) if isinstance(node.get("inputs"), list) else []:
            check(
                f"node_{node_id}_input_{input_id}_exists",
                input_id in known_ids,
                f"Node '{node_id}' declares unknown input '{input_id}'",
            )

        contract = node.get("contract")
        if contract is not None:
            check(
                f"node_{node_id}_contract_is_object",
                isinstance(contract, dict),
                f"Node '{node_id}' contract must be an object when supplied",
            )
            if isinstance(contract, dict):
                for contract_field in ("preconditions", "postconditions", "failure_output"):
                    if contract_field in contract:
                        check(
                            f"node_{node_id}_{contract_field}_is_string",
                            isinstance(contract[contract_field], str),
                            f"Node '{node_id}' contract field '{contract_field}' must be a string",
                        )

    for index, edge in enumerate(edges):
        edge_type = edge.get("type")
        from_id = edge.get("from")
        to_id = edge.get("to")
        check(f"edge_{index}_has_required_fields", all(field in edge for field in ("from", "to", "dependency_reason", "type")), f"Edge {index} is missing a required field")
        check(f"edge_{index}_from_exists", from_id in known_ids, f"Edge {index} references unknown source '{from_id}'")
        check(f"edge_{index}_to_exists", to_id in known_ids, f"Edge {index} references unknown target '{to_id}'")
        check(f"edge_{index}_type_valid", edge_type in valid_edge_types, f"Edge {index} has invalid type '{edge_type}'")
        if edge_type in ("data", "control") and from_id in known_ids and to_id in known_ids:
            structural_edges.add((from_id, to_id))
            destination = next(node for node in nodes if node.get("id") == to_id)
            check(
                f"edge_{index}_declared_in_destination_inputs",
                from_id in destination.get("inputs", []),
                f"Data/control edge {from_id} → {to_id} is not declared in the destination inputs",
            )

    for node in nodes:
        node_id = node.get("id")
        for input_id in node.get("inputs", []) if isinstance(node.get("inputs"), list) else []:
            check(
                f"input_edge_{input_id}_{node_id}_exists",
                (input_id, node_id) in structural_edges,
                f"Node '{node_id}' declares input '{input_id}' but no data/control edge supplies it",
            )


def check_non_empty_outputs(graph):
    """Every node must have at least one non-empty output description."""
    for node in graph.get("nodes", []):
        node_id = node.get("id", "unknown")
        outputs = node.get("outputs", [])
        check(
            f"node_{node_id}_outputs_non_empty",
            isinstance(outputs, list) and len(outputs) > 0 and all(
                isinstance(o, str) and o.strip() for o in outputs
            ),
            f"Node '{node_id}' must have at least one non-empty output — empty outputs hide artifact contracts",
        )


def check_tools_well_formed(graph):
    """Node tools arrays must contain valid shared-policy declarations."""
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_id = node.get("id", "unknown")
        tools = node.get("tools")
        if tools is None:
            continue
        check(
            f"node_{node_id}_tools_is_list",
            isinstance(tools, list),
            f"Node '{node_id}' tools must be a list of strings, got {type(tools).__name__}",
        )
        if isinstance(tools, list):
            for i, tool in enumerate(tools):
                check(
                    f"node_{node_id}_tool_{i}_is_string",
                    normalize_tool(tool) is not None,
                    f"Node '{node_id}' tool[{i}] must be a non-empty string or a valid object declaration",
                )


_PORT_SCHEMA_CACHE = {}


def _resolve_port_schema(schema):
    """Resolve only local schema references used by typed graph ports."""
    current = schema
    seen = set()
    for _ in range(8):
        if not isinstance(current, dict):
            return None
        ref = current.get("$ref")
        if not isinstance(ref, str):
            return current
        if ref in seen or not ref.startswith("schemas/"):
            return None
        seen.add(ref)
        path = (Path(SKILL_DIR) / ref).resolve()
        try:
            path.relative_to(Path(SKILL_DIR).resolve())
        except ValueError:
            return None
        if not path.is_file():
            return None
        try:
            if ref not in _PORT_SCHEMA_CACHE:
                _PORT_SCHEMA_CACHE[ref] = json.loads(path.read_text(encoding="utf-8"))
            current = _PORT_SCHEMA_CACHE[ref]
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
    return None


def _schemas_compatible(source_schema, destination_schema):
    """Use a conservative subset check for machine-consumed port contracts.

    A source output must be guaranteed to satisfy the destination input. Exact
    schemas, equal local references, and unconstrained destination primitive or
    object types are safe. For constrained objects, required fields and
    declared property schemas must be compatible. Unknown schema relations are
    rejected rather than accepted by matching only ``type``.
    """
    if not isinstance(source_schema, dict) or not isinstance(destination_schema, dict):
        return False
    if source_schema == destination_schema:
        return True
    if (
        isinstance(source_schema.get("$ref"), str)
        and source_schema.get("$ref") == destination_schema.get("$ref")
    ):
        return True
    source = _resolve_port_schema(source_schema)
    destination = _resolve_port_schema(destination_schema)
    if source is None or destination is None:
        return False
    if source == destination:
        return True

    destination_type = destination.get("type")
    source_type = source.get("type")
    if (
        isinstance(destination_type, str)
        and set(destination) <= {"type"}
        and source_type == destination_type
    ):
        return True

    if source_type != "object" or destination_type != "object":
        return False

    source_required = set(source.get("required", []))
    destination_required = set(destination.get("required", []))
    if not destination_required.issubset(source_required):
        return False
    source_properties = source.get("properties", {})
    destination_properties = destination.get("properties", {})
    if not isinstance(source_properties, dict) or not isinstance(destination_properties, dict):
        return False
    if not set(destination_properties).issubset(source_properties):
        return False
    for name, destination_property in destination_properties.items():
        if source_properties.get(name) != destination_property:
            return False
    if destination.get("additionalProperties") is False and source.get("additionalProperties") is not False:
        return False
    return True


def check_v11_typed_contracts(graph):
    """Validate typed ports and review-report bindings for strict v1.1 graphs."""
    if graph.get("schema_version") != "v1.1":
        return

    nodes = {node.get("id"): node for node in graph.get("nodes", []) if isinstance(node, dict)}
    output_ports = {}
    input_ports = {}
    for node_id, node in nodes.items():
        outputs = node.get("output_ports", [])
        inputs = node.get("input_ports", [])
        output_names = [port.get("name") for port in outputs if isinstance(port, dict)]
        input_names = [port.get("name") for port in inputs if isinstance(port, dict)]
        output_ports[node_id] = set(output_names)
        input_ports[node_id] = {port.get("name"): port for port in inputs if isinstance(port, dict)}
        check(
            f"node_{node_id}_output_ports_unique",
            len(output_names) == len(set(output_names)),
            f"Node '{node_id}' has duplicate output port names",
        )
        check(
            f"node_{node_id}_input_ports_unique",
            len(input_names) == len(set(input_names)),
            f"Node '{node_id}' has duplicate input port names",
        )
        if node.get("type") == "reviewer":
            report_schema = node.get("review_report_schema", "")
            check(
                f"reviewer_{node_id}_report_schema_bound",
                report_schema == "schemas/review-report.schema.json",
                f"Reviewer '{node_id}' must bind schemas/review-report.schema.json",
            )
            reviewed_workers = {
                edge.get("from")
                for edge in graph.get("edges", [])
                if edge.get("to") == node_id
                and edge.get("type") in ("data", "control")
                and nodes.get(edge.get("from"), {}).get("type") == "worker"
            }
            expected_reviewed_worker = reviewed_worker_id(graph, node_id)
            check(
                f"reviewer_{node_id}_reviewed_node_bound",
                expected_reviewed_worker is not None
                and node.get("reviewed_node_id") == expected_reviewed_worker
                and len(reviewed_workers) == 1,
                f"Reviewer '{node_id}' must bind exactly one reviewed worker; found {reviewed_workers}",
            )
            check(
                f"reviewer_{node_id}_report_port_present",
                "review_report" in output_ports[node_id] or "review-report" in output_ports[node_id],
                f"Reviewer '{node_id}' must expose a review_report output port",
            )
            report_ports = [
                port for port in outputs
                if isinstance(port, dict) and port.get("name") in ("review_report", "review-report")
            ]
            check(
                f"reviewer_{node_id}_report_port_schema_bound",
                bool(report_ports) and report_ports[0].get("schema", {}).get("$ref") == "schemas/review-report.schema.json",
                f"Reviewer '{node_id}' report port must reference schemas/review-report.schema.json",
            )

        for port_index, port in enumerate(outputs + inputs):
            if not isinstance(port, dict) or not isinstance(port.get("schema"), dict):
                continue
            if not HAS_JSONSCHEMA:
                continue
            try:
                jsonschema.Draft7Validator.check_schema(port["schema"])
                check(f"node_{node_id}_port_{port_index}_schema_valid", True)
            except jsonschema.SchemaError as exc:
                check(f"node_{node_id}_port_{port_index}_schema_valid", False, f"Invalid port schema: {exc.message}")

    for index, edge in enumerate(graph.get("edges", [])):
        if not isinstance(edge, dict) or edge.get("type") not in ("data", "control"):
            continue
        source, target = edge.get("from"), edge.get("to")
        from_port, to_port = edge.get("from_port"), edge.get("to_port")
        check(
            f"edge_{index}_typed_ports_present",
            bool(from_port and to_port),
            f"v1.1 edge {index} must declare from_port and to_port",
        )
        if source in output_ports and target in input_ports and from_port and to_port:
            check(
                f"edge_{index}_source_port_exists",
                from_port in output_ports[source],
                f"Edge {index} references missing output port '{from_port}' on '{source}'",
            )
            destination_port = input_ports[target].get(to_port)
            check(
                f"edge_{index}_destination_port_exists",
                destination_port is not None,
                f"Edge {index} references missing input port '{to_port}' on '{target}'",
            )
            if destination_port is not None:
                check(
                    f"edge_{index}_port_source_matches",
                    destination_port.get("from_node") == source
                    and destination_port.get("from_port", from_port) == from_port,
                    f"Edge {index} input port '{to_port}' does not bind to {source}.{from_port}",
                )
                source_port = next(
                    (
                        port for port in nodes.get(source, {}).get("output_ports", [])
                        if isinstance(port, dict) and port.get("name") == from_port
                    ),
                    None,
                )
                source_schema = source_port.get("schema") if source_port else None
                destination_schema = destination_port.get("schema")
                compatible = _schemas_compatible(source_schema, destination_schema)
                check(
                    f"edge_{index}_port_schema_compatible",
                    compatible,
                    f"Edge {index} source and destination port schemas are incompatible",
                )


def check_v11_resources_and_exhaustion(graph):
    """Require explicit resource locks and cap-exhaustion routes in v1.1."""
    if graph.get("schema_version") != "v1.1":
        return

    nodes = {node.get("id"): node for node in graph.get("nodes", []) if isinstance(node, dict)}
    writers = {}
    for node_id, node in nodes.items():
        resources = node.get("resources", {})
        writes = resources.get("writes", []) if isinstance(resources, dict) else []
        locks = set(resources.get("locks", [])) if isinstance(resources, dict) else set()
        declared_resources = []
        if isinstance(resources, dict):
            declared_resources.extend(resources.get("reads", []))
            declared_resources.extend(resources.get("writes", []))
            declared_resources.extend(resources.get("locks", []))
        for resource in declared_resources:
            check(
                f"resource_{node_id}_{resource}_canonical",
                isinstance(resource, str)
                and bool(resource)
                and not resource.startswith("/")
                and ".." not in resource.split("/")
                and not any(char.isspace() for char in resource),
                f"Resource '{resource}' must be a canonical non-traversing resource ID",
            )
        if writes:
            check(
                f"node_{node_id}_writes_have_locks",
                bool(locks),
                f"Node '{node_id}' declares writes but no resource lock",
            )
        for resource in writes:
            writers.setdefault(resource, []).append((node_id, locks))

    for resource, entries in writers.items():
        if len(entries) < 2:
            continue
        shared_locks = set.intersection(*(locks for _, locks in entries)) if entries else set()
        check(
            f"resource_{resource}_writers_are_serialized",
            bool(shared_locks),
            f"Resource '{resource}' has multiple writers without a shared lock: {[node_id for node_id, _ in entries]}",
        )

    failure_targets = {
        edge.get("to")
        for edge in graph.get("edges", [])
        if isinstance(edge, dict) and edge.get("type") == "failure"
    }
    for worker_id in failure_targets:
        exhaustion_edges = [
            edge for edge in graph.get("edges", [])
            if isinstance(edge, dict)
            and edge.get("type") == "exhaustion"
            and edge.get("from") == worker_id
        ]
        check(
            f"worker_{worker_id}_has_explicit_exhaustion_route",
            any(
                nodes.get(edge.get("to"), {}).get("type") == "human-gate"
                and edge.get("condition") == "retry_exhausted"
                for edge in exhaustion_edges
            ),
            f"Worker '{worker_id}' must route retry-cap exhaustion to a human-gate",
        )
    for index, edge in enumerate(graph.get("edges", [])):
        if edge.get("type") == "failure":
            check(
                f"failure_edge_{index}_condition_is_review_failed",
                edge.get("condition") in ("review_failed", "retryable_failure"),
                f"v1.1 failure edge {index} must declare a review_failed or retryable_failure condition",
            )
        elif edge.get("type") == "exhaustion":
            check(
                f"exhaustion_edge_{index}_condition_is_retry_exhausted",
                edge.get("condition") == "retry_exhausted",
                f"v1.1 exhaustion edge {index} must declare condition retry_exhausted",
            )
            check(
                f"exhaustion_edge_{index}_targets_human_gate",
                nodes.get(edge.get("to"), {}).get("type") == "human-gate",
                f"v1.1 exhaustion edge {index} must target a human-gate",
            )
        elif edge.get("type") in ("data", "control") and nodes.get(edge.get("from"), {}).get("type") == "reviewer":
            check(
                f"pass_edge_{index}_condition_is_review_passed",
                edge.get("condition") == "review_passed",
                f"v1.1 reviewer pass edge {index} must declare condition review_passed",
            )


def check_v11_joins(graph):
    """Require explicit expected-count and partial-failure policy for fan-in joins."""
    if graph.get("schema_version") != "v1.1":
        return
    nodes = {node.get("id"): node for node in graph.get("nodes", []) if isinstance(node, dict)}
    incoming = {node_id: 0 for node_id in nodes}
    for edge in graph.get("edges", []):
        if edge.get("type") in ("data", "control") and edge.get("to") in incoming:
            incoming[edge["to"]] += 1
    join_map = {join.get("node_id"): join for join in graph.get("joins", []) if isinstance(join, dict)}
    for node_id, count in incoming.items():
        if count <= 1:
            continue
        join = join_map.get(node_id)
        check(
            f"join_{node_id}_declared",
            join is not None,
            f"Fan-in node '{node_id}' has {count} inputs but no join contract",
        )
        if join is None:
            continue
        check(
            f"join_{node_id}_expected_count_matches",
            join.get("expected_count") == count,
            f"Join '{node_id}' expected_count {join.get('expected_count')} does not match {count} incoming data/control edges",
        )
        policy = join.get("partial_failure")
        check(
            f"join_{node_id}_partial_failure_policy",
            policy in ("block", "human_gate", "continue_with_warning"),
            f"Join '{node_id}' must declare an explicit partial_failure policy",
        )
        if policy == "human_gate":
            gate_id = join.get("human_gate_id")
            check(
                f"join_{node_id}_partial_failure_gate",
                nodes.get(gate_id, {}).get("type") == "human-gate",
                f"Join '{node_id}' human_gate_id must reference a human-gate",
            )
    for node_id in join_map:
        check(
            f"join_{node_id}_node_exists",
            node_id in nodes,
            f"Join contract references unknown node '{node_id}'",
        )


def check_v11_budgets(graph):
    """Check that declared budgets cover structural lower bounds."""
    if graph.get("schema_version") != "v1.1":
        return
    nodes = graph.get("nodes", [])
    budget = graph.get("budget", {})
    workers = sum(1 for node in nodes if node.get("type") == "worker")
    model_nodes = sum(1 for node in nodes if node.get("type") != "human-gate")
    max_fanout = max(
        (
            sum(
                1 for edge in graph.get("edges", [])
                if edge.get("from") == node.get("id") and edge.get("type") in ("data", "control")
            )
            for node in nodes
        ),
        default=0,
    )
    tool_count = sum(len(node.get("tools", [])) for node in nodes if isinstance(node.get("tools", []), list))
    write_count = sum(
        len(node.get("resources", {}).get("writes", []))
        for node in nodes
        if isinstance(node.get("resources", {}), dict)
    )
    max_loop_cap = max((node.get("loop_cap", 0) for node in nodes if node.get("type") == "worker"), default=0)
    caps = graph.get("caps", {})
    lower_bounds = {
        "max_model_calls": model_nodes,
        "max_spawned_agents": max(workers, caps.get("max_spawned_agents", 0)),
        "max_concurrency": max_fanout,
        "max_tool_calls": tool_count,
        "max_retries": max_loop_cap,
        "max_graph_writes": write_count,
    }
    for name, lower_bound in lower_bounds.items():
        check(
            f"budget_{name}_covers_graph",
            budget.get(name, 0) >= lower_bound,
            f"Budget {name}={budget.get(name)} is below structural lower bound {lower_bound}",
        )


def check_failure_edge_targets_reviewed_worker(graph):
    """Failure edges must route back to the same worker the reviewer reviewed."""
    nodes = {n.get("id"): n for n in graph.get("nodes", [])}
    for index, edge in enumerate(graph.get("edges", [])):
        if edge.get("type") != "failure":
            continue
        reviewer_id = edge.get("from")
        target_id = edge.get("to")
        if graph.get("schema_version") == "v1.1":
            reviewed_worker = reviewed_worker_id(graph, reviewer_id)
            valid_targets = {reviewed_worker} if reviewed_worker is not None else set()
        else:
            reviewed_worker = None
            valid_targets = reviewed_worker_ids(graph, reviewer_id)
        check(
            f"failure_edge_{index}_targets_reviewed_worker",
            target_id in valid_targets,
            f"Failure edge {index} from reviewer '{reviewer_id}' targets worker '{target_id}' but reviewed workers are {sorted(valid_targets)} — failure feedback must route to a reviewed worker",
        )


def check_reviewer_has_pass_and_fail_routes(graph):
    """Every reviewer must have both a pass (data/control) and fail (failure) route."""
    edges = graph.get("edges", [])
    for node in graph.get("nodes", []):
        if node.get("type") != "reviewer":
            continue
        nid = node.get("id")
        has_pass = any(e.get("from") == nid and e.get("type") in ("data", "control") for e in edges)
        has_fail = any(e.get("from") == nid and e.get("type") == "failure" for e in edges)
        check(
            f"reviewer_{nid}_has_pass_route",
            has_pass,
            f"Reviewer '{nid}' has no pass route (data/control edge) — passed reviews must flow forward",
        )
        check(
            f"reviewer_{nid}_has_fail_route",
            has_fail,
            f"Reviewer '{nid}' has no fail route (failure edge) — failed reviews must route back",
        )


def check_retry_cap_exhaustion_routes_to_human(graph):
    """Workers with loop_caps that have failure edges must also have a path to a human gate."""
    nodes = {n.get("id"): n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])
    # Find workers that are failure targets (have retry loops)
    for edge in edges:
        if edge.get("type") != "failure":
            continue
        worker_id = edge.get("to")
        worker = nodes.get(worker_id, {})
        if worker.get("type") != "worker":
            continue
        # Check if there's a path from this worker to a human-gate via data/control edges
        adjacency = {nid: set() for nid in nodes}
        for e in edges:
            if e.get("type") in ("data", "control") and e.get("from") in adjacency and e.get("to") in adjacency:
                adjacency[e["from"]].add(e["to"])
        # BFS from worker to find any human-gate
        visited = set()
        queue = [worker_id]
        found_gate = False
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            if nodes.get(current, {}).get("type") == "human-gate":
                found_gate = True
                break
            queue.extend(adjacency.get(current, set()))
        check(
            f"worker_{worker_id}_retry_cap_routes_to_human",
            found_gate,
            f"Worker '{worker_id}' has a failure/retry loop but no path to a human-gate — retry cap exhaustion must route to a human, not silently end",
        )


def check_no_duplicate_edges(graph):
    """No two edges should have the same from, to, and type."""
    seen = set()
    for index, edge in enumerate(graph.get("edges", [])):
        key = (edge.get("from"), edge.get("to"), edge.get("type"))
        check(
            f"edge_{index}_not_duplicate",
            key not in seen,
            f"Edge {index} ({edge.get('from')} → {edge.get('to')} type={edge.get('type')}) is a duplicate",
        )
        seen.add(key)


def check_reviewer_contract_emits_report(graph):
    """Reviewer nodes must produce a review report output."""
    for node in graph.get("nodes", []):
        if node.get("type") != "reviewer":
            continue
        nid = node.get("id")
        outputs = node.get("outputs", [])
        if graph.get("schema_version") == "v1.1":
            report_ports = [
                port for port in node.get("output_ports", [])
                if isinstance(port, dict) and port.get("name") in ("review_report", "review-report")
            ]
            has_report = bool(report_ports) and report_ports[0].get("schema", {}).get("$ref") == "schemas/review-report.schema.json"
            check(
                f"reviewer_{nid}_emits_review_report",
                has_report,
                f"Reviewer '{nid}' must expose the review-report schema through a typed output port",
            )
            continue
        has_report = any("review" in o.lower() or "report" in o.lower() or "feedback" in o.lower() for o in outputs if isinstance(o, str))
        check(
            f"reviewer_{nid}_emits_review_report",
            has_report,
            f"Reviewer '{nid}' outputs {outputs} do not mention review/report/feedback — reviewer must emit a structured review report",
        )


def check_structural_reachability_and_cycles(graph):
    """Require a reachable DAG for data/control flow; recovery loops use failure edges."""
    nodes = graph.get("nodes", [])
    node_ids = [node.get("id") for node in nodes]
    known_ids = {node_id for node_id in node_ids}
    adjacency = {node_id: set() for node_id in known_ids}
    incoming = {node_id: 0 for node_id in known_ids}
    for edge in graph.get("edges", []):
        if edge.get("type") in ("data", "control") and edge.get("from") in known_ids and edge.get("to") in known_ids:
            source, target = edge["from"], edge["to"]
            adjacency[source].add(target)
            incoming[target] += 1

    root_candidates = [node_id for node_id, count in incoming.items() if count == 0]
    planner_roots = [node_id for node_id in root_candidates if next(node for node in nodes if node.get("id") == node_id).get("type") == "planner"]
    inferred_entries = planner_roots or root_candidates
    declared_entry = graph.get("entry_node")
    if declared_entry is not None:
        check("declared_entry_exists", declared_entry in known_ids, f"Declared entry node '{declared_entry}' does not exist")
        check("declared_entry_has_no_parent", declared_entry in root_candidates, f"Declared entry node '{declared_entry}' must not have a data/control parent")
        entries = [declared_entry] if declared_entry in known_ids else []
    else:
        entries = inferred_entries
        check("structural_entry_exists", bool(entries), "Data/control graph has no entry node")

    reachable = set(entries)
    pending = list(entries)
    while pending:
        current = pending.pop()
        for target in adjacency[current]:
            if target not in reachable:
                reachable.add(target)
                pending.append(target)
    check(
        "all_nodes_structurally_reachable",
        reachable == known_ids,
        f"Unreachable nodes: {sorted(known_ids - reachable)}",
    )

    colors = {node_id: 0 for node_id in known_ids}

    def visit(node_id):
        colors[node_id] = 1
        for target in adjacency[node_id]:
            if colors[target] == 1:
                return False
            if colors[target] == 0 and not visit(target):
                return False
        colors[node_id] = 2
        return True

    acyclic = all(visit(node_id) for node_id in known_ids if colors[node_id] == 0)
    check(
        "data_control_graph_acyclic",
        acyclic,
        "Data/control edges contain a cycle; use a bounded failure edge for review recovery instead",
    )


def check_failure_edge_semantics(graph):
    nodes = {node.get("id"): node for node in graph.get("nodes", [])}
    for index, edge in enumerate(graph.get("edges", [])):
        if edge.get("type") != "failure":
            continue
        source = nodes.get(edge.get("from"), {})
        target = nodes.get(edge.get("to"), {})
        check(
            f"failure_edge_{index}_from_reviewer",
            source.get("type") == "reviewer",
            f"Failure edge {index} must originate at a reviewer",
        )
        check(
            f"failure_edge_{index}_to_worker",
            target.get("type") == "worker",
            f"Failure edge {index} must return feedback to a worker",
        )
        check(
            f"failure_edge_{index}_target_is_bounded",
            isinstance(target.get("loop_cap"), int) and target.get("loop_cap", 0) >= 1,
            f"Failure target '{edge.get('to')}' must declare a positive loop_cap",
        )


def check_runtime_refs(graph, runtime_root=None):
    """Optionally verify graph runtime skill references against a local repo root."""
    refs = graph.get("runtime_refs", [])
    if not refs:
        return
    check("runtime_refs_is_list", isinstance(refs, list), "runtime_refs must be a list of skill names")
    if not isinstance(refs, list):
        return
    if not runtime_root:
        check(
            "runtime_root_required_for_refs",
            False,
            "runtime_refs require --runtime-root; refusing to guess or perform network discovery",
        )
        return

    root = os.path.realpath(runtime_root)
    skills_root = os.path.realpath(os.path.join(root, "skills"))
    for ref in refs:
        safe_ref = isinstance(ref, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]+", ref))
        check(f"runtime_ref_{ref}_is_safe", safe_ref, f"Runtime reference '{ref}' must be a simple skill directory name")
        if safe_ref:
            skill_path = os.path.realpath(os.path.join(skills_root, ref, "SKILL.md"))
            try:
                inside = os.path.commonpath([skills_root, skill_path]) == skills_root
            except ValueError:
                inside = False
            check(f"runtime_ref_{ref}_inside_skills_root", inside, f"Runtime reference '{ref}' escapes the skills root")
            check(
                f"runtime_ref_{ref}_exists",
                inside and os.path.isfile(skill_path),
                f"Runtime skill '{ref}' not found at {skill_path}",
            )


def check_node_single_responsibility(graph, rules):
    nodes = graph.get("nodes", [])
    for node in nodes:
        resp = node.get("responsibility", "")
        nid = node.get("id", "unknown")
        # Check for "and" joining two distinct tasks (heuristic)
        # This is a soft check — not all "and" means dual responsibility
        if re.search(r'\bAND\b', resp, re.IGNORECASE):
            # Check if it's joining two verbs (strong signal of dual responsibility)
            if re.search(r'(write|research|review|plan|merge|approve|deploy|send|publish|generate|analyze|check|validate|create|build|design)\s+\w+\s+AND\s+(write|research|review|plan|merge|approve|deploy|send|publish|generate|analyze|check|validate|create|build|design)', resp, re.IGNORECASE):
                check(
                    f"node_{nid}_single_responsibility",
                    False,
                    f"Node '{nid}' responsibility contains dual-task pattern: '{resp}'. Split into two nodes.",
                )
            else:
                warn(f"node_{nid}_responsibility_has_and", f"Responsibility contains 'and' — verify it's truly one job: '{resp}'")
        else:
            check(f"node_{nid}_single_responsibility", True)


def check_node_types_valid(graph, rules):
    valid_types = set(rules.get("rules", {}).get("valid_node_types", ["planner", "worker", "reviewer", "synthesizer", "human-gate"])) if rules else {"planner", "worker", "reviewer", "synthesizer", "human-gate"}
    for node in graph.get("nodes", []):
        nid = node.get("id", "unknown")
        ntype = node.get("type", "")
        check(
            f"node_{nid}_type_valid",
            ntype in valid_types,
            f"Node '{nid}' has invalid type '{ntype}'. Must be one of: {valid_types}",
        )


def check_edges_have_dependency_reason(graph):
    for i, edge in enumerate(graph.get("edges", [])):
        reason = edge.get("dependency_reason", "")
        check(
            f"edge_{i}_dependency_reason",
            reason and reason.strip(),
            f"Edge {i} ({edge.get('from', '?')} → {edge.get('to', '?')}) has no dependency_reason — fake edges must be deleted",
        )


def check_no_fake_edges(graph, rules):
    fake_patterns = rules.get("rules", {}).get("fake_edge_patterns", ["related", "flows naturally", "next step", "sequential", "just because"]) if rules else ["related", "flows naturally", "next step", "sequential", "just because"]
    for i, edge in enumerate(graph.get("edges", [])):
        reason = edge.get("dependency_reason", "").lower()
        for pattern in fake_patterns:
            if pattern in reason:
                check(
                    f"edge_{i}_not_fake",
                    False,
                    f"Edge {i} dependency_reason '{reason}' matches fake-edge pattern '{pattern}' — delete this edge",
                )
                break
        else:
            check(f"edge_{i}_not_fake", True)


def check_reviewers_exist_for_workers(graph):
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])
    for node in graph.get("nodes", []):
        if node.get("type") == "worker":
            nid = node.get("id")
            # Find edges from this worker to a reviewer
            has_reviewer = any(
                e.get("from") == nid and nodes.get(e.get("to"), {}).get("type") == "reviewer"
                for e in edges
            )
            check(
                f"worker_{nid}_has_reviewer",
                has_reviewer,
                f"Worker '{nid}' has no reviewer — never let an agent grade its own homework",
            )


def check_no_self_review(graph):
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])
    for edge in edges:
        from_id = edge.get("from", "")
        to_id = edge.get("to", "")
        from_node = nodes.get(from_id, {})
        to_node = nodes.get(to_id, {})
        if from_node.get("type") == "worker" and to_node.get("type") == "reviewer":
            # Check the reviewer doesn't review its own work
            # A self-review is when the reviewer's inputs include the worker's id
            # AND the reviewer is the same agent as the worker (we check by id difference)
            check(
                f"no_self_review_{from_id}_{to_id}",
                from_id != to_id,
                f"Reviewer '{to_id}' is reviewing its own work (same as worker '{from_id}') — use a separate reviewer",
            )


def check_reviewer_unique_questions(graph, rules):
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])
    max_reviewers = rules.get("rules", {}).get("max_reviewers_per_node", 5) if rules else 5
    for reviewer in graph.get("nodes", []):
        if reviewer.get("type") != "reviewer":
            continue
        questions = reviewer.get("review_questions", [])
        check(
            f"reviewer_{reviewer.get('id')}_has_one_question",
            isinstance(questions, list) and len(questions) == 1 and isinstance(questions[0], str) and questions[0].strip(),
            f"Reviewer '{reviewer.get('id')}' must ask exactly one non-empty review question",
        )
    # Group reviewers by the worker they review
    worker_reviewers = {}
    for edge in edges:
        from_id = edge.get("from", "")
        to_id = edge.get("to", "")
        from_node = nodes.get(from_id, {})
        to_node = nodes.get(to_id, {})
        if from_node.get("type") == "worker" and to_node.get("type") == "reviewer":
            worker_reviewers.setdefault(from_id, []).append(to_id)

    for worker_id, reviewer_ids in worker_reviewers.items():
        check(
            f"worker_{worker_id}_reviewer_count_within_cap",
            len(reviewer_ids) <= max_reviewers,
            f"Worker '{worker_id}' has {len(reviewer_ids)} reviewers, exceeding max_reviewers_per_node ({max_reviewers})",
        )
        questions = []
        for rid in reviewer_ids:
            rq = nodes.get(rid, {}).get("review_questions", [])
            questions.extend(rq)
        # Check for duplicates (case-insensitive)
        lower_questions = [q.lower().strip() for q in questions]
        duplicates = [q for q in lower_questions if lower_questions.count(q) > 1]
        check(
            f"worker_{worker_id}_unique_review_questions",
            len(duplicates) == 0,
            f"Worker '{worker_id}' has duplicate reviewer questions: {set(duplicates)} — overlapping reviewers repeat blind spots",
        )


def check_loop_caps(graph, rules):
    caps = graph.get("caps", {})
    max_review_rounds = caps.get("max_review_rounds", rules.get("rules", {}).get("max_review_rounds", 3) if rules else 3)
    max_spawned = caps.get("max_spawned_agents", rules.get("rules", {}).get("max_spawned_agents", 8) if rules else 8)
    max_total = caps.get("max_total_agents", rules.get("rules", {}).get("max_total_agents", 20) if rules else 20)

    # Check individual node loop_caps
    for node in graph.get("nodes", []):
        if node.get("type") == "worker" and "loop_cap" in node:
            lc = node["loop_cap"]
            check(
                f"node_{node['id']}_loop_cap_within_limit",
                lc <= max_review_rounds,
                f"Node '{node['id']}' loop_cap ({lc}) exceeds max_review_rounds ({max_review_rounds})",
            )

    # Check spawned agents (workers at the same level)
    worker_count = sum(1 for n in graph.get("nodes", []) if n.get("type") == "worker")
    check(
        "spawned_agents_within_cap",
        worker_count <= max_spawned,
        f"Worker count ({worker_count}) exceeds max_spawned_agents ({max_spawned})",
    )

    # Check total agents
    total_nodes = len(graph.get("nodes", []))
    check(
        "total_agents_within_cap",
        total_nodes <= max_total,
        f"Total node count ({total_nodes}) exceeds max_total_agents ({max_total})",
    )


def check_human_gates_for_expensive_actions(graph, rules):
    expensive_actions = set(rules.get("rules", {}).get("require_human_gate_for_actions", ["publish", "send", "refund", "invoice", "deploy", "delete"])) if rules else {"publish", "send", "refund", "invoice", "deploy", "delete"}
    node_map = {node.get("id"): node for node in graph.get("nodes", [])}
    incoming = {node_id: 0 for node_id in node_map}
    outgoing = {node_id: 0 for node_id in node_map}
    for edge in graph.get("edges", []):
        if edge.get("type") in ("data", "control"):
            if edge.get("to") in incoming:
                incoming[edge["to"]] += 1
            if edge.get("from") in outgoing:
                outgoing[edge["from"]] += 1
    for node in graph.get("nodes", []):
        if node.get("type") == "human-gate":
            node_id = node.get("id")
            check(
                f"human_gate_{node_id}_has_predecessor",
                incoming.get(node_id, 0) > 0,
                f"Human-gate node '{node_id}' must follow a data/control predecessor",
            )
            check(
                f"human_gate_{node_id}_is_terminal",
                outgoing.get(node_id, 0) == 0,
                f"Human-gate node '{node_id}' must be terminal before the external irreversible action",
            )
    declared_positions = set()
    for index, gate in enumerate(graph.get("human_gates", [])):
        position = gate.get("position")
        declared_positions.add(position)
        check(
            f"human_gate_{index}_position_exists",
            position in node_map and node_map[position].get("type") == "human-gate",
            f"Human gate position '{position}' must reference a human-gate node",
        )
        check(
            f"human_gate_{index}_action_is_string",
            isinstance(gate.get("action"), str) and gate.get("action", "").strip(),
            f"Human gate {index} must declare a non-empty action",
        )
    for node in graph.get("nodes", []):
        if node.get("type") == "human-gate":
            check(
                f"human_gate_{node.get('id')}_declared",
                node.get("id") in declared_positions,
                f"Human-gate node '{node.get('id')}' is not listed in human_gates",
            )
    human_gates = graph.get("human_gates", [])
    gated_actions = {g.get("action", "").lower() for g in human_gates}

    # Also check human-gate nodes
    for node in graph.get("nodes", []):
        if node.get("type") == "human-gate":
            action = node.get("human_gate_action", "").lower()
            if action:
                gated_actions.add(action)

    for action in expensive_actions:
        # Check if any node references this action
        has_action = any(
            action in n.get("human_gate_action", "").lower()
            or action in n.get("responsibility", "").lower()
            for n in graph.get("nodes", [])
        )
        if has_action:
            check(
                f"human_gate_for_{action}",
                action in gated_actions,
                f"Action '{action}' is expensive to undo but has no human gate — place a gate before it",
            )


def check_failure_paths(graph):
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])
    # Check that reviewer nodes have a failure edge
    for node in graph.get("nodes", []):
        if node.get("type") == "reviewer":
            nid = node.get("id")
            has_failure_edge = any(
                e.get("from") == nid and e.get("type") == "failure"
                for e in edges
            )
            check(
                f"reviewer_{nid}_has_failure_path",
                has_failure_edge,
                f"Reviewer '{nid}' has no failure edge — failed checks must route back, not end the run",
            )


def check_one_writer_per_file(graph):
    if graph.get("schema_version") == "v1.1":
        return
    warn(
        "legacy_writer_contract_untyped",
        "v1 output descriptions are prose; writer exclusivity is enforced only by v1.1 resources.writes and locks",
    )


def check_tool_auto_revocation(graph, rules_path=None):
    """ECC Auto-Revocation: gate tools declared in node `tools` arrays.

    Core tools are never gated. Workflow tools fail loud if missing.
    Advisory tools skip silently if missing (warn only).
    This mirrors the ECC operating protocol's tool taxonomy so graph
    definitions stay honest about runtime availability.
    """
    try:
        policy = load_tool_policy(rules_path or DEFAULT_RULES_PATH)
    except ValueError as exc:
        check("tool_policy_loads", False, f"Tool policy is invalid; validation is fail-closed: {exc}")
        return
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_tools = node.get("tools", [])
        if not isinstance(node_tools, list):
            continue  # check_tools_well_formed owns the hard failure
        for tool in node_tools:
            declaration = normalize_tool(tool)
            if declaration is None:
                continue
            tool_name = declaration["name"]
            category = classify_tool(tool_name, policy)
            if category == "unknown":
                check(
                    f"tool_{node.get('id')}_{tool_name}_known",
                    False,
                    f"Unknown tool '{tool_name}' (node '{node.get('id')}') is blocked; add it to the shared policy taxonomy",
                )
                continue
            if not executable_available(tool_name):
                if category == "workflow" or (category == "unknown" and declaration["required"]):
                    check(
                        f"tool_{node.get('id')}_{tool_name}_available",
                        False,
                        f"Required tool '{tool_name}' (node '{node.get('id')}') is not installed — "
                        f"install it or remove the node dependency; do not silently skip",
                    )
                else:
                    warn(
                        f"tool_{node.get('id')}_{tool_name}_skipped",
                        f"Optional/advisory tool '{tool_name}' (node '{node.get('id')}') is not installed — degrading",
                    )


def print_summary(graph):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    human_gates = graph.get("human_gates", [])

    node_types = {}
    for n in nodes:
        t = n.get("type", "unknown")
        node_types[t] = node_types.get(t, 0) + 1

    edge_types = {}
    for e in edges:
        t = e.get("type", "unknown")
        edge_types[t] = edge_types.get(t, 0) + 1

    reviewers = [
        {"node": n["id"], "questions": n.get("review_questions", [])}
        for n in nodes if n.get("type") == "reviewer"
    ]

    print("\n" + "=" * 60)
    print("GRAPH SUMMARY REPORT")
    print("=" * 60)
    print(f"\nGraph: {graph.get('name', 'unnamed')}")
    print(f"Description: {graph.get('description', 'none')}")
    print(f"\nNodes ({len(nodes)} total):")
    for ntype, count in sorted(node_types.items()):
        print(f"  {ntype}: {count}")
    print(f"\nEdges ({len(edges)} total):")
    for etype, count in sorted(edge_types.items()):
        print(f"  {etype}: {count}")
    print(f"\nReview assignments ({len(reviewers)}):")
    for r in reviewers:
        questions = r["questions"] if r["questions"] else ["(no question specified)"]
        for q in questions:
            print(f"  {r['node']}: {q}")
    print(f"\nHuman gates ({len(human_gates)}):")
    for g in human_gates:
        print(f"  Position: {g.get('position', '?')} — Action: {g.get('action', '?')}")
    caps = graph.get("caps", {})
    print(f"\nCaps:")
    print(f"  max_review_rounds: {caps.get('max_review_rounds', 3)}")
    print(f"  max_spawned_agents: {caps.get('max_spawned_agents', 8)}")
    print(f"  max_total_agents: {caps.get('max_total_agents', 20)}")
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")
    print("\n" + "=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_graph.py [--rules <rules.json>] <graph-definition.json>")
        sys.exit(1)

    args = sys.argv[1:]
    rules_path = DEFAULT_RULES_PATH
    runtime_root = None
    graph_path = None
    review_report_paths = []

    i = 0
    while i < len(args):
        if args[i] == "--rules":
            if i + 1 >= len(args):
                print("ERROR: --rules requires a path")
                sys.exit(1)
            rules_path = args[i + 1]
            i += 2
        elif args[i] == "--runtime-root":
            if i + 1 >= len(args):
                print("ERROR: --runtime-root requires a repository path")
                sys.exit(1)
            runtime_root = args[i + 1]
            i += 2
        elif args[i] == "--review-report":
            if i + 1 >= len(args):
                print("ERROR: --review-report requires a path")
                sys.exit(1)
            review_report_paths.append(args[i + 1])
            i += 2
        else:
            if graph_path is not None:
                print(f"ERROR: unexpected argument: {args[i]}")
                sys.exit(1)
            graph_path = args[i]
            i += 1

    if not graph_path:
        print("ERROR: No graph definition file specified")
        sys.exit(1)

    rules = load_rules(rules_path)
    graph = load_graph(graph_path)

    print(f"Validating graph: {graph_path}")
    print(f"Rules: {rules_path if rules else 'defaults'}\n")

    # Hard checks (exit 1 on failure)
    check_graph_shape(graph)
    check_json_schema(graph)
    check_review_reports(graph, review_report_paths)
    if checks_failed:
        print(f"\nSchema/shape checks failed; semantic validation was not attempted.")
        print(f"Checks passed: {checks_passed}")
        print(f"Checks failed: {checks_failed}")
        print(f"FAILED checks: {failures}")
        print("RESULT: FAIL (exit 1)")
        sys.exit(1)
    check_diagram_present(graph)
    check_nodes_exist(graph)
    check_node_edge_contracts(graph, rules)
    check_non_empty_outputs(graph)
    check_tools_well_formed(graph)
    check_v11_typed_contracts(graph)
    check_v11_resources_and_exhaustion(graph)
    check_v11_joins(graph)
    check_v11_budgets(graph)
    check_no_duplicate_edges(graph)
    check_structural_reachability_and_cycles(graph)
    check_failure_edge_semantics(graph)
    check_failure_edge_targets_reviewed_worker(graph)
    check_reviewer_has_pass_and_fail_routes(graph)
    check_retry_cap_exhaustion_routes_to_human(graph)
    check_reviewer_contract_emits_report(graph)
    check_runtime_refs(graph, runtime_root)
    check_node_types_valid(graph, rules)
    check_node_single_responsibility(graph, rules)
    check_edges_have_dependency_reason(graph)
    check_no_fake_edges(graph, rules)
    check_reviewers_exist_for_workers(graph)
    check_no_self_review(graph)
    check_reviewer_unique_questions(graph, rules)
    check_loop_caps(graph, rules)
    check_human_gates_for_expensive_actions(graph, rules)
    check_failure_paths(graph)
    check_one_writer_per_file(graph)
    check_tool_auto_revocation(graph, rules_path)

    print(f"\n{'─' * 40}")
    print(f"Checks passed: {checks_passed}")
    print(f"Checks failed: {checks_failed}")

    if checks_failed > 0:
        print(f"\nFAILED checks: {failures}")
        print("\n" + "=" * 60)
        print("RESULT: FAIL (exit 1)")
        print("=" * 60)
        sys.exit(1)

    print_summary(graph)
    print("\nRESULT: PASS (exit 0)")
    sys.exit(0)


if __name__ == "__main__":
    main()
