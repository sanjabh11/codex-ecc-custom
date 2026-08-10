#!/usr/bin/env python3
"""Regression tests for the proof-tiered skill usage audit."""

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scripts.skill_usage_audit import audit_usage, load_skill_manifest, load_source_manifest, sha256_file  # noqa: E402


def write_jsonl(path: Path, events: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


def meta(session_id: str, timestamp: str) -> dict:
    return {"type": "session_meta", "timestamp": timestamp, "payload": {"type": "session_meta", "id": session_id}}


def user_message(text: str, *, with_context: bool = False, timestamp: str = "2026-07-01T00:01:00Z") -> dict:
    blocks = []
    if with_context:
        blocks.append({"type": "input_text", "text": "<recommended_plugins>\n@alpha\n"})
        blocks.append({"type": "input_text", "text": "# AGENTS.md instructions\n@alpha\n"})
    blocks.append({"type": "input_text", "text": text})
    return {
        "type": "response_item",
        "timestamp": timestamp,
        "payload": {"type": "message", "role": "user", "content": blocks},
    }


class SkillUsageAuditTests(unittest.TestCase):
    def test_context_is_excluded_and_selector_is_deduplicated_by_session(self):
        with self.subTest("fixture setup"):
            import tempfile

            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                sessions = root / "sessions"
                sessions.mkdir()
                write_jsonl(
                    sessions / "one.jsonl",
                    [
                        meta("session-1", "2026-07-01T00:00:00Z"),
                        user_message("Use @alpha to audit the repository.", with_context=True),
                        user_message("Use @alpha again for the verification pass."),
                    ],
                )
                result = audit_usage(
                    session_roots=[sessions],
                    skill_root=root / "skills",
                    inventory_csv=None,
                    start=datetime(2026, 6, 10, tzinfo=timezone.utc),
                    end=datetime(2026, 8, 10, 23, 59, tzinfo=timezone.utc),
                    extra_skills=["alpha"],
                )
                alpha = next(item for item in result["skills"] if item["name"] == "alpha")
                self.assertEqual(alpha["selector_prompt_count"], 2)
                self.assertEqual(alpha["selector_session_count"], 1)
                self.assertEqual(result["source_coverage"]["excluded_context_blocks"], 2)
                self.assertEqual(result["source_coverage"]["user_prompt_count"], 2)

    def test_malformed_lines_and_out_of_window_sessions_are_not_false_usage(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sessions = root / "sessions"
            sessions.mkdir()
            path = sessions / "mixed.jsonl"
            write_jsonl(
                path,
                [
                    meta("old", "2026-01-01T00:00:00Z"),
                    user_message("@alpha old", timestamp="2026-01-01T00:01:00Z"),
                    meta("current", "2026-07-02T00:00:00Z"),
                    user_message("@alpha current", timestamp="2026-07-02T00:01:00Z"),
                ],
            )
            path.write_text(path.read_text(encoding="utf-8") + "not-json\n", encoding="utf-8")
            result = audit_usage(
                session_roots=[sessions],
                skill_root=root / "skills",
                inventory_csv=None,
                start=datetime(2026, 6, 10, tzinfo=timezone.utc),
                end=datetime(2026, 8, 10, 23, 59, tzinfo=timezone.utc),
                extra_skills=["alpha"],
            )
            alpha = next(item for item in result["skills"] if item["name"] == "alpha")
            self.assertEqual(alpha["selector_prompt_count"], 1)
            self.assertEqual(alpha["selector_session_count"], 1)
            self.assertEqual(result["source_coverage"]["active_source_file_count"], 1)
            self.assertEqual(result["source_coverage"]["malformed_jsonl_lines"], 1)

    def test_source_manifest_is_hash_bound_and_fails_closed_on_drift(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "frozen.jsonl"
            write_jsonl(source, [meta("frozen", "2026-07-02T00:00:00Z")])
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "skill-usage-source-manifest.v1",
                        "files": [{"path": str(source), "sha256": sha256_file(source)}],
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(load_source_manifest(manifest), [source.resolve()])
            source.write_text(source.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_source_manifest(manifest)

    def test_skill_manifest_binds_skill_files_and_inventory(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = root / "skills"
            skill_dir = skill_root / "demo"
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text("---\nname: demo\ndescription: demo\n---\n", encoding="utf-8")
            inventory = root / "skill-inventory.csv"
            inventory.write_text("name,categories\ndemo,testing\n", encoding="utf-8")
            manifest = root / "skill-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "skill-usage-skill-manifest.v1",
                        "skill_root": str(skill_root.resolve()),
                        "inventory_csv": str(inventory.resolve()),
                        "inventory_sha256": sha256_file(inventory),
                        "files": [{"path": str(skill_file), "sha256": sha256_file(skill_file)}],
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                load_skill_manifest(manifest, skill_root=skill_root, inventory_csv=inventory),
                1,
            )
            skill_file.write_text(skill_file.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_skill_manifest(manifest, skill_root=skill_root, inventory_csv=inventory)

    def test_top_level_actions_are_separate_from_lower_confidence_wrapper_call_sites(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sessions = root / "sessions"
            sessions.mkdir()
            write_jsonl(
                sessions / "actions.jsonl",
                [
                    meta("session-actions", "2026-07-03T00:00:00Z"),
                    {
                        "type": "response_item",
                        "timestamp": "2026-07-03T00:01:00Z",
                        "payload": {
                            "type": "custom_tool_call",
                            "name": "exec",
                            "input": "const r = await tools.apply_patch({}); text('tools.fake()');",
                        },
                    },
                ],
            )
            result = audit_usage(
                session_roots=[sessions],
                skill_root=root / "skills",
                inventory_csv=None,
                start=datetime(2026, 6, 10, tzinfo=timezone.utc),
                end=datetime(2026, 8, 10, 23, 59, tzinfo=timezone.utc),
            )
            self.assertEqual(result["actions"]["top_level"][0]["action"], "exec")
            nested = {row["action"]: row for row in result["actions"]["nested_call_sites"]}
            self.assertIn("apply_patch", nested)
            self.assertEqual(nested["apply_patch"]["proof_level"], "L3-wrapper-call-site")
            self.assertIn("not host-activation proof", nested["apply_patch"]["warning"])

    def test_underutilized_candidates_are_local_relevance_hypotheses(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill_root = root / "skills"
            (skill_root / "security-audit").mkdir(parents=True)
            (skill_root / "security-audit" / "SKILL.md").write_text(
                "---\nname: security-audit\ndescription: Audit security regressions and run tests.\n---\n",
                encoding="utf-8",
            )
            sessions = root / "sessions"
            sessions.mkdir()
            write_jsonl(
                sessions / "usage.jsonl",
                [meta("session-usage", "2026-07-04T00:00:00Z"), user_message("Audit the code and run tests.")],
            )
            result = audit_usage(
                session_roots=[sessions],
                skill_root=skill_root,
                inventory_csv=None,
                start=datetime(2026, 6, 10, tzinfo=timezone.utc),
                end=datetime(2026, 8, 10, 23, 59, tzinfo=timezone.utc),
            )
            candidate = next(item for item in result["underutilized_candidates"] if item["name"] == "security-audit")
            self.assertEqual(candidate["selector_session_count"], 0)
            self.assertGreater(candidate["relevance_score"], 0)
            self.assertGreater(candidate["opportunity_gap_score"], 0)
            self.assertTrue(candidate["quality_signals"]["has_frontmatter"])
            self.assertFalse(candidate["quality_signals"]["has_output_contract"])


if __name__ == "__main__":
    unittest.main()
