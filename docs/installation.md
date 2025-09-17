# 💾 Installation Guide

## 🌟 **Enterprise Installation for DataLineagePy**

This comprehensive guide covers all installation methods for DataLineagePy, from quick development setup to enterprise production deployments.

> **📅 Last Updated**: June 19, 2025  
> **🔧 Supported Platforms**: Windows, macOS, Linux

# � DataLineagePy 3.0 — Installation Guide

---

<div align="center">
<img src="https://raw.githubusercontent.com/Arbaznazir/DataLineagePy/main/docs/assets/logo.png" alt="DataLineagePy Logo" width="120"/>
</div>

<h2 align="center">💾 Professional, Beautiful, and Effortless Installation</h2>

<p align="center">
<b>Get started with DataLineagePy in minutes — from local development to enterprise production.</b><br>
<i>All platforms, all Python versions, all features. No headaches.</i>
</p>

---

## 📋 System Requirements

| Environment | Python | Memory | Storage | CPU    | OS/Platform                  |
| ----------- | ------ | ------ | ------- | ------ | ---------------------------- |
| Minimum     | 3.8+   | 512MB  | 100MB   | 1 core | Win 10+, macOS 10.14+, Linux |
| Recommended | 3.11+  | 2GB    | 1GB     | 2+     | All modern distros           |
| Enterprise  | 3.11+  | 4GB+   | 5GB+    | 4+     | Hardened, isolated           |

---

## 🚀 Quick Installation (All Platforms)

### 1. PyPI (Recommended)

```bash
pip install datalineagepy
python -c "import datalineagepy; print(f'DataLineagePy v{datalineagepy.__version__} installed!')"
```

### 2. With Optional Features

```bash
# Visualization support
pip install datalineagepy[viz]
# All features
pip install datalineagepy[all]
# Dev tools
pip install datalineagepy[dev]
```

### 3. Latest Development Version

```bash
pip install git+https://github.com/Arbaznazir/DataLineagePy.git
# Or a specific branch
pip install git+https://github.com/Arbaznazir/DataLineagePy.git@development
```

---

## 🛠️ Professional Installation Methods

### A. Virtual Environment (Best Practice)

#### Windows

```powershell
mkdir my_datalineage_project
cd my_datalineage_project
python -m venv datalineage_env
datalineage_env\Scripts\activate
pip install datalineagepy
python -c "import datalineagepy; print('Success!')"
```

#### macOS/Linux

```bash
mkdir my_datalineage_project
cd my_datalineage_project
python3 -m venv datalineage_env
source datalineage_env/bin/activate
pip install datalineagepy
python -c "import datalineagepy; print('Success!')"
```

### B. Conda Environment

```bash
conda create -n datalineage python=3.11
conda activate datalineage
pip install datalineagepy
# (Coming soon) conda install -c conda-forge datalineagepy
```

### C. Docker (Enterprise/Cloud)

```bash
docker pull datalineagepy/datalineagepy:latest
docker run -it datalineagepy/datalineagepy:latest python
docker run -it -v $(pwd):/workspace datalineagepy/datalineagepy:latest
```

