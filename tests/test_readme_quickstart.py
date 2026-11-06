"""The README quick start must run against the public package name."""

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datalineagepy import LineageDataFrame, LineageTracker


def test_readme_quickstart(tmp_path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    tracker = LineageTracker(name="demo")
    ldf = LineageDataFrame(df, name="my_df", tracker=tracker)
    ldf2 = ldf.filter(ldf._df["a"] > 1)
    ldf3 = ldf2.assign(c=ldf2._df["a"] + ldf2._df["b"])

    html_path = tmp_path / "lineage.html"
    json_path = tmp_path / "lineage.json"

    written_html = tracker.visualize(str(html_path))
    written_json = tracker.export_lineage(str(json_path))

    assert written_html == str(html_path)
    assert written_json == str(json_path)
    assert html_path.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(payload["nodes"]) == 3
    assert len(payload["edges"]) == 2
    assert list(ldf3.columns) == ["a", "b", "c"]
    assert len(ldf3) == 2
