
# =============================================================
#  🚀 DataLineagePy 3.0.3 Basic Example
# =============================================================
#
# Demonstrates core features: automatic lineage tracking, column-level
# dependencies, assign/filter/groupby, and lineage queries/statistics.
#
# Version: 3.0.3   |   Last Updated: September 2025
# =============================================================


from datalineagepy import LineageDataFrame, LineageTracker
import pandas as pd


def main():
    print("\n🔗 DataLineagePy 3.0.3 Basic Example")
    print("=" * 50)

    # --- Reset tracker for clean demo ---
    LineageTracker.reset_global_instance()

    # 1️⃣  Create initial sales data
    print("\n1️⃣  Creating initial sales data...")
    sales_data = {
        'product_id': ['P001', 'P002', 'P001', 'P003', 'P002'],
        'quantity': [10, 15, 8, 12, 20],
        'unit_price': [25.0, 40.0, 25.0, 15.0, 40.0],
        'region': ['North', 'South', 'North', 'East', 'South']
    }

    sales_df = LineageDataFrame(
        sales_data, name="raw_sales_data", source_type="csv")
    print(f"   ✅ Created DataFrame: {sales_df.shape}")
    print(f"   Columns: {list(sales_df.columns)}")

    # 2️⃣  Calculate total revenue
    print("\n2️⃣  Calculating total revenue...")
    sales_with_revenue = sales_df.assign(
        total_revenue=lambda x: x['quantity'] * x['unit_price']
    )
    print(f"   ➕ Added revenue column: {sales_with_revenue.shape}")
    print(
        f"   Sample revenue values: {list(sales_with_revenue._df['total_revenue'][:3])}")

    # 3️⃣  Filter high-value transactions
    print("\n3️⃣  Filtering high-value transactions (>= $300)...")
    high_value = sales_with_revenue[sales_with_revenue._df['total_revenue'] >= 300]
    print(f"   💰 High-value transactions: {high_value.shape}")

    # 4️⃣  Group by region
    print("\n4️⃣  Summarizing by region...")
    region_summary = sales_with_revenue.groupby('region').agg({
        'total_revenue': 'sum',
        'quantity': 'sum'
    }).reset_index()
    print(f"   📊 Region summary: {region_summary.shape}")
    print("   Sample data:")
    print(region_summary._df.to_string(index=False))

    # 5️⃣  Show lineage information
    print("\n5️⃣  Lineage Information")
    print("-" * 30)

    # Get tracker stats
    tracker = LineageTracker.get_global_instance()
    stats = tracker.get_stats()
    print(f"   📊 Total nodes tracked: {stats['total_nodes']}")
    print(f"   � Total transformations: {stats['total_edges']}")

    # Show column lineage for total_revenue
    print("\n   🔍 Column lineage for 'total_revenue':")
    revenue_lineage = region_summary.get_lineage_for_column('total_revenue')
    source_cols = revenue_lineage.get('source_columns', [])
    print(f"      Source columns: {source_cols}")

    # Show table lineage
    print("\n   🔍 Table lineage:")
    table_lineage = region_summary.get_table_lineage()
    dependencies = table_lineage.get('all_dependencies', [])
    print(f"      Depends on {len(dependencies)} upstream tables")

    print("\n✅ Example completed! DataLineagePy 3.0.3 successfully tracked the entire pipeline.")
    print("\n💡 Key features demonstrated:")
    print("   • Automatic lineage tracking for DataFrame operations")
    print("   • Column-level dependency tracking")
    print("   • Support for assign, filter, groupby operations")
    print("   • Lineage queries and statistics")


if __name__ == "__main__":
    main()
