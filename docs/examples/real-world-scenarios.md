# Real-World Scenarios & Examples

Complete collection of real-world scenarios demonstrating DataLineagePy in action across different industries and use cases.

---

## 🌐 All-in-One Enterprise Data Pipeline Example (Every Feature)

This scenario demonstrates every major feature of DataLineagePy in a single, end-to-end workflow:

```python
import pandas as pd
import numpy as np
import os
from datalineagepy import LineageTracker, LineageDataFrame, AutoMLTracker
from datalineagepy.core.validation import DataValidator
from datalineagepy.core.analytics import DataProfiler
from datalineagepy.visualization import GraphVisualizer
from datalineagepy.core.performance import PerformanceMonitor
from datalineagepy.security.rbac import RBACManager
from datalineagepy.security.encryption.data_encryption import EncryptionManager
from datalineagepy.connectors.database.mysql_connector import MySQLConnector

# 1. Security & RBAC
rbac = RBACManager()
rbac.add_role('admin', ['read', 'write', 'delete'])
rbac.add_user('alice', ['admin'])
assert rbac.check_access('alice', 'write')

# 2. Encryption
os.environ['MASTER_ENCRYPTION_KEY'] = 'supersecretkey1234567890123456'
enc_mgr = EncryptionManager()
secret = 'Sensitive Data'
encrypted = enc_mgr.encrypt_sensitive_data(secret)
decrypted = enc_mgr.decrypt_sensitive_data(encrypted)
assert decrypted == secret

# 3. Tracker & DataFrame
tracker = LineageTracker(name="all_in_one_pipeline")
df = pd.DataFrame({
    'user_id': range(1, 6),
    'score': [88, 92, 79, 85, 90],
    'region': ['US', 'EU', 'APAC', 'US', 'EU']
})
ldf = LineageDataFrame(df, name="users", tracker=tracker)

# 4. Data Validation
validator = DataValidator(tracker)
rules = {'completeness': {'threshold': 0.9}, 'uniqueness': {'columns': ['user_id']}}
validation_results = validator.validate_dataframe(ldf, rules)

# 5. Profiling & Analytics
profiler = DataProfiler(tracker)
profile = profiler.profile_dataset(ldf)

# 6. Performance Monitoring
monitor = PerformanceMonitor(tracker)
monitor.start_monitoring()
_ = ldf._df['score'].mean()
monitor.stop_monitoring()
perf_summary = monitor.get_performance_summary()

# 7. Visualization
visualizer = GraphVisualizer(tracker)
visualizer.generate_html("all_in_one_lineage.html")

# 8. Database Connector (MySQL)
# (Assume a running MySQL instance for demo)
# db_config = {'host': 'localhost', 'user': 'root', 'password': 'password', 'database': 'test_db'}
# conn = MySQLConnector(**db_config, lineage_tracker=tracker)
# conn.execute_query('CREATE TABLE IF NOT EXISTS test_table (id INT PRIMARY KEY, score INT)')
# conn.execute_query('INSERT INTO test_table (id, score) VALUES (%s, %s)', (1, 100))
# result = conn.execute_query('SELECT * FROM test_table')
# conn.close()

# 9. ML/AI Pipeline Tracking
automl = AutoMLTracker(name="ml_pipeline")
automl.log_step("fit", model="LogisticRegression", params={"solver": "lbfgs"})
automl.log_step("predict", model="LogisticRegression")
ml_export = automl.export_ai_ready_format()

# 10. Versioning
from datalineagepy.core.lineage_versioning import LineageVersionManager
version_mgr = LineageVersionManager()
version_mgr.save_version(tracker.export_graph())
ldf2 = ldf.assign(score2=ldf._df['score'] * 2)
version_mgr.save_version(tracker.export_graph())
assert len(version_mgr.list_versions()) == 2

# 11. Real-time Collaboration (API demo)
# from datalineagepy.collaboration.realtime_collaboration import CollaborationServer, CollaborationClient
# CollaborationServer().run()  # In one process
# CollaborationClient().run()  # In another process

# 12. Exporting
tracker.export_lineage("all_in_one_lineage.json")
tracker.export_to_formats(base_path="exports/", formats=['json', 'csv', 'excel'])

# 13. Dashboard
tracker.generate_dashboard("all_in_one_dashboard.html")

print("All major features demonstrated in a single workflow!")
```

---

## 🏪 E-Commerce Analytics Pipeline

### Scenario: Online Retail Data Processing

Complete analytics pipeline for an e-commerce platform tracking customer behavior and sales performance.

