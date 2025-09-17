# 🚀 DataLineagePy 3.0

**Enterprise-Grade Python Data Lineage Tracking**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)](https://github.com/Arbaznazir/DataLineagePy)
[![Performance Score](https://img.shields.io/badge/performance-92.1%2F100-brightgreen.svg)](https://github.com/Arbaznazir/DataLineagePy)
[![Enterprise Grade](https://img.shields.io/badge/enterprise-grade%20ready-gold.svg)](https://github.com/Arbaznazir/DataLineagePy)

---

<div align="center">
  <img src="https://raw.githubusercontent.com/Arbaznazir/DataLineagePy/main/docs/assets/logo.png" width="180" alt="DataLineagePy Logo"/>
  <h2>Beautiful, Powerful, and Effortless Data Lineage for Python</h2>
  <p>Track, visualize, and govern your data pipelines with zero friction.</p>
</div>

---

## 🌟 Why DataLineagePy?

- **Automatic, column-level lineage tracking** for all pandas DataFrames
- **Enterprise performance**: memory-optimized, scalable, and production-ready
- **Stunning visualizations**: interactive dashboards, HTML, PNG, SVG, and more
- **Plug-and-play connectors**: MySQL, PostgreSQL, SQLite, and custom sources
- **Security & compliance**: RBAC, AES-256 encryption, audit trails
- **Real-time collaboration**: WebSocket server/client for team workflows
- **ML/AI pipeline tracking**: Full auditability for machine learning steps
- **Cloud-native deployment**: Docker, Kubernetes, Helm, Terraform

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Core Features](#core-features)
- [Usage Guide](#usage-guide)
- [Database Connectors](#database-connectors)
- [Visualization & Reporting](#visualization--reporting)
- [Performance Monitoring](#performance-monitoring)
- [Security & Compliance](#security--compliance)
- [ML/AI Pipeline Tracking](#mlai-pipeline-tracking)
- [Enterprise Deployment](#enterprise-deployment)
- [Use Cases](#use-cases)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## 🚀 Quick Start

```bash
pip install datalineagepy
```

```python
from datalineagepy import LineageTracker, LineageDataFrame
import pandas as pd

df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
tracker = LineageTracker(name="demo")
ldf = LineageDataFrame(df, name="my_df", tracker=tracker)
ldf2 = ldf.filter(ldf._df['a'] > 1)
ldf3 = ldf2.assign(c=ldf2._df['a'] + ldf2._df['b'])
tracker.visualize()  # Interactive HTML dashboard
tracker.export_lineage("lineage.json")
```

---

## 💾 Installation

- **PyPI**: `pip install datalineagepy`
- **With visualization**: `pip install datalineagepy[viz]`
- **All features**: `pip install datalineagepy[all]`
- **Conda**: `conda install -c conda-forge datalineagepy` _(coming soon)_
- **Docker**: `docker pull datalineagepy/datalineagepy:latest`

See [Installation Guide](docs/installation.md) for advanced and enterprise setup.

---

## 📚 Core Features

- **Automatic lineage tracking** for pandas DataFrames
- **Data validation**: completeness, uniqueness, range, custom rules
- **Profiling & analytics**: quality scoring, missing data, correlations
- **Visualization**: HTML, PNG, SVG, interactive dashboards
- **Performance monitoring**: execution time, memory, alerts
- **Security**: RBAC, AES-256 encryption, audit trail
- **Custom connectors**: SDK for any data source
- **Versioning**: save, diff, rollback lineage graphs
- **Collaboration**: real-time editing/viewing
- **ML/AI pipeline tracking**: AutoMLTracker for full auditability

---

## 🔧 Usage Guide

### 1. Lineage Tracking

```python
from datalineagepy import LineageTracker, LineageDataFrame
import pandas as pd
tracker = LineageTracker(name="my_pipeline")
df = pd.DataFrame({'x': [1,2,3], 'y': [4,5,6]})
ldf = LineageDataFrame(df, name="input", tracker=tracker)
ldf2 = ldf.assign(z=ldf._df['x'] + ldf._df['y'])
print(tracker.export_graph())
```

### 2. Data Validation

```python
from datalineagepy.core.validation import DataValidator
validator = DataValidator(tracker)
rules = {'completeness': {'threshold': 0.9}, 'uniqueness': {'columns': ['x']}}
results = validator.validate_dataframe(ldf, rules)
print(results)
```

### 3. Profiling & Analytics

```python
from datalineagepy.core.analytics import DataProfiler
profiler = DataProfiler(tracker)
profile = profiler.profile_dataset(ldf, include_correlations=True)
print(profile)
```

### 4. Visualization & Reporting

```python
from datalineagepy.visualization.graph_visualizer import GraphVisualizer
visualizer = GraphVisualizer(tracker)
visualizer.generate_html("lineage.html")
visualizer.generate_png("lineage.png")
```

### 5. Performance Monitoring

```python
from datalineagepy.core.performance import PerformanceMonitor
monitor = PerformanceMonitor(tracker)
monitor.start_monitoring()
_ = ldf._df.sum()
monitor.stop_monitoring()
print(monitor.get_performance_summary())
```

### 6. Security & Compliance

```python
from datalineagepy.security.rbac import RBACManager
rbac = RBACManager()
rbac.add_role('admin', ['read', 'write'])
rbac.add_user('alice', ['admin'])
print(rbac.check_access('alice', 'write'))

from datalineagepy.security.encryption.data_encryption import EncryptionManager
import os
os.environ['MASTER_ENCRYPTION_KEY'] = 'supersecretkey1234567890123456'
enc_mgr = EncryptionManager()
secret = 'Sensitive Data'
encrypted = enc_mgr.encrypt_sensitive_data(secret)
decrypted = enc_mgr.decrypt_sensitive_data(encrypted)
print(decrypted)
```

### 7. Database Connectors

```python
from datalineagepy.connectors.database.mysql_connector import MySQLConnector
from datalineagepy.core import LineageTracker
db_config = {'host': 'localhost', 'user': 'root', 'password': 'password', 'database': 'test_db'}
tracker = LineageTracker()
conn = MySQLConnector(**db_config, lineage_tracker=tracker)
conn.execute_query('SELECT * FROM test_table')
conn.close()
```

### 8. ML/AI Pipeline Tracking

```python
from datalineagepy import AutoMLTracker
tracker = AutoMLTracker(name='ml_pipeline')
tracker.log_step('fit', model='LogisticRegression', params={'solver': 'lbfgs'})
tracker.log_step('predict', model='LogisticRegression')
print(tracker.export_ai_ready_format())
```

---

## 📊 Visualization & Reporting

- **Interactive HTML dashboards**: `tracker.visualize()`
- **Export formats**: JSON, DOT, PNG, SVG, Excel, CSV
- **Custom visualizations**: Use `GraphVisualizer` for advanced needs

---

## 🗄️ Database Connectors

- **MySQL, PostgreSQL, SQLite**: Full lineage tracking for every query
- **Custom connectors**: Build your own with the SDK
- See [Database Connectors Guide](docs/user-guide/database-connectors.md)

---

## ⚡ Performance Monitoring

- **Track execution time, memory, and operation stats**
- **Alerting**: Slack, Email, custom hooks
- **Production monitoring**: Integrate with Prometheus, Grafana, etc.

---

## 🔒 Security & Compliance

- **RBAC**: Role-based access control for users and actions
- **AES-256 encryption**: At-rest and in-transit data protection
- **Audit trail**: Full operation history for compliance

---

## 🤖 ML/AI Pipeline Tracking

- **AutoMLTracker**: Log, audit, and export every ML pipeline step
- **Explainability**: Export pipeline steps for downstream analysis

---

## ☁️ Enterprise Deployment

- **Docker, Kubernetes, Helm, Terraform**: Cloud-native ready
- **Production scripts**: See `deploy/` for examples

---

## 💡 Use Cases

- **Data science**: Reproducibility, experiment tracking, Jupyter integration
- **Enterprise ETL**: Production pipelines, data quality, compliance
- **Data governance**: Impact analysis, documentation, audit trails
- **ML/AI**: Pipeline explainability, model audit, feature tracking

---

## 📖 Documentation

- [User Guide](docs/user-guide/)
- [API Reference](docs/api/)
- [Quick Start](docs/quickstart.md)
- [Enterprise Guide](docs/advanced/production.md)
- [FAQ](docs/faq.md)
- [Examples](examples/)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">
  <b>DataLineagePy 3.0 &mdash; The new standard for Python data lineage</b><br/>
  <i>Beautiful. Powerful. Effortless.</i>
</div>
