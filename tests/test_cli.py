"""The console scripts declared in pyproject.toml must run."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datalineagepy.cli import main as datalineage_main
from datalineagepy.cli import run as datalineage_run
from datalineagepy.export.cli import run as export_run
from datalineagepy.visualization.cli import run as viz_run


def test_version_exits_zero():
    try:
        datalineage_main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("version should exit the process")


def test_track_writes_json_and_html(tmp_path, capsys):
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text("order_id,amount\n1,10\n2,15\n", encoding="utf-8")
    json_path = tmp_path / "lineage.json"
    html_path = tmp_path / "lineage.html"

    status = datalineage_run(
        ["track", str(csv_path), "--output", str(json_path), "--html", str(html_path)]
    )

    assert status == 0
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["nodes"]
    assert "order_id" in html_path.read_text(encoding="utf-8")
    assert "2 rows" in capsys.readouterr().out


def test_export_writes_dot(tmp_path):
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text("order_id,amount\n1,10\n", encoding="utf-8")
    dot_path = tmp_path / "lineage.dot"

    status = export_run(
        [str(csv_path), "--output", str(dot_path), "--format", "dot"]
    )

    assert status == 0
    assert "digraph lineage" in dot_path.read_text(encoding="utf-8")


def test_visualize_writes_html(tmp_path, capsys):
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text("order_id,amount\n1,10\n", encoding="utf-8")
    html_path = tmp_path / "lineage.html"

    status = viz_run([str(csv_path), "--output", str(html_path)])

    assert status == 0
    assert html_path.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    assert str(html_path) in capsys.readouterr().out


def test_missing_csv_returns_error(tmp_path):
    missing = tmp_path / "missing.csv"
    assert datalineage_run(["track", str(missing), "--output", str(tmp_path / "out.json")]) == 1
    assert export_run([str(missing), "--output", str(tmp_path / "out.json")]) == 1
    assert viz_run([str(missing), "--output", str(tmp_path / "out.html")]) == 1