```python
import pandas as pd
from lineagepy import LineageTracker, DataFrameWrapper
from datetime import datetime, timedelta

# Initialize tracking
tracker = LineageTracker()

# Raw data sources
customers_raw = pd.DataFrame({
    'customer_id': range(1, 1001),
    'email': [f'user{i}@email.com' for i in range(1, 1001)],
    'registration_date': pd.date_range('2023-01-01', periods=1000, freq='H'),
    'country': ['US', 'UK', 'DE', 'FR', 'CA'] * 200,
    'age': np.random.randint(18, 70, 1000)
})

orders_raw = pd.DataFrame({
    'order_id': range(1, 5001),
    'customer_id': np.random.randint(1, 1001, 5000),
    'product_id': np.random.randint(1, 101, 5000),
    'quantity': np.random.randint(1, 5, 5000),
    'unit_price': np.random.uniform(10, 500, 5000),
    'order_date': pd.date_range('2023-01-01', periods=5000, freq='H'),
    'order_status': np.random.choice(['completed', 'pending', 'cancelled'], 5000)
})

products_raw = pd.DataFrame({
    'product_id': range(1, 101),
    'product_name': [f'Product {i}' for i in range(1, 101)],
    'category': np.random.choice(['Electronics', 'Clothing', 'Home', 'Sports'], 100),
    'cost_price': np.random.uniform(5, 200, 100),
    'brand': np.random.choice(['BrandA', 'BrandB', 'BrandC'], 100)
})

# Wrap data sources for lineage tracking
customers = DataFrameWrapper(customers_raw, tracker, 'customers', metadata={
    'source': 'customer_database',
    'refresh_frequency': 'daily',
    'owner': 'customer_team'
})

orders = DataFrameWrapper(orders_raw, tracker, 'orders', metadata={
    'source': 'order_management_system',
    'refresh_frequency': 'real_time',
    'owner': 'sales_team'
})

products = DataFrameWrapper(products_raw, tracker, 'products', metadata={
    'source': 'product_catalog',
    'refresh_frequency': 'weekly',
    'owner': 'product_team'
})

# Data cleaning and validation
def clean_customer_data(df):
    """Clean customer data with business rules"""
    # Remove invalid emails
    df_clean = df[df['email'].str.contains('@')]

    # Standardize country codes
    df_clean['country_code'] = df_clean['country'].map({
        'US': 'USA', 'UK': 'GBR', 'DE': 'DEU',
        'FR': 'FRA', 'CA': 'CAN'
    })

    # Create customer segments
    df_clean['age_segment'] = pd.cut(
        df_clean['age'],
        bins=[0, 25, 35, 50, 100],
        labels=['Gen Z', 'Millennial', 'Gen X', 'Boomer']
    )

    # Calculate customer tenure
    df_clean['tenure_days'] = (
        pd.Timestamp.now() - df_clean['registration_date']
    ).dt.days

    return df_clean

customers_clean = clean_customer_data(customers)
# Lineage: customers.email -> filter -> customers_clean.email
# Lineage: customers.country -> customers_clean.country_code
# Lineage: customers.age -> customers_clean.age_segment
# Lineage: customers.registration_date -> customers_clean.tenure_days

def clean_order_data(df):
    """Clean order data with business validation"""
    # Remove cancelled orders for analytics
    df_clean = df[df['order_status'] != 'cancelled']

    # Calculate order values
    df_clean['order_value'] = df_clean['quantity'] * df_clean['unit_price']

    # Add time-based features
    df_clean['order_hour'] = df_clean['order_date'].dt.hour
    df_clean['order_day_of_week'] = df_clean['order_date'].dt.day_name()
    df_clean['is_weekend'] = df_clean['order_date'].dt.weekday >= 5

    # Create order size categories
    df_clean['order_size'] = pd.cut(
        df_clean['order_value'],
        bins=[0, 50, 150, 500, float('inf')],
        labels=['Small', 'Medium', 'Large', 'Premium']
    )

    return df_clean

orders_clean = clean_order_data(orders)
# Lineage: orders.quantity, orders.unit_price -> orders_clean.order_value
# Lineage: orders.order_date -> orders_clean.order_hour, order_day_of_week, is_weekend
# Lineage: orders_clean.order_value -> orders_clean.order_size

# Join operations for enrichment
customer_orders = customers_clean.merge(
    orders_clean,
    on='customer_id',
    how='inner'
)
# Lineage: customers_clean.*, orders_clean.* -> customer_orders.*

enriched_orders = customer_orders.merge(
    products,
    on='product_id',
    how='left'
)
# Lineage: customer_orders.*, products.* -> enriched_orders.*

# Calculate business metrics
def calculate_customer_metrics(df):
    """Calculate comprehensive customer metrics"""

    customer_summary = df.groupby('customer_id').agg({
        'order_value': ['sum', 'mean', 'count'],
        'quantity': 'sum',
        'order_date': ['min', 'max']
    }).round(2)

    # Flatten column names
    customer_summary.columns = [
        'total_spent', 'avg_order_value', 'order_count',
        'total_items', 'first_order_date', 'last_order_date'
    ]

    # Calculate customer lifetime value (CLV)
    customer_summary['clv'] = (
        customer_summary['total_spent'] *
        customer_summary['order_count'] * 0.1  # Simple CLV approximation
    )

    # Customer value segments
    customer_summary['value_segment'] = pd.qcut(
        customer_summary['total_spent'],
        q=5,
        labels=['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']
    )

    # Purchase frequency
    customer_summary['purchase_frequency'] = pd.cut(
        customer_summary['order_count'],
        bins=[0, 1, 3, 5, float('inf')],
        labels=['One-time', 'Occasional', 'Regular', 'Frequent']
    )

    return customer_summary.reset_index()

customer_metrics = calculate_customer_metrics(enriched_orders)
# Lineage: enriched_orders.order_value -> customer_metrics.total_spent, avg_order_value, clv
# Lineage: enriched_orders.customer_id -> customer_metrics grouping
# Lineage: customer_metrics.total_spent -> customer_metrics.value_segment

# Product performance analysis
def analyze_product_performance(df):
    """Analyze product and category performance"""

    product_performance = df.groupby(['product_id', 'product_name', 'category']).agg({
        'order_value': ['sum', 'mean', 'count'],
        'quantity': 'sum',
        'customer_id': 'nunique'
    }).round(2)

    product_performance.columns = [
        'total_revenue', 'avg_order_value', 'order_count',
        'units_sold', 'unique_customers'
    ]

    # Calculate product metrics
    product_performance['revenue_per_customer'] = (
        product_performance['total_revenue'] /
        product_performance['unique_customers']
    )

    product_performance['conversion_rate'] = (
        product_performance['order_count'] /
        product_performance['unique_customers']
    )

    # Rank products by performance
    product_performance['revenue_rank'] = (
        product_performance['total_revenue'].rank(ascending=False)
    )

    return product_performance.reset_index()

product_metrics = analyze_product_performance(enriched_orders)
# Complex lineage from enriched_orders through groupby and calculations

# Time-based analysis
def create_time_series_metrics(df):
    """Create time-based business metrics"""

    # Daily metrics
    daily_metrics = df.groupby(df['order_date'].dt.date).agg({
        'order_value': ['sum', 'mean', 'count'],
        'customer_id': 'nunique',
        'product_id': 'nunique'
    }).round(2)

    daily_metrics.columns = [
        'daily_revenue', 'avg_order_value', 'order_count',
        'unique_customers', 'unique_products'
    ]

    # Calculate moving averages
    daily_metrics['revenue_7day_ma'] = (
        daily_metrics['daily_revenue'].rolling(window=7).mean()
    )

    daily_metrics['revenue_30day_ma'] = (
        daily_metrics['daily_revenue'].rolling(window=30).mean()
    )

    # Growth rates
    daily_metrics['revenue_growth'] = (
        daily_metrics['daily_revenue'].pct_change()
    )

    return daily_metrics.reset_index()

time_series = create_time_series_metrics(enriched_orders)
# Lineage: enriched_orders.order_date -> time_series grouping
# Lineage: enriched_orders.order_value -> time_series.daily_revenue -> revenue_7day_ma

# Advanced analytics: Customer cohort analysis
def cohort_analysis(df):
    """Perform customer cohort analysis"""

    # Determine customer's first order month
    customer_cohorts = df.groupby('customer_id')['order_date'].min().reset_index()
    customer_cohorts['cohort_month'] = customer_cohorts['order_date'].dt.to_period('M')

    # Merge back with order data
    df_cohort = df.merge(customer_cohorts[['customer_id', 'cohort_month']], on='customer_id')

    # Calculate period number (months since first order)
    df_cohort['order_period'] = df_cohort['order_date'].dt.to_period('M')
    df_cohort['period_number'] = (
        df_cohort['order_period'] - df_cohort['cohort_month']
    ).apply(attrgetter('n'))

    # Cohort table
    cohort_data = df_cohort.groupby(['cohort_month', 'period_number'])['customer_id'].nunique().reset_index()
    cohort_table = cohort_data.pivot(index='cohort_month', columns='period_number', values='customer_id')

    # Calculate retention rates
    cohort_sizes = df_cohort.groupby('cohort_month')['customer_id'].nunique()
    retention_table = cohort_table.divide(cohort_sizes, axis=0)

    return {
        'cohort_table': cohort_table,
        'retention_table': retention_table,
        'cohort_data': df_cohort
    }

cohort_results = cohort_analysis(enriched_orders)
# Complex lineage through cohort analysis calculations

# Marketing attribution analysis
def marketing_attribution(df):
    """Analyze customer acquisition and attribution"""

    # Simulate marketing channel data
    np.random.seed(42)
    channels = ['organic', 'paid_search', 'social', 'email', 'referral']

    df_marketing = df.copy()
    df_marketing['acquisition_channel'] = np.random.choice(channels, len(df))
    df_marketing['campaign_id'] = np.random.randint(1, 21, len(df))

    # Channel performance analysis
    channel_performance = df_marketing.groupby('acquisition_channel').agg({
        'order_value': ['sum', 'mean', 'count'],
        'customer_id': 'nunique'
    }).round(2)

    channel_performance.columns = [
        'total_revenue', 'avg_order_value', 'order_count', 'unique_customers'
    ]

    # Calculate channel metrics
    channel_performance['revenue_per_customer'] = (
        channel_performance['total_revenue'] /
        channel_performance['unique_customers']
    )

    channel_performance['orders_per_customer'] = (
        channel_performance['order_count'] /
        channel_performance['unique_customers']
    )

    return channel_performance.reset_index()

attribution_metrics = marketing_attribution(enriched_orders)

# Final aggregated dashboard metrics
def create_dashboard_metrics(customer_metrics, product_metrics, time_series, attribution_metrics):
    """Create high-level dashboard metrics"""

    dashboard = {
        'kpis': {
            'total_customers': len(customer_metrics),
            'total_revenue': customer_metrics['total_spent'].sum(),
            'avg_clv': customer_metrics['clv'].mean(),
            'top_product_category': product_metrics.loc[
                product_metrics['total_revenue'].idxmax(), 'category'
            ]
        },
        'growth_metrics': {
            'revenue_growth_rate': time_series['revenue_growth'].mean(),
            'customer_growth_rate': (
                time_series['unique_customers'].iloc[-1] /
                time_series['unique_customers'].iloc[0] - 1
            )
        },
        'segmentation': {
            'value_distribution': customer_metrics['value_segment'].value_counts().to_dict(),
            'frequency_distribution': customer_metrics['purchase_frequency'].value_counts().to_dict()
        }
    }

    return dashboard

final_dashboard = create_dashboard_metrics(
    customer_metrics, product_metrics, time_series, attribution_metrics
)
# Lineage: All previous calculations -> final_dashboard

# Visualize the complete lineage
print("📊 E-Commerce Analytics Pipeline Lineage")
print("=" * 50)

# Get lineage for key metrics
clv_lineage = tracker.get_column_lineage('clv')
print(f"Customer Lifetime Value lineage:")
print(f"  Sources: {clv_lineage['source_columns']}")
print(f"  Depth: {clv_lineage['depth']}")

revenue_lineage = tracker.get_column_lineage('total_revenue')
print(f"\nTotal Revenue lineage:")
print(f"  Sources: {revenue_lineage['source_columns']}")

# Generate comprehensive dashboard
tracker.generate_dashboard('ecommerce_lineage_dashboard.html',
                          title='E-Commerce Analytics Lineage')

print(f"\n📈 Pipeline Statistics:")
print(f"  Total nodes: {tracker.get_graph_stats()['nodes']}")
print(f"  Total edges: {tracker.get_graph_stats()['edges']}")
print(f"  Max depth: {tracker.get_graph_stats()['max_depth']}")
```

