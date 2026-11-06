"""Lightweight SQL parser for table-level lineage."""

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class TableRef:
    """A table named by a SQL statement."""

    name: str
    schema: str = ""

    @property
    def full_name(self) -> str:
        if self.schema:
            return "{}.{}".format(self.schema, self.name)
        return self.name


@dataclass
class QueryLineage:
    """Tables and statement type extracted from one query."""

    query_type: str
    source_tables: List[TableRef]
    raw_query: str
    operations: List[str] = field(default_factory=list)


_TABLE = re.compile(
    r"""
    (?:\bFROM\b|\bJOIN\b)\s+
    (?:
        (?P<quoted_schema>"[^"]+"|`[^`]+`)\s*\.\s*(?P<quoted_name>"[^"]+"|`[^`]+`)
        |
        (?P<schema>[A-Za-z_][\w]*)\s*\.\s*(?P<name>[A-Za-z_][\w]*)
        |
        (?P<only>"[^"]+"|`[^`]+`|[A-Za-z_][\w]*)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


class SQLLineageParser:
    """Extract source tables from SELECT and JOIN queries."""

    def parse_query(self, query: str) -> QueryLineage:
        stripped = (query or "").strip()
        query_type = stripped.split(None, 1)[0].upper() if stripped else "UNKNOWN"
        tables = []
        seen = set()
        for match in _TABLE.finditer(stripped):
            if match.group("quoted_name"):
                schema = match.group("quoted_schema").strip('"`')
                name = match.group("quoted_name").strip('"`')
            elif match.group("name"):
                schema = match.group("schema")
                name = match.group("name")
            else:
                schema = ""
                name = match.group("only").strip('"`')
            key = (schema, name)
            if key in seen:
                continue
            seen.add(key)
            tables.append(TableRef(name=name, schema=schema))

        operations = [
            keyword
            for keyword in ("SELECT", "JOIN", "WHERE", "GROUP", "ORDER")
            if re.search(r"\b{}\b".format(keyword), stripped, re.IGNORECASE)
        ]
        return QueryLineage(
            query_type=query_type,
            source_tables=tables,
            raw_query=query,
            operations=operations,
        )
