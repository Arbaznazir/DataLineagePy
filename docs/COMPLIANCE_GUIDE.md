# DataLineagePy Compliance Framework Guide

## Overview

The DataLineagePy Compliance Framework provides comprehensive regulatory compliance capabilities for enterprise data lineage operations. It supports multiple compliance standards including GDPR, SOX, HIPAA, PCI DSS, ISO 27001, and NIST frameworks.

## Table of Contents

1. [Architecture](#architecture)
2. [Supported Standards](#supported-standards)
3. [Quick Start](#quick-start)
4. [GDPR Compliance](#gdpr-compliance)
5. [SOX Compliance](#sox-compliance)
6. [HIPAA Compliance](#hipaa-compliance)
7. [Audit System](#audit-system)
8. [Unified Framework](#unified-framework)
9. [Configuration](#configuration)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [API Reference](#api-reference)

## Architecture

The compliance framework is built with a modular architecture:

```
datalineagepy/compliance/
├── __init__.py          # Module exports and factory functions
├── framework.py         # Unified compliance framework
├── audit.py            # Audit logging and reporting
├── gdpr.py             # GDPR compliance implementation
├── sox.py              # SOX compliance implementation
├── hipaa.py            # HIPAA compliance implementation
├── data_governance.py  # Data governance framework (future)
└── policy_engine.py    # Policy enforcement engine (future)
```

### Key Components

- **ComplianceFramework**: Unified interface for all compliance standards
- **ComplianceAuditor**: Centralized audit logging and reporting
- **Standard-specific modules**: GDPR, SOX, HIPAA implementations
- **AuditLog**: Thread-safe audit event storage and querying

## Supported Standards

| Standard | Status | Description |
|----------|--------|-------------|
| GDPR | ✅ Complete | General Data Protection Regulation |
| SOX | ✅ Complete | Sarbanes-Oxley Act |
| HIPAA | ✅ Complete | Health Insurance Portability and Accountability Act |
| PCI DSS | 🚧 Planned | Payment Card Industry Data Security Standard |
| ISO 27001 | 🚧 Planned | Information Security Management |
| NIST | 🚧 Planned | National Institute of Standards and Technology |

## Quick Start

### Installation

```bash
# Install compliance dependencies
pip install -r requirements-compliance.txt
```

### Basic Usage

```python
from datalineagepy.compliance import create_compliance_framework

# Create unified compliance framework
framework = create_compliance_framework(
    standards=["GDPR", "SOX", "HIPAA"]
)

# Process data with compliance checks
processing_id = framework.process_data(
    data_type="personal_customer_data",
    data_value={"name": "John Doe", "email": "john@example.com"},
    subject_id="customer_123",
    processing_context={
        "legal_basis": "consent",
        "purpose": "marketing",
        "user_id": "data_processor_1"
    }
)

# Generate compliance dashboard
dashboard = framework.generate_compliance_dashboard()
print(f"Compliance Status: {dashboard['compliance_overview']['overall_status']}")
```

## GDPR Compliance

### Features

- **Consent Management**: Record, validate, and track consent
- **Data Subject Rights**: Handle access, rectification, erasure, portability
- **Legal Basis Tracking**: Ensure valid legal basis for processing
- **Breach Notification**: Automated breach detection and reporting
- **Privacy Impact Assessments**: Risk assessment for high-risk processing
- **Data Protection Officer**: DPO management and reporting

### Example Usage

```python
from datalineagepy.compliance import create_gdpr_compliance
from datalineagepy.compliance import LegalBasis, ProcessingPurpose

# Create GDPR compliance instance
gdpr = create_gdpr_compliance()

# Record consent
consent_id = gdpr.consent_manager.record_consent(
    subject_id="user_123",
    purpose=ProcessingPurpose.MARKETING,
    legal_basis=LegalBasis.CONSENT,
    consent_text="I agree to receive marketing emails"
)

# Process personal data
processing_id = gdpr.process_personal_data(
    subject_id="user_123",
    data_type="email_address",
    data_value="user@example.com",
    legal_basis=LegalBasis.CONSENT,
    purpose=ProcessingPurpose.MARKETING
)

# Handle data subject request
request_id = gdpr.data_subject_rights.handle_access_request(
    subject_id="user_123",
    request_type="access",
    requester_email="user@example.com"
)
```

### GDPR Configuration

```python
gdpr_config = {
    "consent_retention_days": 1095,  # 3 years
    "breach_notification_hours": 72,
    "data_retention_days": 2555,  # 7 years
    "require_explicit_consent": True,
    "enable_right_to_be_forgotten": True,
    "enable_data_portability": True,
    "privacy_by_design": True
}
```

## SOX Compliance

### Features

- **Financial Data Governance**: Classification and protection of financial data
- **Internal Controls**: Implementation and testing of controls
- **Audit Trail Management**: Comprehensive audit trails for financial processes
- **Change Management**: Approval workflows for system changes
- **Access Controls**: Role-based access to financial systems
- **Segregation of Duties**: Enforcement of duty separation

### Example Usage

```python
from datalineagepy.compliance import create_sox_compliance
from datalineagepy.compliance import ControlType, FinancialDataType

# Create SOX compliance instance
sox = create_sox_compliance()

# Add internal control
control_id = sox.internal_controls.add_control(
    control_type=ControlType.PREVENTIVE,
    description="Segregation of duties for financial reporting",
    owner="CFO",
    frequency="continuous"
)

# Classify financial data
sox.financial_governance.classify_financial_data(
    data_id="revenue_q1_2024",
    data_type=FinancialDataType.REVENUE,
    sensitivity="high"
)

# Request change approval
change_id = sox.change_management.request_change(
    change_type="system_configuration",
    description="Update financial reporting parameters",
    requester="system_admin",
    business_justification="Quarterly reporting requirements"
)
```

### SOX Configuration

```python
sox_config = {
    "audit_retention_years": 7,
    "require_change_approval": True,
    "segregation_of_duties": True,
    "financial_controls_testing": True,
    "quarterly_assessments": True,
    "management_certification": True
}
```

## HIPAA Compliance

### Features

- **PHI Protection**: Encryption and access controls for Protected Health Information
- **Security Rule**: Administrative, physical, and technical safeguards
- **Privacy Rule**: Minimum necessary standard and authorization
- **Breach Notification**: Automated breach detection and reporting
- **Business Associate Agreements**: BAA management and compliance
- **Access Logging**: Comprehensive PHI access tracking

### Example Usage

```python
from datalineagepy.compliance import create_hipaa_compliance
from datalineagepy.compliance import PHIType, AccessPurpose

# Create HIPAA compliance instance
hipaa = create_hipaa_compliance()

# Process PHI
phi_id = hipaa.process_phi(
    patient_id="patient_123",
    phi_type=PHIType.MEDICAL_RECORDS,
    data_value={"diagnosis": "Hypertension", "treatment": "ACE inhibitor"},
    user_id="doctor_smith",
    purpose=AccessPurpose.TREATMENT
)

# Log PHI access
access_id = hipaa.phi_protection.log_access(
    patient_id="patient_123",
    user_id="nurse_jones",
    purpose=AccessPurpose.TREATMENT,
    data_accessed="vital_signs"
)

# Handle breach incident
incident_id = hipaa.breach_notification.report_incident(
    incident_type="unauthorized_access",
    description="Laptop theft containing PHI",
    affected_individuals=150,
    discovery_date=time.time()
)
```

### HIPAA Configuration

```python
hipaa_config = {
    "phi_retention_years": 6,
    "encryption_required": True,
    "access_logging_required": True,
    "breach_notification_days": 60,
    "minimum_necessary_standard": True,
    "business_associate_agreements": True,
    "risk_assessment_frequency_months": 12
}
```

## Audit System

### Features

- **Centralized Logging**: All compliance events in one system
- **Event Types**: Comprehensive event classification
- **Filtering and Querying**: Advanced audit log analysis
- **Compliance Reporting**: Automated compliance reports
- **Risk Assessment**: Periodic risk evaluations
- **Real-time Monitoring**: Live compliance monitoring

### Example Usage

```python
from datalineagepy.compliance import create_audit_system
from datalineagepy.compliance import AuditEventType, AuditSeverity, ComplianceStandard

# Create audit system
auditor = create_audit_system()

# Log audit event
event_id = auditor.audit_log.log_event(
    event_type=AuditEventType.DATA_ACCESS,
    severity=AuditSeverity.MEDIUM,
    user_id="data_analyst",
    resource="customer_database",
    action="query_personal_data",
    outcome="success",
    compliance_standards=[ComplianceStandard.GDPR]
)

# Generate compliance report
report_id = auditor.generate_compliance_report(
    standard=ComplianceStandard.GDPR,
    period_start=time.time() - (30 * 24 * 3600),  # Last 30 days
    period_end=time.time()
)

# Conduct risk assessment
assessment_id = auditor.conduct_risk_assessment(ComplianceStandard.HIPAA)
```

## Unified Framework

### Features

- **Multi-Standard Support**: Handle multiple compliance standards simultaneously
- **Centralized Management**: Single interface for all compliance operations
- **Cross-Standard Validation**: Ensure compliance across all applicable standards
- **Unified Reporting**: Comprehensive compliance dashboards
- **Policy Enforcement**: Automated compliance policy enforcement

### Example Usage

```python
from datalineagepy.compliance import create_compliance_framework

# Create framework with multiple standards
framework = create_compliance_framework(
    standards=["GDPR", "SOX", "HIPAA"],
    config={
        "gdpr": {"require_explicit_consent": True},
        "sox": {"require_change_approval": True},
        "hipaa": {"encryption_required": True}
    }
)

# Process data with multi-standard compliance
processing_id = framework.process_data(
    data_type="patient_financial_data",  # Triggers both SOX and HIPAA
    data_value={"patient_id": "P123", "billing_amount": 1500},
    subject_id="patient_123",
    processing_context={
        "user_id": "billing_clerk",
        "contains_phi": True,
        "financial_impact": True,
        "access_purpose": "payment"
    }
)

# Generate unified compliance dashboard
dashboard = framework.generate_compliance_dashboard()

# Run comprehensive assessment
assessment_results = framework.run_compliance_assessment()

# Calculate compliance scores
scores = framework.get_compliance_score()
```

## Configuration

### Framework Configuration

```python
framework_config = {
    "enabled_standards": ["GDPR", "SOX", "HIPAA"],
    "compliance_level": "enterprise",
    "audit_retention_days": 2555,
    "auto_remediation": False,
    "real_time_monitoring": True
}
```

### Audit Configuration

```python
audit_config = {
    "retention_days": 2555,  # 7 years
    "enable_real_time_monitoring": True,
    "alert_on_violations": True,
    "export_to_siem": False,
    "compliance_reporting": True
}
```

### Environment Variables

```bash
# Database configuration
COMPLIANCE_DB_URL=postgresql://user:pass@localhost/compliance
COMPLIANCE_DB_POOL_SIZE=10

# Encryption keys
COMPLIANCE_ENCRYPTION_KEY=your-encryption-key-here
COMPLIANCE_SIGNING_KEY=your-signing-key-here

# External integrations
COMPLIANCE_SIEM_ENDPOINT=https://siem.company.com/api
COMPLIANCE_NOTIFICATION_EMAIL=compliance@company.com

# Compliance settings
COMPLIANCE_ENVIRONMENT=production
COMPLIANCE_LOG_LEVEL=INFO
COMPLIANCE_AUDIT_RETENTION_DAYS=2555
```

## Best Practices

### 1. Data Classification

```python
# Always classify data appropriately
data_classification = {
    "personal_data": ["name", "email", "phone", "address"],
    "sensitive_personal_data": ["ssn", "passport", "medical_id"],
    "financial_data": ["account_number", "credit_card", "salary"],
    "health_data": ["diagnosis", "treatment", "medical_records"]
}
```

### 2. Consent Management

```python
# Record consent before processing
consent_id = gdpr.consent_manager.record_consent(
    subject_id=user_id,
    purpose=ProcessingPurpose.MARKETING,
    legal_basis=LegalBasis.CONSENT,
    consent_text="Explicit consent text",
    consent_method="web_form"
)

# Always check consent before processing
if gdpr.consent_manager.check_consent(user_id, ProcessingPurpose.MARKETING):
    # Process data
    pass
```

### 3. Audit Logging

```python
# Log all significant events
auditor.audit_log.log_event(
    event_type=AuditEventType.DATA_ACCESS,
    severity=AuditSeverity.MEDIUM,
    user_id=current_user.id,
    resource=f"database.{table_name}",
    action="SELECT",
    outcome="success",
    ip_address=request.remote_addr,
    user_agent=request.user_agent.string,
    details={"query": sanitized_query}
)
```

### 4. Error Handling

```python
try:
    framework.process_data(...)
except ComplianceViolationError as e:
    # Log violation
    logger.error(f"Compliance violation: {e}")
    # Notify compliance team
    send_compliance_alert(str(e))
    # Return appropriate error to user
    return {"error": "Data processing not permitted"}
```

### 5. Regular Assessments

```python
# Schedule regular compliance assessments
def run_monthly_assessment():
    results = framework.run_compliance_assessment()
    scores = framework.get_compliance_score()
    
    # Generate executive report
    generate_executive_report(results, scores)
    
    # Identify areas for improvement
    for standard, score in scores.items():
        if score < 80:
            create_improvement_plan(standard, score)
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```python
# Error: ModuleNotFoundError: No module named 'datalineagepy.compliance'
# Solution: Install compliance dependencies
pip install -r requirements-compliance.txt
```

#### 2. Configuration Errors

```python
# Error: Invalid compliance configuration
# Solution: Validate configuration
from datalineagepy.compliance import validate_compliance_config

is_valid = validate_compliance_config(config, "GDPR")
if not is_valid:
    print("Invalid GDPR configuration")
```

#### 3. Database Connection Issues

```python
# Error: Database connection failed
# Solution: Check database configuration
import os
db_url = os.getenv('COMPLIANCE_DB_URL')
if not db_url:
    print("COMPLIANCE_DB_URL environment variable not set")
```

#### 4. Audit Log Performance

```python
# Issue: Slow audit log queries
# Solution: Add database indexes and cleanup old events
auditor.audit_log.cleanup_old_events()
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for compliance
compliance_logger = logging.getLogger('datalineagepy.compliance')
compliance_logger.setLevel(logging.DEBUG)
```

## API Reference

### ComplianceFramework

```python
class ComplianceFramework:
    def __init__(self, standards: List[str], config: Dict[str, Any])
    def process_data(self, data_type: str, data_value: Any, subject_id: str, processing_context: Dict[str, Any]) -> str
    def access_data(self, data_id: str, user_id: str, access_context: Dict[str, Any]) -> Any
    def generate_compliance_dashboard(self) -> Dict[str, Any]
    def run_compliance_assessment(self) -> Dict[str, str]
    def get_compliance_score(self) -> Dict[str, float]
    def cleanup_expired_data(self) -> Dict[str, int]
    def add_violation_handler(self, handler: callable)
```

### ComplianceAuditor

```python
class ComplianceAuditor:
    def __init__(self, audit_log: AuditLog)
    def generate_compliance_report(self, standard: ComplianceStandard, period_start: float, period_end: float) -> str
    def conduct_risk_assessment(self, standard: ComplianceStandard) -> str
    def get_audit_summary(self) -> Dict[str, Any]
```

### AuditLog

```python
class AuditLog:
    def __init__(self, retention_days: int = 2555)
    def log_event(self, event_type: AuditEventType, severity: AuditSeverity, user_id: str, resource: str, action: str, outcome: str, **kwargs) -> str
    def query_events(self, filter_criteria: AuditFilter) -> List[AuditEvent]
    def add_event_handler(self, handler: callable)
    def cleanup_old_events(self) -> int
```

### Factory Functions

```python
def create_compliance_framework(standards: list = None, config: dict = None) -> ComplianceFramework
def create_audit_system(config: dict = None) -> ComplianceAuditor
def create_gdpr_compliance(config: dict = None) -> GDPRCompliance
def create_sox_compliance(config: dict = None) -> SOXCompliance
def create_hipaa_compliance(config: dict = None) -> HIPAACompliance
```

## Integration Examples

### Flask Web Application

```python
from flask import Flask, request, jsonify
from datalineagepy.compliance import create_compliance_framework

app = Flask(__name__)
compliance = create_compliance_framework()

@app.route('/api/data', methods=['POST'])
def process_data():
    try:
        data = request.json
        processing_id = compliance.process_data(
            data_type=data['type'],
            data_value=data['value'],
            subject_id=data['subject_id'],
            processing_context={
                'user_id': request.headers.get('User-ID'),
                'ip_address': request.remote_addr,
                'user_agent': request.user_agent.string
            }
        )
        return jsonify({'processing_id': processing_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
```

### Celery Background Tasks

```python
from celery import Celery
from datalineagepy.compliance import create_compliance_framework

celery = Celery('compliance_tasks')
compliance = create_compliance_framework()

@celery.task
def run_compliance_assessment():
    results = compliance.run_compliance_assessment()
    # Send results to management dashboard
    return results

@celery.task
def cleanup_expired_data():
    stats = compliance.cleanup_expired_data()
    # Log cleanup statistics
    return stats
```

### Database Integration

```python
from sqlalchemy import event
from datalineagepy.compliance import create_audit_system

auditor = create_audit_system()

@event.listens_for(User, 'after_insert')
def log_user_creation(mapper, connection, target):
    auditor.audit_log.log_event(
        event_type=AuditEventType.DATA_MODIFICATION,
        severity=AuditSeverity.MEDIUM,
        user_id='system',
        resource='users_table',
        action='INSERT',
        outcome='success',
        details={'user_id': target.id}
    )
```

## Deployment

### Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-compliance.txt .
RUN pip install -r requirements-compliance.txt

COPY . .

ENV COMPLIANCE_ENVIRONMENT=production
ENV COMPLIANCE_LOG_LEVEL=INFO

CMD ["python", "-m", "datalineagepy.compliance.server"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: compliance-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: compliance-service
  template:
    metadata:
      labels:
        app: compliance-service
    spec:
      containers:
      - name: compliance
        image: datalineagepy/compliance:latest
        env:
        - name: COMPLIANCE_DB_URL
          valueFrom:
            secretKeyRef:
              name: compliance-secrets
              key: db-url
        - name: COMPLIANCE_ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: compliance-secrets
              key: encryption-key
```

## Support and Resources

- **Documentation**: [https://docs.datalineagepy.com/compliance](https://docs.datalineagepy.com/compliance)
- **GitHub Issues**: [https://github.com/datalineagepy/datalineagepy/issues](https://github.com/datalineagepy/datalineagepy/issues)
- **Community Forum**: [https://community.datalineagepy.com](https://community.datalineagepy.com)
- **Enterprise Support**: [enterprise@datalineagepy.com](mailto:enterprise@datalineagepy.com)

## License

The DataLineagePy Compliance Framework is licensed under the Apache License 2.0. See [LICENSE](../LICENSE) for details.

---

*This guide covers the comprehensive compliance capabilities of DataLineagePy. For specific regulatory requirements, consult with your legal and compliance teams.*