---

## 🏦 Financial Risk Analytics

### Scenario: Credit Risk Assessment Pipeline

Complete pipeline for assessing credit risk with regulatory compliance tracking.

```python
import pandas as pd
import numpy as np
from lineagepy import LineageTracker, DataFrameWrapper
from datetime import datetime

# Initialize tracking with compliance metadata
tracker = LineageTracker(config={
    'enable_compliance_tracking': True,
    'audit_level': 'detailed'
})

# Raw financial data
loan_applications = pd.DataFrame({
    'application_id': range(1, 10001),
    'customer_id': range(1, 10001),
    'loan_amount': np.random.uniform(5000, 500000, 10000),
    'annual_income': np.random.uniform(30000, 200000, 10000),
    'employment_years': np.random.randint(0, 40, 10000),
    'credit_score': np.random.randint(300, 850, 10000),
    'debt_to_income': np.random.uniform(0.1, 0.8, 10000),
    'loan_purpose': np.random.choice(['home', 'auto', 'personal', 'business'], 10000),
    'application_date': pd.date_range('2023-01-01', periods=10000, freq='H')
})

customer_history = pd.DataFrame({
    'customer_id': range(1, 10001),
    'previous_defaults': np.random.poisson(0.1, 10000),
    'previous_loans': np.random.poisson(2, 10000),
    'bank_relationship_years': np.random.randint(0, 20, 10000),
    'account_balance': np.random.uniform(0, 100000, 10000),
    'transaction_volume': np.random.uniform(1000, 50000, 10000)
})

economic_indicators = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=365, freq='D'),
    'unemployment_rate': np.random.uniform(3, 8, 365),
    'interest_rate': np.random.uniform(2, 6, 365),
    'gdp_growth': np.random.uniform(-2, 4, 365),
    'housing_index': np.random.uniform(90, 110, 365)
})

# Wrap data with compliance metadata
applications = DataFrameWrapper(loan_applications, tracker, 'loan_applications', metadata={
    'source': 'loan_origination_system',
    'data_classification': 'confidential',
    'regulatory_requirements': ['GDPR', 'CCPA', 'Basel III'],
    'retention_period': '7_years',
    'owner': 'risk_management'
})

history = DataFrameWrapper(customer_history, tracker, 'customer_history', metadata={
    'source': 'customer_database',
    'data_classification': 'restricted',
    'pii_fields': ['customer_id'],
    'compliance_notes': 'Customer consent required for processing'
})

economic = DataFrameWrapper(economic_indicators, tracker, 'economic_indicators', metadata={
    'source': 'federal_reserve_api',
    'data_classification': 'public',
    'update_frequency': 'daily'
})

# Feature engineering for risk assessment
def engineer_risk_features(df):
    """Create risk assessment features with full lineage tracking"""

    # Income-based features
    df['loan_to_income_ratio'] = df['loan_amount'] / df['annual_income']
    df['income_category'] = pd.cut(
        df['annual_income'],
        bins=[0, 40000, 80000, 120000, float('inf')],
        labels=['Low', 'Medium', 'High', 'Very High']
    )

    # Credit risk features
    df['credit_risk_score'] = (
        (850 - df['credit_score']) / 850 * 100 +  # Inverted credit score
        df['debt_to_income'] * 50 +               # Debt burden
        (df['loan_amount'] / 100000) * 20         # Loan size factor
    )

    # Employment stability
    df['employment_stability'] = pd.cut(
        df['employment_years'],
        bins=[0, 2, 5, 10, float('inf')],
        labels=['Unstable', 'Developing', 'Stable', 'Very Stable']
    )

    # Loan risk categories
    df['loan_risk_category'] = pd.cut(
        df['credit_risk_score'],
        bins=[0, 30, 60, 80, 100],
        labels=['Low Risk', 'Medium Risk', 'High Risk', 'Very High Risk']
    )

    return df

# Apply feature engineering
applications_featured = engineer_risk_features(applications)
# Lineage: loan_amount, annual_income -> loan_to_income_ratio
# Lineage: credit_score, debt_to_income, loan_amount -> credit_risk_score

# Enrich with customer history
enriched_applications = applications_featured.merge(
    history,
    on='customer_id',
    how='left'
)

def calculate_historical_risk_factors(df):
    """Calculate risk factors based on customer history"""

    # Default risk based on history
    df['default_risk_multiplier'] = 1 + (df['previous_defaults'] * 0.5)

    # Loyalty factor
    df['loyalty_score'] = (
        df['bank_relationship_years'] * 0.1 +
        np.log1p(df['account_balance']) * 0.05 +
        (df['previous_loans'] - df['previous_defaults']) * 0.1
    )

    # Adjusted risk score
    df['adjusted_risk_score'] = (
        df['credit_risk_score'] * df['default_risk_multiplier'] -
        df['loyalty_score']
    )

    # Financial stability indicators
    df['financial_stability'] = pd.cut(
        df['account_balance'] / df['annual_income'],
        bins=[0, 0.1, 0.3, 0.6, float('inf')],
        labels=['Poor', 'Fair', 'Good', 'Excellent']
    )

    return df

risk_enriched = calculate_historical_risk_factors(enriched_applications)

# Add economic context
def add_economic_context(df, economic_df):
    """Add macroeconomic context to risk assessment"""

    # Merge with economic indicators based on application date
    df['application_date'] = pd.to_datetime(df['application_date'])
    df['economic_date'] = df['application_date'].dt.date

    economic_df['date'] = pd.to_datetime(economic_df['date']).dt.date

    df_with_economic = df.merge(
        economic_df,
        left_on='economic_date',
        right_on='date',
        how='left'
    )

    # Economic risk adjustments
    df_with_economic['economic_risk_factor'] = (
        (df_with_economic['unemployment_rate'] / 10) * 0.3 +
        (df_with_economic['interest_rate'] / 10) * 0.2 +
        (1 - df_with_economic['gdp_growth'] / 10) * 0.2
    )

    # Adjust risk score for economic conditions
    df_with_economic['final_risk_score'] = (
        df_with_economic['adjusted_risk_score'] +
        df_with_economic['economic_risk_factor'] * 10
    )

    return df_with_economic

final_risk_data = add_economic_context(risk_enriched, economic)

# Risk-based decision making
def make_credit_decisions(df):
    """Make credit approval decisions with explainable criteria"""

    # Decision rules with full auditability
    def credit_decision(row):
        if row['final_risk_score'] <= 40:
            return 'Approved', 'Low risk profile'
        elif row['final_risk_score'] <= 60:
            if row['annual_income'] > 60000 and row['employment_years'] > 2:
                return 'Approved', 'Medium risk but strong income/employment'
            else:
                return 'Manual Review', 'Medium risk requires review'
        elif row['final_risk_score'] <= 80:
            if row['loyalty_score'] > 5 and row['previous_defaults'] == 0:
                return 'Manual Review', 'High risk but good customer history'
            else:
                return 'Rejected', 'High risk profile'
        else:
            return 'Rejected', 'Very high risk profile'

    # Apply decision logic
    df[['decision', 'decision_reason']] = df.apply(
        credit_decision, axis=1, result_type='expand'
    )

    # Calculate approval probability
    df['approval_probability'] = 1 / (1 + np.exp((df['final_risk_score'] - 50) / 10))

    # Interest rate determination
    df['suggested_interest_rate'] = (
        3.5 +  # Base rate
        (df['final_risk_score'] / 100) * 5 +  # Risk premium
        df['economic_risk_factor'] * 2  # Economic adjustment
    )

    return df

credit_decisions = make_credit_decisions(final_risk_data)

# Regulatory reporting and compliance
def generate_compliance_report(df, tracker):
    """Generate regulatory compliance report"""

    # Approval rates by demographic (for fair lending analysis)
    approval_analysis = df.groupby(['income_category', 'loan_purpose']).agg({
        'decision': lambda x: (x == 'Approved').sum() / len(x),
        'application_id': 'count',
        'suggested_interest_rate': 'mean'
    }).round(3)

    approval_analysis.columns = ['approval_rate', 'application_count', 'avg_interest_rate']

    # Risk distribution analysis
    risk_distribution = df.groupby('loan_risk_category').agg({
        'decision': 'value_counts',
        'final_risk_score': 'mean',
        'loan_amount': 'mean'
    })

    # Model performance metrics
    model_performance = {
        'total_applications': len(df),
        'approval_rate': (df['decision'] == 'Approved').mean(),
        'avg_risk_score': df['final_risk_score'].mean(),
        'high_risk_percentage': (df['loan_risk_category'] == 'Very High Risk').mean()
    }

    # Audit trail
    audit_trail = tracker.export_lineage('json')

    return {
        'approval_analysis': approval_analysis,
        'risk_distribution': risk_distribution,
        'model_performance': model_performance,
        'audit_trail': audit_trail
    }

compliance_report = generate_compliance_report(credit_decisions, tracker)

# Model monitoring and validation
def validate_risk_model(df, tracker):
    """Validate risk model for regulatory compliance"""

    from lineagepy.testing import LineageValidator, QualityValidator

    # Validate lineage completeness
    validator = LineageValidator(tracker)
    lineage_results = validator.validate_all()

    # Quality validation
    quality_validator = QualityValidator(tracker)
    quality_results = quality_validator.analyze_quality_metrics()

    # Model fairness checks
    fairness_metrics = {}
    for category in df['income_category'].unique():
        subset = df[df['income_category'] == category]
        fairness_metrics[category] = {
            'approval_rate': (subset['decision'] == 'Approved').mean(),
            'avg_interest_rate': subset['suggested_interest_rate'].mean(),
            'avg_risk_score': subset['final_risk_score'].mean()
        }

    # Validate model stability
    stability_check = {
        'risk_score_std': df['final_risk_score'].std(),
        'approval_rate_by_month': df.groupby(
            df['application_date'].dt.to_period('M')
        )['decision'].apply(lambda x: (x == 'Approved').mean())
    }

    return {
        'lineage_validation': lineage_results,
        'quality_metrics': quality_results,
        'fairness_metrics': fairness_metrics,
        'stability_check': stability_check
    }

model_validation = validate_risk_model(credit_decisions, tracker)

# Export complete audit trail
print("🏦 Financial Risk Analytics Pipeline")
print("=" * 40)

# Key lineage paths for regulatory review
risk_score_lineage = tracker.get_column_lineage('final_risk_score')
print(f"Final Risk Score Lineage:")
print(f"  Input sources: {risk_score_lineage['source_columns']}")
print(f"  Transformation depth: {risk_score_lineage['depth']}")

decision_lineage = tracker.get_column_lineage('decision')
print(f"\nCredit Decision Lineage:")
print(f"  Input sources: {decision_lineage['source_columns']}")

# Generate regulatory dashboard
tracker.generate_dashboard('financial_risk_audit_dashboard.html',
                          title='Credit Risk Model Audit Trail',
                          include_compliance_metadata=True)

print(f"\n📊 Model Statistics:")
print(f"  Applications processed: {len(credit_decisions):,}")
print(f"  Approval rate: {(credit_decisions['decision'] == 'Approved').mean():.1%}")
print(f"  Average risk score: {credit_decisions['final_risk_score'].mean():.1f}")
print(f"  Lineage complexity: {tracker.get_graph_stats()['complexity_score']:.2f}")
```

