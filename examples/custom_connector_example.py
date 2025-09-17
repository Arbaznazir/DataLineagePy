"""
Custom Connector SDK Example for DataLineagePy
Demonstrates how to build and use a custom connector with full lineage tracking.
"""
from datalineagepy.connectors.custom_connector_sdk import BaseCustomConnector


class MyCSVConnector(BaseCustomConnector):
    def connect(self, file_path):
        self.file_path = file_path
        print(f"Connected to CSV file: {file_path}")

    def execute(self, operation: str, *args, **kwargs):
        # Example: Only support 'read' operation
        if operation == "read":
            with open(self.file_path, "r") as f:
                data = f.read()
            node = self.tracker.create_node("csv_read", self.file_path)
            node.add_metadata("operation", operation)
            return data
        else:
            raise NotImplementedError(
                f"Operation '{operation}' not supported.")

    def close(self):
        print("Connection closed.")


# Usage
connector = MyCSVConnector(name="csv_connector_demo")
connector.connect("test_data.csv")
data = connector.execute("read")
print("Read data:", data[:50], "...")
connector.close()
print("Exported lineage:", connector.export_lineage())
