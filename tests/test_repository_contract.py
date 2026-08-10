from __future__ import annotations

import datetime as dt
import json
import plistlib
import re
import stat
import unittest
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
DISCOVERY_DIR = ROOT / "discoveries"
WEEKLY_DIR = ROOT / "docs" / "weekly"
EXAMPLES_DIR = ROOT / "examples"

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
FULL_ACTION_SHA = re.compile(r"^[0-9a-f]{40}$")
ISO_DATE_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

DISCOVERY_KEYS = {
    "id",
    "title",
    "category",
    "discovered_on",
    "evidence_window",
    "summary",
    "why_it_matters",
    "caveats",
    "adoption_question",
    "confidence",
    "disposition",
    "sources",
    "example",
    "example_reason",
}
SOURCE_KEYS = {"title", "url", "published_on", "first_party"}
RECENT_CATEGORIES = {"new", "operational-lesson", "tool-watch"}
CATEGORIES = RECENT_CATEGORIES | {"established"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
DISPOSITIONS = {"accepted", "deferred", "rejected"}

WEEKLY_MUTABLE_PATHS = (
    Path("README.md"),
    Path("docs/weekly"),
    Path("discoveries"),
    Path("examples"),
)

SECRET_PATTERNS = {
    "private key": re.compile(
        rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
    ),
    "AWS access key": re.compile(rb"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "Slack token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
}

CLOUD_CREDENTIAL_MARKERS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "AZURE_CLIENT_SECRET",
    "ARM_CLIENT_SECRET",
    "CLOUDFLARE_API_TOKEN",
    "KUBECONFIG",
    "VAULT_TOKEN",
    "TF_TOKEN_",
)

MUTATING_COMMANDS = re.compile(
    r"""
    \b(?:terraform|tofu)
      (?:\s+-[A-Za-z0-9_-]+(?:=(?:"[^"]*"|'[^']*'|[^\s\\]+))?)*
      \s+(?:apply|destroy|import|refresh|plan)\b
    |\bpulumi\s+(?:up|destroy|refresh|import)\b
    |\bkubectl\s+(?:apply|create|delete|replace|patch|set|scale|rollout)\b
    |\bhelm\s+(?:install|upgrade|uninstall|rollback)\b
    |\b(?:aws\s+)?cloudformation\s+(?:deploy|create-stack|update-stack|delete-stack)\b
    |\b(?:aws\s+)?cdk\s+(?:deploy|destroy)\b
    |\bsam\s+(?:deploy|delete)\b
    |\bansible-playbook\b
    |\bpacker\s+build\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def repository_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def parse_date(value: object, location: str, failures: list[str]) -> dt.date | None:
    if not isinstance(value, str):
        failures.append(f"{location}: expected an ISO date string")
        return None
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        failures.append(f"{location}: invalid ISO date {value!r}")
        return None
    if parsed.isoformat() != value:
        failures.append(f"{location}: date must use YYYY-MM-DD")
        return None
    return parsed


def load_discoveries() -> list[tuple[Path, object]]:
    records: list[tuple[Path, object]] = []
    for path in sorted(DISCOVERY_DIR.glob("*.json")):
        try:
            records.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            records.append((path, error))
    return records


def markdown_targets(document: Path) -> set[str]:
    targets: set[str] = set()
    for raw_target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
        target = raw_target.strip()
        if target.startswith("<") and ">" in target:
            target = target[1 : target.index(">")]
        else:
            target = target.split(maxsplit=1)[0]
        target = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not target or urlsplit(target).scheme or target.startswith("mailto:"):
            continue
        targets.add((document.parent / target).resolve().relative_to(ROOT).as_posix().rstrip("/"))
    return targets


def canonical_url(raw_url: str) -> str:
    parsed = urlsplit(raw_url)
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/") or "/",
            parsed.query,
            "",
        )
    )


def strip_hcl_comments(contents: str) -> str:
    contents = re.sub(r"/\*.*?\*/", "", contents, flags=re.DOTALL)
    return "\n".join(
        line
        for line in contents.splitlines()
        if not re.match(r"^\s*(?:#|//)", line)
    )


def operational_files() -> list[Path]:
    files: list[Path] = []
    for directory in (WORKFLOW_DIR, ROOT / "automation", ROOT / "scripts", ROOT / ".codex" / "bin"):
        if directory.is_dir():
            files.extend(path for path in directory.rglob("*") if path.is_file())
    return sorted(set(files))


def mutable_files() -> list[Path]:
    files: list[Path] = []
    for relative in WEEKLY_MUTABLE_PATHS:
        path = ROOT / relative
        if path.is_file() or path.is_symlink():
            files.append(path)
        elif path.is_dir():
            files.extend(
                candidate
                for candidate in path.rglob("*")
                if (candidate.is_file() or candidate.is_symlink())
                and "__pycache__" not in candidate.parts
                and ".terraform" not in candidate.parts
                and candidate.suffix not in {".pyc", ".pyo"}
            )
    return sorted(set(files))


class RepositorySurfaceTests(unittest.TestCase):
    def test_required_repository_surfaces_exist(self) -> None:
        required = {
            ".codex/bin/publish-weekly-pr",
            ".codex/rules/weekly-publisher.rules",
            ".github/workflows/ci.yml",
            ".github/workflows/freshness.yml",
            ".gitignore",
            "AGENTS.md",
            "CLAUDE.md",
            "CONTRIBUTING.md",
            "Makefile",
            "README.md",
            "automation/WEEKLY_PROMPT.md",
            "automation/com.cekapitan.infrastructure-curiosity-weekly.plist",
            "automation/run-weekly.sh",
            "docs/automation.md",
            "scripts/check.sh",
        }
        missing = sorted(path for path in required if not (ROOT / path).is_file())
        self.assertEqual([], missing, f"missing required repository surfaces: {missing}")

        self.assertTrue(list(DISCOVERY_DIR.glob("*.json")), "at least one discovery is required")
        self.assertTrue(list(WEEKLY_DIR.glob("*.md")), "at least one weekly brief is required")
        self.assertTrue(list(EXAMPLES_DIR.rglob("*.tf")), "at least one Terraform example is required")
        self.assertTrue(
            list(EXAMPLES_DIR.rglob("*.tftest.hcl")),
            "at least one mocked Terraform test is required",
        )

    def test_local_markdown_links_resolve(self) -> None:
        failures: list[str] = []
        for document in sorted(ROOT.rglob("*.md")):
            if ".git" in document.parts:
                continue
            for raw_target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
                target = raw_target.strip()
                if target.startswith("<") and ">" in target:
                    target = target[1 : target.index(">")]
                else:
                    target = target.split(maxsplit=1)[0]
                target = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if not target or urlsplit(target).scheme or target.startswith("mailto:"):
                    continue
                try:
                    resolved = (document.parent / target).resolve()
                    resolved.relative_to(ROOT)
                except ValueError:
                    failures.append(f"{document.relative_to(ROOT)} -> escapes repository: {target}")
                    continue
                if not resolved.exists():
                    failures.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual([], failures, "broken or unsafe local Markdown links")

    def test_text_files_are_clean(self) -> None:
        failures: list[str] = []
        checked_suffixes = {".hcl", ".json", ".md", ".plist", ".py", ".sh", ".tf", ".yml", ".yaml"}
        checked_names = {"Makefile"}
        for path in repository_files():
            if path.suffix not in checked_suffixes and path.name not in checked_names:
                continue
            try:
                contents = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                failures.append(f"{path.relative_to(ROOT)}: not UTF-8 text")
                continue
            if contents and not contents.endswith("\n"):
                failures.append(f"{path.relative_to(ROOT)}: missing final newline")
            for number, line in enumerate(contents.splitlines(), 1):
                has_forbidden_tab = path.name != "Makefile" and "\t" in line
                if line.endswith((" ", "\t")) or has_forbidden_tab:
                    failures.append(f"{path.relative_to(ROOT)}:{number}: whitespace")
        self.assertEqual([], failures, "text hygiene violations")


class DiscoveryContractTests(unittest.TestCase):
    def test_discovery_records_follow_the_canonical_schema(self) -> None:
        records = load_discoveries()
        self.assertTrue(records, "no discovery records found")
        failures: list[str] = []

        for path, record in records:
            relative = path.relative_to(ROOT).as_posix()
            if isinstance(record, Exception):
                failures.append(f"{relative}: invalid JSON: {record}")
                continue
            if not isinstance(record, dict):
                failures.append(f"{relative}: top-level value must be an object")
                continue

            missing = sorted(DISCOVERY_KEYS.difference(record))
            if missing:
                failures.append(f"{relative}: missing keys {missing}")
                continue

            discovery_id = record["id"]
            if not nonempty_string(discovery_id) or not SLUG.fullmatch(discovery_id):
                failures.append(f"{relative}: id must be a lowercase kebab-case slug")
            elif discovery_id != path.stem and not discovery_id.startswith(f"{path.stem}-"):
                failures.append(f"{relative}: id must be stable and derived from the filename slug")

            for field in (
                "title",
                "summary",
                "why_it_matters",
                "adoption_question",
                "example_reason",
            ):
                if not nonempty_string(record[field]):
                    failures.append(f"{relative}: {field} must be a non-empty string")

            caveats = record["caveats"]
            if not isinstance(caveats, list) or not caveats or not all(nonempty_string(item) for item in caveats):
                failures.append(f"{relative}: caveats must be a non-empty string array")

            if record["category"] not in CATEGORIES:
                failures.append(f"{relative}: category must be one of {sorted(CATEGORIES)}")
            if record["confidence"] not in CONFIDENCE_LEVELS:
                failures.append(f"{relative}: confidence must be one of {sorted(CONFIDENCE_LEVELS)}")
            if record["disposition"] not in DISPOSITIONS:
                failures.append(f"{relative}: disposition must be one of {sorted(DISPOSITIONS)}")
            elif record["disposition"] != "accepted":
                failures.append(f"{relative}: discovery files contain accepted items only")

            discovered_on = parse_date(record["discovered_on"], f"{relative}.discovered_on", failures)
            window = record["evidence_window"]
            if not isinstance(window, dict) or set(window) != {"start", "end"}:
                failures.append(f"{relative}: evidence_window must contain exactly start and end")
                window_start = window_end = None
            else:
                window_start = parse_date(window["start"], f"{relative}.evidence_window.start", failures)
                window_end = parse_date(window["end"], f"{relative}.evidence_window.end", failures)
                if window_start and window_end:
                    span = (window_end - window_start).days
                    if span < 0 or span > 30:
                        failures.append(f"{relative}: evidence window must span zero to 30 days")
                    if discovered_on and not window_start <= discovered_on <= window_end:
                        failures.append(f"{relative}: discovered_on must fall inside the evidence window")

            sources = record["sources"]
            if not isinstance(sources, list) or not sources:
                failures.append(f"{relative}: sources must be a non-empty array")
                sources = []
            first_party_count = 0
            for index, source in enumerate(sources):
                location = f"{relative}.sources[{index}]"
                if not isinstance(source, dict):
                    failures.append(f"{location}: source must be an object")
                    continue
                missing_source_keys = sorted(SOURCE_KEYS.difference(source))
                if missing_source_keys:
                    failures.append(f"{location}: missing keys {missing_source_keys}")
                    continue
                if not nonempty_string(source["title"]):
                    failures.append(f"{location}: title must be a non-empty string")
                raw_url = source["url"]
                if not nonempty_string(raw_url):
                    failures.append(f"{location}: url must be a non-empty string")
                else:
                    parsed_url = urlsplit(raw_url)
                    if parsed_url.scheme != "https" or not parsed_url.netloc or parsed_url.fragment:
                        failures.append(f"{location}: use a canonical HTTPS URL without a fragment")
                if type(source["first_party"]) is not bool:
                    failures.append(f"{location}: first_party must be a boolean")
                elif source["first_party"]:
                    first_party_count += 1
                parse_date(source["published_on"], f"{location}.published_on", failures)
            if not first_party_count:
                failures.append(f"{relative}: accepted records need at least one first-party source")

            example = record["example"]
            if example is not None:
                if not nonempty_string(example):
                    failures.append(f"{relative}: example must be a repository-relative path or null")
                else:
                    example_path = Path(example)
                    if example_path.is_absolute() or ".." in example_path.parts or not example_path.parts or example_path.parts[0] != "examples":
                        failures.append(f"{relative}: example must stay under examples/")
                    elif not (ROOT / example_path).exists():
                        failures.append(f"{relative}: example path does not exist: {example}")

        self.assertEqual([], failures, "discovery schema violations")

    def test_discovery_ids_and_canonical_source_urls_are_unique(self) -> None:
        ids: defaultdict[str, list[str]] = defaultdict(list)
        urls: defaultdict[str, list[str]] = defaultdict(list)
        failures: list[str] = []
        for path, record in load_discoveries():
            relative = path.relative_to(ROOT).as_posix()
            if not isinstance(record, dict):
                continue
            discovery_id = record.get("id")
            if isinstance(discovery_id, str):
                ids[discovery_id].append(relative)
            sources = record.get("sources", [])
            if not isinstance(sources, list):
                continue
            for source in sources:
                if isinstance(source, dict) and nonempty_string(source.get("url")):
                    urls[canonical_url(source["url"])].append(relative)

        for discovery_id, locations in sorted(ids.items()):
            if len(locations) > 1:
                failures.append(f"duplicate id {discovery_id!r}: {locations}")
        for url, locations in sorted(urls.items()):
            if len(locations) > 1:
                failures.append(f"duplicate source URL {url}: {locations}")
        self.assertEqual([], failures, "discovery deduplication violations")

    def test_recency_categories_are_supported_by_dated_evidence(self) -> None:
        failures: list[str] = []
        for path, record in load_discoveries():
            relative = path.relative_to(ROOT).as_posix()
            if not isinstance(record, dict):
                continue
            window = record.get("evidence_window")
            sources = record.get("sources")
            category = record.get("category")
            if not isinstance(window, dict) or not isinstance(sources, list):
                continue
            local_failures: list[str] = []
            window_start = parse_date(window.get("start"), f"{relative}.evidence_window.start", local_failures)
            window_end = parse_date(window.get("end"), f"{relative}.evidence_window.end", local_failures)
            if not window_start or not window_end:
                continue

            first_party_dates: list[dt.date] = []
            for index, source in enumerate(sources):
                if not isinstance(source, dict) or source.get("first_party") is not True:
                    continue
                published = parse_date(source.get("published_on"), f"{relative}.sources[{index}].published_on", local_failures)
                if published:
                    first_party_dates.append(published)

            if category in RECENT_CATEGORIES and not any(
                window_start <= published <= window_end for published in first_party_dates
            ):
                failures.append(
                    f"{relative}: {category!r} needs first-party evidence published in its evidence window"
                )
            if category == "established" and not any(
                published < window_start for published in first_party_dates
            ):
                failures.append(
                    f"{relative}: 'established' needs dated first-party evidence predating its evidence window"
                )
        self.assertEqual([], failures, "category/evidence-window mismatches")


class DocumentationCatalogTests(unittest.TestCase):
    def test_readme_catalog_links_every_record_brief_and_example(self) -> None:
        readme_targets = markdown_targets(ROOT / "README.md")
        expected = {
            path.relative_to(ROOT).as_posix()
            for path in DISCOVERY_DIR.glob("*.json")
        }
        expected.update(
            path.relative_to(ROOT).as_posix()
            for path in WEEKLY_DIR.glob("*.md")
        )
        expected.update(
            directory.relative_to(ROOT).as_posix()
            for directory in sorted({path.parent for path in EXAMPLES_DIR.rglob("*.tf")})
            if directory != EXAMPLES_DIR and not directory.name == "tests"
        )
        missing = sorted(expected.difference(readme_targets))
        self.assertEqual([], missing, f"README catalog is missing links: {missing}")

    def test_weekly_briefs_are_dated_markdown_with_catalog_context(self) -> None:
        reports = sorted(WEEKLY_DIR.glob("*.md"))
        self.assertTrue(reports, "at least one weekly brief is required")
        failures: list[str] = []
        for report in reports:
            relative = report.relative_to(ROOT).as_posix()
            if not ISO_DATE_NAME.fullmatch(report.name):
                failures.append(f"{relative}: filename must be YYYY-MM-DD.md")
                continue
            report_date = report.stem
            contents = report.read_text(encoding="utf-8")
            if not re.search(rf"(?m)^# .+{re.escape(report_date)}", contents):
                failures.append(f"{relative}: top-level heading must include the report date")
            if not re.search(r"(?im)^## .*(?:accepted|radar|findings|bring these|no additions)", contents):
                failures.append(f"{relative}: include an accepted/radar/findings section")
            if not re.search(r"(?im)^## .*(?:rejected|deferred|not adopted)", contents):
                failures.append(f"{relative}: record rejected or deferred candidates")
        self.assertEqual([], failures, "weekly brief contract violations")


class TerraformSafetyTests(unittest.TestCase):
    def test_terraform_examples_have_no_live_state_or_provisioners(self) -> None:
        terraform_files = sorted(EXAMPLES_DIR.rglob("*.tf"))
        self.assertTrue(terraform_files, "no Terraform examples found")
        failures: list[str] = []
        forbidden_blocks = re.compile(
            r"(?m)^\s*(?:backend\s+\"|cloud\s*\{|provisioner\s+\"|data\s+\"terraform_remote_state\")"
        )
        forbidden_arguments = re.compile(
            r"(?m)^\s*(?:access_key|secret_key|token|shared_credentials_files?|profile)\s*="
        )

        for path in terraform_files:
            relative = path.relative_to(ROOT).as_posix()
            contents = strip_hcl_comments(path.read_text(encoding="utf-8"))
            if forbidden_blocks.search(contents):
                failures.append(f"{relative}: backend, cloud, provisioner, or remote-state block")
            if forbidden_arguments.search(contents):
                failures.append(f"{relative}: provider credential configuration")

        forbidden_artifacts = sorted(
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file()
            and (
                path.name.endswith((".tfstate", ".tfstate.backup"))
                or path.suffix == ".tfvars"
                or path.name.endswith(".auto.tfvars")
                or path.suffix == ".tf.json"
            )
            and ".git" not in path.parts
        )
        if forbidden_artifacts:
            failures.append(f"state, variable-value, or JSON Terraform artifacts: {forbidden_artifacts}")
        self.assertEqual([], failures, "Terraform live-state safety violations")

    def test_every_terraform_example_has_mocked_plan_only_tests(self) -> None:
        example_roots = sorted({path.parent for path in EXAMPLES_DIR.rglob("*.tf")})
        failures: list[str] = []
        for example_root in example_roots:
            relative_root = example_root.relative_to(ROOT).as_posix()
            test_files = sorted(example_root.rglob("*.tftest.hcl"))
            if not test_files:
                failures.append(f"{relative_root}: no .tftest.hcl file")
            if not (example_root / "README.md").is_file():
                failures.append(f"{relative_root}: no README.md")

        test_files = sorted(EXAMPLES_DIR.rglob("*.tftest.hcl"))
        self.assertTrue(test_files, "no Terraform test files found")
        for path in test_files:
            relative = path.relative_to(ROOT).as_posix()
            contents = strip_hcl_comments(path.read_text(encoding="utf-8"))
            if not re.search(r"(?m)^\s*mock_provider\s+\"[A-Za-z0-9_-]+\"\s*\{", contents):
                failures.append(f"{relative}: missing mock_provider")
            run_count = len(re.findall(r"(?m)^\s*run\s+\"[^\"]+\"\s*\{", contents))
            plan_count = len(re.findall(r"(?m)^\s*command\s*=\s*plan\s*$", contents))
            all_commands = re.findall(r"(?m)^\s*command\s*=\s*([^\s#]+)", contents)
            if run_count == 0:
                failures.append(f"{relative}: at least one run block is required")
            if run_count != plan_count or any(command != "plan" for command in all_commands):
                failures.append(
                    f"{relative}: every run must declare command = plan (runs={run_count}, plans={plan_count})"
                )
            override_values = re.findall(r"(?m)^\s*override_during\s*=\s*([^\s#]+)", contents)
            if any(value != "plan" for value in override_values):
                failures.append(f"{relative}: override_during may only be plan")
        self.assertEqual([], failures, "Terraform mocked-test contract violations")

    def test_repository_gate_executes_nested_mocked_tests_without_a_backend(self) -> None:
        gate = (ROOT / "scripts" / "check.sh").read_text(encoding="utf-8")
        self.assertRegex(
            gate,
            r'terraform\s+-chdir="\$terraform_dir"\s+init\s+[^\n]*-backend=false',
            "the gate must initialize every example without a backend",
        )
        self.assertRegex(gate, r'terraform\s+-chdir="\$terraform_dir"\s+validate\b')
        self.assertRegex(gate, r'terraform\s+-chdir="\$terraform_dir"\s+test\b')
        self.assertNotRegex(
            gate,
            r'find\s+"\$terraform_dir"[^\n]*-maxdepth\s+1[^\n]*\.tftest\.hcl',
            "mocked tests live below tests/ and must not be skipped by a depth-one search",
        )


class AutomationSafetyTests(unittest.TestCase):
    def test_weekly_prompt_requires_the_research_and_no_provision_contract(self) -> None:
        prompt = (ROOT / "automation" / "WEEKLY_PROMPT.md").read_text(encoding="utf-8")
        required_phrases = (
            "$last30days",
            "rolling 30-day window",
            "dated first-party source",
            "README.md",
            "docs/weekly/",
            "discoveries/",
            "examples/",
            "make gate",
            ".codex/bin/publish-weekly-pr",
            "command = plan",
        )
        missing = [phrase for phrase in required_phrases if phrase not in prompt]
        self.assertEqual([], missing, f"weekly prompt is missing required guidance: {missing}")
        self.assertRegex(prompt, r"(?i)do not (?:obtain, inspect, or use|use).*credentials")
        self.assertRegex(prompt, r"(?i)do not provision")
        self.assertRegex(prompt, r"(?i)do not (?:invoke|run) `?git`?.*`?gh`?")

    def test_launchd_schedule_is_monday_at_0717(self) -> None:
        plist_path = ROOT / "automation" / "com.cekapitan.infrastructure-curiosity-weekly.plist"
        with plist_path.open("rb") as handle:
            configuration = plistlib.load(handle)

        schedule = configuration.get("StartCalendarInterval")
        entries = schedule if isinstance(schedule, list) else [schedule]
        wanted = {"Weekday": 2, "Hour": 7, "Minute": 17}
        normalized = [
            {key: int(entry.get(key, -1)) for key in wanted}
            for entry in entries
            if isinstance(entry, dict)
        ]
        self.assertIn(wanted, normalized, "launchd must run Monday at 07:17 local time")
        self.assertNotIn("StartInterval", configuration, "use a calendar schedule, not a drifting interval")
        self.assertFalse(configuration.get("RunAtLoad", False), "weekly research must not run at every load")

        arguments = configuration.get("ProgramArguments")
        self.assertIsInstance(arguments, list, "launchd needs ProgramArguments")
        joined_arguments = " ".join(str(argument) for argument in arguments)
        self.assertIn("run-weekly.sh", joined_arguments)
        self.assertIsNone(MUTATING_COMMANDS.search(joined_arguments), "launchd cannot invoke an IaC mutation")

    def test_workflows_and_automation_have_no_cloud_auth_or_mutating_commands(self) -> None:
        failures: list[str] = []
        for path in operational_files():
            relative = path.relative_to(ROOT).as_posix()
            if path.suffix.lower() not in {"", ".plist", ".sh", ".yaml", ".yml"}:
                continue
            contents = path.read_text(encoding="utf-8")
            active_contents = "\n".join(
                line for line in contents.splitlines() if not re.match(r"^\s*#", line)
            ).replace("\\\n", " ")
            command_match = MUTATING_COMMANDS.search(active_contents)
            if command_match:
                failures.append(f"{relative}: forbidden command {command_match.group(0)!r}")
            for marker in CLOUD_CREDENTIAL_MARKERS:
                if marker in contents:
                    failures.append(f"{relative}: cloud credential marker {marker}")
            if path.is_relative_to(WORKFLOW_DIR):
                if re.search(r"(?im)^\s*id-token\s*:", contents):
                    failures.append(f"{relative}: OIDC id-token permission")
                if "aws-actions/configure-aws-credentials" in contents:
                    failures.append(f"{relative}: AWS credential action")
                if re.search(r"\$\{\{\s*secrets\.", contents):
                    failures.append(f"{relative}: workflow secret reference")
        self.assertEqual([], failures, "live cloud/deployment automation violations")

    def test_weekly_runner_delegates_publication_to_the_protected_publisher(self) -> None:
        runner = (ROOT / "automation" / "run-weekly.sh").read_text(encoding="utf-8")
        self.assertIn(".codex/bin/publish-weekly-pr", runner)
        direct_publication = re.compile(
            r"(?m)^\s*(?:git\s+(?:add|commit|push)|gh\s+pr\s+(?:create|merge))\b"
        )
        self.assertIsNone(
            direct_publication.search(runner),
            "the runner must delegate every publication mutation to publish-weekly-pr",
        )

    def test_prompt_and_publisher_agree_on_the_mutable_surface(self) -> None:
        prompt = (ROOT / "automation" / "WEEKLY_PROMPT.md").read_text(encoding="utf-8")
        publisher = (ROOT / ".codex" / "bin" / "publish-weekly-pr").read_text(encoding="utf-8")
        for allowed in ("README.md", "docs/weekly/", "discoveries/", "examples/"):
            self.assertIn(allowed, prompt, f"weekly prompt allowlist is missing {allowed}")
            self.assertIn(allowed, publisher, f"publisher allowlist is missing {allowed}")
        self.assertRegex(prompt, r"do not edit[^\n]*tests/\*\*", "contract tests must stay fixed")
        self.assertIn("tests/*", publisher, "publisher must reject fixed contract tests")
        self.assertIn(".tftest.hcl", prompt, "weekly tests belong beside examples")
        self.assertIn(".tftest.hcl", publisher, "publisher must accept colocated Terraform tests")


class WorkflowContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflows = sorted(WORKFLOW_DIR.glob("*.y*ml"))
        self.assertTrue(self.workflows, "at least one GitHub Actions workflow is required")

    def test_workflows_are_read_only_and_do_not_persist_credentials(self) -> None:
        failures: list[str] = []
        for workflow in self.workflows:
            contents = workflow.read_text(encoding="utf-8")
            relative = workflow.relative_to(ROOT).as_posix()
            if not re.search(r"(?m)^permissions:\s*\n\s+contents:\s*read\s*$", contents):
                failures.append(f"{relative}: missing top-level contents: read")
            if re.search(r"(?m)^\s+[A-Za-z0-9_-]+:\s*write\s*$", contents):
                failures.append(f"{relative}: write permission")
            if re.search(r"(?m)^\s*pull_request_target\s*:", contents):
                failures.append(f"{relative}: pull_request_target is forbidden")
            checkout_count = len(re.findall(r"\buses:\s*['\"]?actions/checkout@", contents))
            persist_false_count = len(re.findall(r"(?m)^\s+persist-credentials:\s*false\s*$", contents))
            if checkout_count and checkout_count != persist_false_count:
                failures.append(f"{relative}: each checkout must set persist-credentials: false")
        self.assertEqual([], failures, "GitHub workflow permission violations")

    def test_external_actions_are_pinned_to_full_commit_shas(self) -> None:
        failures: list[str] = []
        for workflow in self.workflows:
            for number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
                match = re.search(r"\buses:\s*['\"]?([^\s'\"#]+)", line)
                if not match or match.group(1).startswith("./"):
                    continue
                action = match.group(1)
                reference = action.rsplit("@", 1)[-1]
                if "@" not in action or not FULL_ACTION_SHA.fullmatch(reference):
                    failures.append(f"{workflow.name}:{number} -> {action}")
        self.assertEqual([], failures, "external Actions must use full commit SHAs")


class PublisherBoundaryTests(unittest.TestCase):
    def test_publisher_enforces_the_weekly_path_allowlist(self) -> None:
        publisher_path = ROOT / ".codex" / "bin" / "publish-weekly-pr"
        publisher = publisher_path.read_text(encoding="utf-8")
        for allowed in ("README.md", "docs/weekly/", "discoveries/", "examples/"):
            self.assertIn(allowed, publisher, f"publisher allowlist is missing {allowed}")
        for forbidden in (".github/", ".codex/", "automation/", "scripts/", "tests/"):
            self.assertIn(forbidden, publisher, f"publisher must explicitly reject {forbidden}")
        self.assertRegex(
            publisher,
            r"git\s+(?:status\s+--porcelain|diff\s+--name-only)",
            "publisher must enumerate the actual changed paths",
        )
        self.assertRegex(publisher, r"\bgh\s+pr\s+create\b")
        self.assertNotRegex(publisher, r"\bgh\s+pr\s+merge\b|--auto\b")
        self.assertNotRegex(publisher, r"(?m)git\s+push[^\n]*(?:\bmain\b|HEAD:main)")

        mode = publisher_path.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR, "publisher must be executable by its owner")
        self.assertFalse(mode & (stat.S_IWGRP | stat.S_IWOTH), "publisher must not be group/world writable")

    def test_codex_rule_allows_only_the_protected_publisher_entrypoint(self) -> None:
        rule = (ROOT / ".codex" / "rules" / "weekly-publisher.rules").read_text(encoding="utf-8")
        self.assertIn(".codex/bin/publish-weekly-pr", rule)
        self.assertRegex(rule, r"decision\s*=\s*['\"]allow['\"]")
        self.assertNotRegex(
            rule,
            r"pattern\s*=\s*\[\s*['\"](?:git|gh|bash|sh|zsh)['\"]",
            "the execution rule must not allow a general shell or publication CLI",
        )

    def test_weekly_mutable_paths_contain_no_secrets_or_executables(self) -> None:
        files = mutable_files()
        self.assertTrue(files, "weekly mutable paths are empty")
        failures: list[str] = []
        sensitive_names = re.compile(
            r"(?:^|/)(?:\.env(?:\..*)?|credentials|config\.json|kubeconfig)$|\.(?:key|pem|p12|pfx|tfstate|tfvars)$",
            re.IGNORECASE,
        )
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            if path.is_symlink():
                failures.append(f"{relative}: symbolic links are forbidden")
                continue
            mode = path.stat().st_mode
            if not stat.S_ISREG(mode):
                failures.append(f"{relative}: not a regular file")
                continue
            if mode & 0o111:
                failures.append(f"{relative}: executable file in weekly mutable path")
            if sensitive_names.search(relative):
                failures.append(f"{relative}: sensitive filename")
            contents = path.read_bytes()
            if b"\x00" in contents:
                failures.append(f"{relative}: binary content")
                continue
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(contents):
                    failures.append(f"{relative}: possible {label}")
        self.assertEqual([], failures, "weekly mutable path safety violations")


if __name__ == "__main__":
    unittest.main()