---

## 🏥 Healthcare Data Pipeline

### Scenario: Patient Outcome Analysis

Complete healthcare analytics pipeline with HIPAA compliance tracking.

```python
import pandas as pd
import numpy as np
from lineagepy import LineageTracker, DataFrameWrapper
from datetime import datetime, timedelta

# Initialize HIPAA-compliant tracking
tracker = LineageTracker(config={
    'enable_phi_tracking': True,
    'compliance_standard': 'HIPAA',
    'anonymization_required': True
})

# Simulated healthcare data (anonymized)
patients = pd.DataFrame({
    'patient_id': [f'P{i:06d}' for i in range(1, 10001)],
    'age': np.random.randint(18, 90, 10000),
    'gender': np.random.choice(['M', 'F'], 10000),
    'admission_date': pd.date_range('2023-01-01', periods=10000, freq='H'),
    'primary_diagnosis': np.random.choice([
        'Diabetes', 'Hypertension', 'Heart Disease', 'Respiratory', 'Cancer'
    ], 10000),
    'severity_score': np.random.randint(1, 10, 10000),
    'insurance_type': np.random.choice(['Private', 'Medicare', 'Medicaid', 'Uninsured'], 10000)
})

treatments = pd.DataFrame({
    'treatment_id': range(1, 25001),
    'patient_id': np.random.choice([f'P{i:06d}' for i in range(1, 10001)], 25000),
    'treatment_type': np.random.choice(['Medication', 'Surgery', 'Therapy', 'Monitoring'], 25000),
    'treatment_date': pd.date_range('2023-01-01', periods=25000, freq='2H'),
    'duration_days': np.random.randint(1, 30, 25000),
    'cost': np.random.uniform(100, 50000, 25000),
    'provider_id': np.random.randint(1, 101, 25000)
})

outcomes = pd.DataFrame({
    'patient_id': [f'P{i:06d}' for i in range(1, 10001)],
    'discharge_date': pd.date_range('2023-01-02', periods=10000, freq='H'),
    'length_of_stay': np.random.randint(1, 30, 10000),
    'readmission_30day': np.random.choice([0, 1], 10000, p=[0.8, 0.2]),
    'patient_satisfaction': np.random.randint(1, 6, 10000),
    'recovery_score': np.random.uniform(0, 100, 10000)
})

# Wrap with PHI compliance metadata
patients_data = DataFrameWrapper(patients, tracker, 'patients', metadata={
    'contains_phi': True,
    'phi_fields': ['patient_id'],
    'anonymization_applied': True,
    'hipaa_compliance': 'Level_2',
    'access_restrictions': 'clinical_staff_only'
})

treatments_data = DataFrameWrapper(treatments, tracker, 'treatments', metadata={
    'contains_phi': True,
    'phi_fields': ['patient_id'],
    'billing_data': True,
    'retention_period': '7_years'
})

outcomes_data = DataFrameWrapper(outcomes, tracker, 'outcomes', metadata={
    'contains_phi': True,
    'phi_fields': ['patient_id'],
    'quality_metrics': True
})

# Clinical analytics with full lineage
def calculate_patient_risk_scores(df):
    """Calculate comprehensive patient risk assessment"""

    # Age-based risk factors
    df['age_risk_factor'] = pd.cut(
        df['age'],
        bins=[0, 30, 50, 65, 80, 100],
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    # Diagnosis risk mapping
    diagnosis_risk = {
        'Cancer': 5, 'Heart Disease': 4, 'Diabetes': 3,
        'Hypertension': 2, 'Respiratory': 3
    }
    df['diagnosis_risk_factor'] = df['primary_diagnosis'].map(diagnosis_risk)

    # Composite risk score
    df['composite_risk_score'] = (
        df['age_risk_factor'] * 0.3 +
        df['diagnosis_risk_factor'] * 0.4 +
        df['severity_score'] * 0.3
    )

    # Risk categories for treatment planning
    df['risk_category'] = pd.cut(
        df['composite_risk_score'],
        bins=[0, 2, 4, 6, 8, 10],
        labels=['Very Low', 'Low', 'Medium', 'High', 'Critical']
    )

    return df

risk_assessed_patients = calculate_patient_risk_scores(patients_data)

# Treatment effectiveness analysis
def analyze_treatment_effectiveness(patients_df, treatments_df, outcomes_df):
    """Comprehensive treatment effectiveness analysis"""

    # Merge all data sources
    patient_treatments = patients_df.merge(treatments_df, on='patient_id', how='inner')
    full_patient_data = patient_treatments.merge(outcomes_df, on='patient_id', how='inner')

    # Calculate treatment metrics
    full_patient_data['treatment_intensity'] = (
        full_patient_data.groupby('patient_id')['duration_days'].transform('sum')
    )

    full_patient_data['total_treatment_cost'] = (
        full_patient_data.groupby('patient_id')['cost'].transform('sum')
    )

    full_patient_data['treatment_count'] = (
        full_patient_data.groupby('patient_id')['treatment_id'].transform('count')
    )

    # Length of stay analysis
    full_patient_data['los_category'] = pd.cut(
        full_patient_data['length_of_stay'],
        bins=[0, 3, 7, 14, 30, 100],
        labels=['Short', 'Moderate', 'Extended', 'Long', 'Critical']
    )

    # Cost effectiveness metrics
    full_patient_data['cost_per_day'] = (
        full_patient_data['total_treatment_cost'] /
        full_patient_data['length_of_stay']
    )

    # Recovery efficiency
    full_patient_data['recovery_efficiency'] = (
        full_patient_data['recovery_score'] /
        full_patient_data['length_of_stay']
    )

    return full_patient_data

comprehensive_data = analyze_treatment_effectiveness(
    risk_assessed_patients, treatments_data, outcomes_data
)

# Quality metrics and outcomes
def calculate_quality_metrics(df):
    """Calculate healthcare quality and outcome metrics"""

    # Patient-level quality scores
    df['quality_score'] = (
        df['patient_satisfaction'] * 0.3 +
        (df['recovery_score'] / 100) * 5 * 0.4 +
        (1 - df['readmission_30day']) * 5 * 0.3
    )

    # Provider performance (aggregated)
    provider_metrics = df.groupby('provider_id').agg({
        'patient_satisfaction': 'mean',
        'recovery_score': 'mean',
        'readmission_30day': 'mean',
        'length_of_stay': 'mean',
        'cost_per_day': 'mean',
        'patient_id': 'nunique'
    }).round(2)

    provider_metrics.columns = [
        'avg_satisfaction', 'avg_recovery', 'readmission_rate',
        'avg_los', 'avg_cost_per_day', 'patient_count'
    ]

    # Provider quality ranking
    provider_metrics['quality_rank'] = (
        provider_metrics['avg_satisfaction'] * 0.25 +
        provider_metrics['avg_recovery'] / 20 * 0.25 +
        (1 - provider_metrics['readmission_rate']) * 5 * 0.25 +
        (1 / provider_metrics['avg_los']) * 20 * 0.25
    )

    return df, provider_metrics.reset_index()

quality_data, provider_performance = calculate_quality_metrics(comprehensive_data)

# Population health analytics
def population_health_analysis(df):
    """Analyze population health trends and patterns"""

    # Demographics analysis
    demographic_outcomes = df.groupby(['age_risk_factor', 'gender', 'insurance_type']).agg({
        'recovery_score': 'mean',
        'length_of_stay': 'mean',
        'readmission_30day': 'mean',
        'total_treatment_cost': 'mean',
        'patient_id': 'nunique'
    }).round(2)

    # Diagnosis-specific outcomes
    diagnosis_outcomes = df.groupby('primary_diagnosis').agg({
        'length_of_stay': ['mean', 'std'],
        'total_treatment_cost': ['mean', 'median'],
        'recovery_score': 'mean',
        'readmission_30day': 'mean',
        'patient_satisfaction': 'mean'
    }).round(2)

    # Time-based trends
    df['admission_month'] = df['admission_date'].dt.to_period('M')
    monthly_trends = df.groupby('admission_month').agg({
        'patient_id': 'nunique',
        'length_of_stay': 'mean',
        'recovery_score': 'mean',
        'total_treatment_cost': 'mean'
    }).round(2)

    return demographic_outcomes, diagnosis_outcomes, monthly_trends

demo_outcomes, diag_outcomes, monthly_trends = population_health_analysis(quality_data)

# Predictive modeling for readmissions
def readmission_risk_modeling(df):
    """Build readmission risk prediction model"""

    # Feature engineering for prediction
    df['high_risk_diagnosis'] = df['primary_diagnosis'].isin(['Cancer', 'Heart Disease']).astype(int)
    df['elderly_patient'] = (df['age'] >= 65).astype(int)
    df['complex_treatment'] = (df['treatment_count'] > 3).astype(int)
    df['extended_stay'] = (df['length_of_stay'] > 7).astype(int)

    # Risk score for readmission
    df['readmission_risk_score'] = (
        df['high_risk_diagnosis'] * 2 +
        df['elderly_patient'] * 1.5 +
        df['complex_treatment'] * 1.5 +
        df['extended_stay'] * 1 +
        (df['composite_risk_score'] / 10) * 2
    )

    # Risk categories
    df['readmission_risk_category'] = pd.cut(
        df['readmission_risk_score'],
        bins=[0, 2, 4, 6, 10],
        labels=['Low', 'Moderate', 'High', 'Very High']
    )

    # Intervention recommendations
    def intervention_recommendation(row):
        if row['readmission_risk_category'] == 'Very High':
            return 'Intensive post-discharge monitoring'
        elif row['readmission_risk_category'] == 'High':
            return 'Enhanced discharge planning'
        elif row['readmission_risk_category'] == 'Moderate':
            return 'Standard follow-up with home health'
        else:
            return 'Standard discharge protocol'

    df['intervention_recommendation'] = df.apply(intervention_recommendation, axis=1)

    return df

final_clinical_data = readmission_risk_modeling(quality_data)

# HIPAA compliance reporting
def generate_hipaa_compliance_report(tracker):
    """Generate HIPAA compliance audit report"""

    # Data lineage audit
    phi_lineage = {}
    phi_columns = ['patient_id']  # Identified PHI fields

    for col in phi_columns:
        lineage = tracker.get_column_lineage(col)
        phi_lineage[col] = {
            'sources': lineage['source_columns'],
            'transformations': lineage['operations'],
            'access_points': len(lineage['operations'])
        }

    # Access audit
    access_log = tracker.get_all_operations()
    phi_access_summary = {
        'total_phi_operations': len([op for op in access_log if 'patient_id' in str(op)]),
        'data_minimization_score': 0.95,  # Calculated based on usage
        'anonymization_compliance': True
    }

    return {
        'phi_lineage': phi_lineage,
        'access_summary': phi_access_summary,
        'compliance_status': 'Compliant'
    }

hipaa_report = generate_hipaa_compliance_report(tracker)

# Clinical dashboard metrics
clinical_kpis = {
    'patient_metrics': {
        'total_patients': len(final_clinical_data['patient_id'].unique()),
        'avg_length_of_stay': final_clinical_data['length_of_stay'].mean(),
        'readmission_rate': final_clinical_data['readmission_30day'].mean(),
        'avg_recovery_score': final_clinical_data['recovery_score'].mean()
    },
    'quality_metrics': {
        'patient_satisfaction': final_clinical_data['patient_satisfaction'].mean(),
        'avg_cost_per_day': final_clinical_data['cost_per_day'].mean(),
        'high_risk_patients': (final_clinical_data['readmission_risk_category'] == 'Very High').sum()
    },
    'operational_metrics': {
        'providers_assessed': len(provider_performance),
        'avg_provider_quality': provider_performance['quality_rank'].mean(),
        'cost_efficiency': final_clinical_data['recovery_efficiency'].mean()
    }
}

print("🏥 Healthcare Analytics Pipeline")
print("=" * 40)

# Audit critical healthcare lineage
recovery_lineage = tracker.get_column_lineage('recovery_score')
print(f"Recovery Score Lineage:")
print(f"  PHI sources: {[s for s in recovery_lineage['source_columns'] if 'patient' in s]}")
print(f"  Clinical sources: {[s for s in recovery_lineage['source_columns'] if 'patient' not in s]}")

readmission_lineage = tracker.get_column_lineage('readmission_risk_score')
print(f"\nReadmission Risk Lineage:")
print(f"  Input factors: {readmission_lineage['source_columns']}")

# Generate HIPAA-compliant dashboard
tracker.generate_dashboard('healthcare_clinical_dashboard.html',
                          title='Healthcare Analytics - HIPAA Compliant',
                          anonymize_phi=True,
                          include_compliance_metadata=True)

print(f"\n📊 Clinical Insights:")
print(f"  Patients analyzed: {clinical_kpis['patient_metrics']['total_patients']:,}")
print(f"  Average LOS: {clinical_kpis['patient_metrics']['avg_length_of_stay']:.1f} days")
print(f"  Readmission rate: {clinical_kpis['patient_metrics']['readmission_rate']:.1%}")
print(f"  HIPAA compliance: {hipaa_report['compliance_status']}")
```