#### Custom Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install datalineagepy
COPY . .
CMD ["python", "your_lineage_script.py"]
```

### D. Development Installation

```bash
git clone https://github.com/Arbaznazir/DataLineagePy.git
cd DataLineagePy
python -m venv dev_env
# Windows: dev_env\Scripts\activate
# macOS/Linux: source dev_env/bin/activate
pip install -e .
pip install -e .[dev]
pytest tests/
```

---

## 🔧 Configuration & Best Practices

### Basic Configuration

Create `datalineage_config.py`:

```python
DATALINEAGE_CONFIG = {
  "default_tracker_name": "my_pipeline",
  # ...other options...
  "log_level": "INFO"
}
```

### Environment Variables

```bash
export DATALINEAGE_DEFAULT_TRACKER="production_pipeline"
export DATALINEAGE_ENABLE_MONITORING="true"
export DATALINEAGE_LOG_LEVEL="INFO"
export DATALINEAGE_EXPORT_PATH="/data/lineage"
```

### Advanced Configuration

```python
from datalineagepy import LineageTracker
tracker = LineageTracker(
  name="enterprise_pipeline",
  # ...advanced options...
)
```

---

## ✅ Installation Verification

### Basic Verification

```python
import datalineagepy
import pandas as pd
print(f"✅ DataLineagePy Version: {datalineagepy.__version__}")
from datalineagepy import LineageTracker, LineageDataFrame
tracker = LineageTracker(name="test_tracker")
df = pd.DataFrame({'test': [1, 2, 3]})
ldf = LineageDataFrame(df, name="test_data", tracker=tracker)
result = ldf.filter(ldf._df['test'] > 1)
print("🎉 Installation verified!")
```

### Advanced Verification

```python
import datalineagepy
from datalineagepy import LineageTracker, LineageDataFrame
from datalineagepy.core.analytics import DataProfiler
from datalineagepy.core.validation import DataValidator
from datalineagepy.visualization import GraphVisualizer
import pandas as pd
tracker = LineageTracker(name="verification_test")
df = pd.DataFrame({
  'id': [1, 2, 3, 4, 5],
  # ...
  'category': ['A', 'B', 'A', 'B', 'A']
})
ldf = LineageDataFrame(df, name="test_data", tracker=tracker)
```

---

## 🛡️ Troubleshooting & FAQ

### Common Issues

| Problem               | Solution                                                         |
| --------------------- | ---------------------------------------------------------------- |
| `ModuleNotFoundError` | Ensure you activated your environment and installed the package. |
| Permission denied     | Run terminal/IDE as admin or check file permissions.             |
| Python version error  | Use `python --version` to check, upgrade if needed.              |
| Dependency conflict   | Use a fresh virtual environment.                                 |
| Docker networking     | Use `--network host` or check firewall settings.                 |

### Best Practices

- Always use a virtual environment for isolation
- Pin your dependencies for reproducible builds
- For enterprise, use Docker or Conda for maximum reproducibility
- Keep DataLineagePy updated for latest features and security
- See [FAQ](faq.md) for more troubleshooting

---

<p align="center">
<b>Need help? See the <a href="faq.md">FAQ</a> or <a href="https://github.com/Arbaznazir/DataLineagePy/issues">open an issue</a>.</b>
</p>

print("🔍 Running comprehensive verification...")

# Test core functionality

tracker = LineageTracker(name="verification_test")
df = pd.DataFrame({
'id': [1, 2, 3, 4, 5],
'value': [10, 20, 30, 40, 50],
'category': ['A', 'B', 'A', 'B', 'A']
})
ldf = LineageDataFrame(df, name="test_data", tracker=tracker)

# Test operations

filtered = ldf.filter(ldf.\_df['value'] > 25)
grouped = filtered.groupby('category').agg({'value': 'sum'})
print("✅ Data operations working")

# Test analytics

profiler = DataProfiler()
profile = profiler.profile_dataset(ldf)
print(f"✅ Data profiling working - Quality score: {profile.get('quality_score', 'N/A')}")

# Test validation

validator = DataValidator()
rules = {'completeness': {'threshold': 0.8}}
validation_result = validator.validate_dataframe(ldf, rules)
print("✅ Data validation working")

# Test visualization

try:
visualizer = GraphVisualizer(tracker)
print("✅ Visualization module loaded")
except ImportError as e:
print(f"⚠️ Visualization dependencies missing: {e}")
print(" Install with: pip install datalineagepy[viz]")

# Test export

lineage_data = tracker.export_lineage()
print("✅ Lineage export working")

print("\n🎉 All advanced features verified successfully!")

````

### **Performance Verification**

```python
# performance_verification.py
import time
import psutil
import pandas as pd
from datalineagepy import LineageTracker, LineageDataFrame

print("⚡ Running performance verification...")

