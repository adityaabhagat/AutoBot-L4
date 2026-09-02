"""Auto-Bot Lite test suite — by Aditya Bhagat.

Offline-only: no Salesforce, ADO, or DB access required. The end-to-end test
replays the real solved case 26-01106039 from a fixture and asserts the
deterministic pipeline lands on rule QPTM-BILL-041 (G5).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "cases"
sys.path.insert(0, str(REPO))

import autobot  # noqa: E402


# ------------------------------------------------------------ unit: matching
def test_term_hit_word_boundaries():
    assert autobot.term_hit("allocation", "the allocation failed")
    assert not autobot.term_hit("allocation", "reallocation records trigger")
    assert autobot.term_hit("SQL 208", "failed with SQL 208 in step 3")
    assert autobot.term_hit("BLSTAG_PAL_EXT", "Invalid object name 'BLSTAG_PAL_EXT'")


def test_term_hit_regex_form():
    assert autobot.term_hit("/(Revenue Override|Override Revenue)/", "the Override Revenue screen hangs")
    assert not autobot.term_hit("/^ENMQR\\d{3}$/", "code ENMQR315 here")  # anchored regex, full-line only


def test_rule_matches_all_any_none():
    rule = {"match": {"all": ["SQL 208"], "any": ["BLINVGEN", "PANIGHTLY"], "none": ["ORA-"]}}
    assert autobot.rule_matches(rule, "BLINVGEN died with SQL 208")
    assert not autobot.rule_matches(rule, "BLINVGEN died with SQL 208 and ORA-01013")
    assert not autobot.rule_matches(rule, "SQL 208 alone, no process named")
    assert not autobot.rule_matches({"match": {"all": [], "any": []}}, "anything")  # empty match never fires


# --------------------------------------------------------- unit: when-DSL
@pytest.mark.parametrize("when,rows,expected", [
    ("rowcount == 0", [], True),
    ("rowcount > 0", [{"a": 1}], True),
    ("rowcount >= 2", [{"a": 1}], False),
    ("rows[0].obj_id is null", [{"obj_id": None}], True),
    ("rows[0].obj_id is not null", [{"obj_id": 42}], True),
    ("rows[0].cnt == 2", [{"cnt": 2}], True),
    ("rows[0].cnt >= 3", [{"cnt": 2}], False),
])
def test_when_dsl(when, rows, expected):
    hit = autobot.evaluate_interpret([{"when": when, "verdict": "CONFIRMED", "meaning": "m"}], rows)
    assert (hit is not None) == expected


def test_when_dsl_rejects_unknown_forms():
    assert autobot.evaluate_interpret([{"when": "rows[1].x == 5 OR banana", "verdict": "CONFIRMED"}], [{"x": 5}]) is None


# ------------------------------------------------------- corpus invariants
def test_all_rule_files_load_and_check_passes():
    rc = subprocess.run([sys.executable, str(REPO / "autobot.py"), "check"],
                        capture_output=True, text=True, cwd=REPO)
    assert rc.returncode == 0, rc.stdout + rc.stderr
    assert "0 problems" in rc.stdout


def test_rules_have_sources_and_valid_gates():
    for product in ("QPTM", "TIPS", "QDO"):
        rules = autobot.load_rules(product)
        assert rules, f"no rules for {product}"
        for r in rules:
            assert r["gate"] in autobot.GATES
            assert r.get("source"), f"{r['id']} missing source anchor"


def test_vocab_prefixes_parse():
    terms, prefixes = autobot.parse_vocab("QPTM")
    assert "BLSTAG_" in prefixes and "NNCTRL_" in prefixes
    assert any(t == "ALALLOCATE" for t in terms)


# -------------------------------------------------- end-to-end regression
def test_regression_26_01106039_fires_bill_041(tmp_path, monkeypatch, capsys):
    case = "26-01106039"
    shutil.copytree(FIXTURES / case, tmp_path / case)
    monkeypatch.setattr(autobot, "CASES", tmp_path)
    args = type("A", (), {"case": case, "product": None, "env": None,
                          "offline": True, "remember": False})()
    assert autobot.solve(args) == 0
    out = capsys.readouterr().out
    assert "SOLVED via QPTM-BILL-041 (G5)" in out
    report = tmp_path / case / "report_Lite_G5.md"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "BLSTAG_PAL_EXT" in text
    assert "not Configuration" in text                      # the NOT-rule
    assert "NOT YET RUN" in text                            # honest offline confidence
    assert "Aditya Bhagat" in text                          # branding footer