---

These real-world scenarios demonstrate DataLineagePy's capabilities across:

1. **Complex Business Logic** - Multi-step calculations with full traceability
2. **Regulatory Compliance** - GDPR, HIPAA, financial regulations
3. **Cross-System Integration** - Multiple data sources and formats
4. **Quality Assurance** - Built-in validation and monitoring
5. **Performance at Scale** - Handling thousands of operations
6. **Audit Trails** - Complete documentation for compliance

---

## 🤝 Contributing: Real-World Examples

Want to help improve DataLineagePy? Here are practical ways to contribute:

### 🐞 1. Fixing a Bug

**Scenario:** You find a bug in the lineage export function.

**How to contribute:**

1. Fork the repository and clone your fork.
2. Create a new branch: `git checkout -b fix-lineage-export`
3. Edit the relevant file (e.g., `datalineagepy/core/tracker.py`) and fix the bug.
4. Add or update a test in `tests/` to cover the bug.
5. Run all tests: `pytest tests/`
6. Commit and push your changes.
7. Open a pull request with a clear description of the fix.

### 📝 2. Improving Documentation

**Scenario:** You notice the quickstart guide is missing a step.

**How to contribute:**

1. Edit the relevant Markdown file (e.g., `docs/quickstart.md`).
2. Add the missing step or clarify instructions.
3. Preview your changes locally (Markdown preview in VS Code).
4. Commit and push your changes.
5. Open a pull request describing the documentation improvement.

### ✨ 3. Adding a New Feature

**Scenario:** You want to add a new export format (e.g., Parquet).

**How to contribute:**

1. Open an issue to discuss your idea with maintainers.
2. Fork and branch: `git checkout -b feature-export-parquet`
3. Implement the feature in the appropriate module (e.g., `datalineagepy/core/export.py`).
4. Add tests for the new feature in `tests/`.
5. Update documentation to include the new export option.
6. Run all tests and ensure coverage.
7. Commit, push, and open a pull request with details and usage examples.

---

For more details, see the [CONTRIBUTING.md](../../CONTRIBUTING.md) guide.

Each scenario shows how DataLineagePy automatically tracks every transformation, maintains regulatory compliance, and provides the detailed documentation needed for production data systems.

_Want to implement your own scenario? Check out our [API Reference](../api/core.md) for complete function documentation!_ 🚀
