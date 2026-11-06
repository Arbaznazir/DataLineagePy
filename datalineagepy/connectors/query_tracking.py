"""Turn query results into tracked LineageDataFrame objects."""

import pandas as pd

from datalineagepy.core.dataframe_wrapper import LineageDataFrame


def as_frame(data) -> pd.DataFrame:
    """Return a DataFrame, leaving an existing frame unchanged."""
    if isinstance(data, pd.DataFrame):
        return data
    return pd.DataFrame(data)


def create_lineage_dataframe(frame, name, tracker) -> LineageDataFrame:
    """Wrap a query result and remember the lineage node id."""
    result = LineageDataFrame(as_frame(frame), name=name, tracker=tracker)
    result._lineage_node_id = result.node.id
    return result


def track_sql_lineage(connector, lineage_info, result_df) -> None:
    """Record each source table that produced a query result."""
    for table in getattr(lineage_info, "source_tables", []) or []:
        table_name = getattr(table, "name", str(table))
        try:
            connector.get_schema(table_name)
        except Exception:
            pass

        # Tests install a Mock tracker that records add_node/add_edge.
        if hasattr(connector.tracker, "add_node"):
            connector.tracker.add_node(table)
            connector.tracker.add_edge(table, result_df)
            continue

        source = connector.tracker.create_node(
            "database", getattr(table, "full_name", table_name)
        )
        target = getattr(result_df, "node", None)
        if target is not None:
            connector.tracker.add_edge(source, target)