# Create large test dataset
size = 10000
df = pd.DataFrame({
    'id': range(size),
    'value': range(size),
    'category': ['A', 'B', 'C'] * (size // 3 + 1)
})

# Measure performance
start_time = time.time()
start_memory = psutil.Process().memory_info().rss / 1024 / 1024

tracker = LineageTracker(name="performance_test")
ldf = LineageDataFrame(df, name="large_data", tracker=tracker)

# Perform operations
filtered = ldf.filter(ldf._df['value'] > size//2)
grouped = filtered.groupby('category').agg({'value': ['sum', 'mean', 'count']})

end_time = time.time()
end_memory = psutil.Process().memory_info().rss / 1024 / 1024

execution_time = end_time - start_time
memory_used = end_memory - start_memory

print(f"✅ Performance test completed:")
print(f"   📊 Dataset size: {size:,} rows")
print(f"   ⏱️  Execution time: {execution_time:.3f} seconds")
print(f"   💾 Memory used: {memory_used:.1f} MB")
print(f"   📈 Lineage nodes created: {len(tracker.nodes)}")

# Performance thresholds
if execution_time < 1.0:
    print("✅ Performance: Excellent")
elif execution_time < 5.0:
    print("✅ Performance: Good")
else:
    print("⚠️  Performance: Consider optimization")

print("\n🎉 Performance verification completed!")
````

---

## 🐳 **Container Deployment**

### **Docker Compose Setup**

```yaml
# docker-compose.yml
version: "3.8"

services:
  datalineage:
    image: datalineagepy/datalineagepy:latest
    container_name: datalineage_app
    volumes:
      - ./data:/app/data
      - ./output:/app/output
    environment:
      - DATALINEAGE_DEFAULT_TRACKER=production_pipeline
      - DATALINEAGE_ENABLE_MONITORING=true
    command: python your_pipeline.py

  jupyter:
    image: jupyter/datascience-notebook
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/home/jovyan/work
    environment:
      - JUPYTER_TOKEN=your_token_here
    command: start-notebook.sh --NotebookApp.token='your_token_here'
```

### **Kubernetes Deployment**

```yaml
# kubernetes-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datalineage-deployment
  labels:
    app: datalineage
spec:
  replicas: 3
  selector:
    matchLabels:
      app: datalineage
  template:
    metadata:
      labels:
        app: datalineage
    spec:
      containers:
        - name: datalineage
          image: datalineagepy/datalineagepy:latest
          ports:
            - containerPort: 8080
          env:
            - name: DATALINEAGE_ENV
              value: "production"
            - name: DATALINEAGE_ENABLE_MONITORING
              value: "true"
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          volumeMounts:
            - name: data-volume
              mountPath: /app/data
      volumes:
        - name: data-volume
          persistentVolumeClaim:
            claimName: datalineage-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: datalineage-service
spec:
  selector:
    app: datalineage
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: LoadBalancer
```

---

## 🔧 **Troubleshooting Installation Issues**

### **Common Issues & Solutions**

#### **Issue 1: Python Version Compatibility**

```bash
# Error: "DataLineagePy requires Python 3.8+"
# Solution: Check Python version
python --version

# If Python 3.8+ not available, install it:
# Windows: Download from python.org
# macOS: brew install python@3.11
# Ubuntu: apt-get install python3.11
```

#### **Issue 2: Permission Errors**

```bash
# Error: "Permission denied" during pip install
# Solution: Use user installation
pip install --user datalineagepy

# Or use virtual environment (recommended)
python -m venv env && source env/bin/activate
```

#### **Issue 3: Missing Dependencies**

```bash
# Error: "No module named 'pandas'"
# Solution: Install dependencies explicitly
pip install pandas numpy matplotlib
pip install datalineagepy
```

#### **Issue 4: Import Errors**

```python
# Error: "ImportError: cannot import name 'LineageTracker'"
# Solution: Check installation
import sys
print(sys.path)

# Reinstall if necessary
pip uninstall datalineagepy -y
pip install datalineagepy
```

#### **Issue 5: Memory Issues**

```python
# Error: "MemoryError" with large datasets
# Solution: Enable memory optimization
from datalineagepy import LineageTracker

tracker = LineageTracker(
    name="memory_optimized",
    config={"memory_optimization": True}
)
```

### **Advanced Troubleshooting**

#### **Debug Installation**

```bash
# Create debug environment
python -m venv debug_env
source debug_env/bin/activate  # Windows: debug_env\Scripts\activate

# Install with verbose output
pip install -v datalineagepy

# Check package info
pip show datalineagepy
pip list | grep datalineage
```

#### **System Information Collection**

```python
# system_info.py
import sys
import platform
import pandas as pd
import numpy as np

print("🔍 System Information:")
print(f"Python Version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.architecture()}")
print(f"Pandas Version: {pd.__version__}")
print(f"NumPy Version: {np.__version__}")

try:
    import datalineagepy
    print(f"DataLineagePy Version: {datalineagepy.__version__}")
    print("✅ DataLineagePy imported successfully")
except ImportError as e:
    print(f"❌ DataLineagePy import failed: {e}")
```

---

## 📚 **Next Steps**

After successful installation:

1. **📖 [Quick Start Guide](quickstart.md)** - Get started in 30 seconds
2. **🛠️ [API Reference](api/)** - Explore all available methods
3. **📊 [Examples](examples/)** - See practical usage examples
4. **🏢 [Production Deployment](advanced/production.md)** - Enterprise setup

---

## 🆘 **Getting Help**

If you encounter issues:

- **📚 [FAQ](faq.md)** - Check frequently asked questions
- **🐛 [GitHub Issues](https://github.com/Arbaznazir/DataLineagePy/issues)** - Report bugs
- **💬 [Discussions](https://github.com/Arbaznazir/DataLineagePy/discussions)** - Community support
- **📧 [Enterprise Support](mailto:enterprise@datalineagepy.com)** - Priority support

---

_Installation guide last updated: June 19, 2025_
