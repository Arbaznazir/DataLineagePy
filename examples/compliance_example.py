"""
DataLineagePy Compliance Framework Example
Demonstrates comprehensive compliance features for GDPR, SOX, and HIPAA.
"""

import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main compliance framework demonstration."""
    print("=" * 80)
    print("DataLineagePy Compliance Framework Demo")
    print("=" * 80)
    
    try:
        # Import compliance components
        from datalineagepy.compliance import (
            create_compliance_framework,
            create_audit_system,
            AuditEventType,
            AuditSeverity,
            ComplianceStandard,
            LegalBasis,
            ProcessingPurpose,
            PHIType,
            AccessPurpose,
            FinancialDataType
        )
        
        print("\n1. Creating Unified Compliance Framework")
        print("-" * 50)
        
        # Create compliance framework with all standards
        framework = create_compliance_framework(
            standards=["GDPR", "SOX", "HIPAA"],
            config={
                "gdpr": {
                    "consent_retention_days": 1095,
                    "breach_notification_hours": 72,
                    "require_explicit_consent": True
                },
                "sox": {
                    "audit_retention_years": 7,
                    "require_change_approval": True,
                    "segregation_of_duties": True
                },
                "hipaa": {
                    "phi_retention_years": 6,
                    "encryption_required": True,
                    "minimum_necessary_standard": True
                }
            }
        )
        
        print(f"✓ Compliance framework initialized with standards: {framework.standards}")
        
        print("\n2. Demonstrating GDPR Compliance")
        print("-" * 50)
        
        # Process personal data with GDPR compliance
        gdpr_processing_id = framework.process_data(
            data_type="personal_customer_data",
            data_value={"name": "John Doe", "email": "john@example.com"},
            subject_id="customer_123",
            processing_context={
                "legal_basis": "consent",
                "purpose": "marketing",
                "user_id": "data_processor_1",
                "contains_pii": True
            }
        )
        
        print(f"✓ GDPR data processing completed: {gdpr_processing_id}")
        
        # Access personal data
        try:
            data = framework.access_data(
                data_id="customer_123_profile",
                user_id="marketing_user",
                access_context={
                    "data_type": "personal_customer_data",
                    "purpose": "marketing",
                    "subject_id": "customer_123",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0..."
                }
            )
            print(f"✓ GDPR data access authorized: {data}")
        except PermissionError as e:
            print(f"✗ GDPR data access denied: {e}")
        
        print("\n3. Demonstrating SOX Compliance")
        print("-" * 50)
        
        # Process financial data with SOX compliance
        sox_processing_id = framework.process_data(
            data_type="financial_revenue_data",
            data_value={"revenue": 1000000, "quarter": "Q1_2024"},
            subject_id="company_financials",
            processing_context={
                "financial_type": "revenue",
                "user_id": "financial_analyst_1",
                "financial_impact": True,
                "approval_id": "FIN_APPROVAL_2024_001"
            }
        )
        
        print(f"✓ SOX financial data processing completed: {sox_processing_id}")
        
        # Access financial data
        try:
            financial_data = framework.access_data(
                data_id="revenue_q1_2024",
                user_id="cfo_user",
                access_context={
                    "data_type": "financial_revenue_data",
                    "financial_impact": True,
                    "purpose": "financial_reporting"
                }
            )
            print(f"✓ SOX financial data access authorized: {financial_data}")
        except PermissionError as e:
            print(f"✗ SOX financial data access denied: {e}")
        
        print("\n4. Demonstrating HIPAA Compliance")
        print("-" * 50)
        
        # Process health data with HIPAA compliance
        hipaa_processing_id = framework.process_data(
            data_type="health_medical_records",
            data_value={"patient_id": "P123", "diagnosis": "Hypertension"},
            subject_id="patient_123",
            processing_context={
                "phi_type": "medical_records",
                "access_purpose": "treatment",
                "user_id": "doctor_smith",
                "contains_phi": True
            }
        )
        
        print(f"✓ HIPAA PHI processing completed: {hipaa_processing_id}")
        
        # Access PHI data
        try:
            phi_data = framework.access_data(
                data_id="patient_123_records",
                user_id="nurse_jones",
                access_context={
                    "data_type": "health_medical_records",
                    "access_purpose": "treatment",
                    "subject_id": "patient_123",
                    "contains_phi": True
                }
            )
            print(f"✓ HIPAA PHI access authorized: {phi_data}")
        except PermissionError as e:
            print(f"✗ HIPAA PHI access denied: {e}")
        
        print("\n5. Audit System Demonstration")
        print("-" * 50)
        
        # Create standalone audit system
        audit_system = create_audit_system()
        
        # Log various audit events
        events = [
            {
                "event_type": AuditEventType.USER_LOGIN,
                "severity": AuditSeverity.LOW,
                "user_id": "admin_user",
                "resource": "compliance_system",
                "action": "login",
                "outcome": "success"
            },
            {
                "event_type": AuditEventType.DATA_ACCESS,
                "severity": AuditSeverity.MEDIUM,
                "user_id": "data_analyst",
                "resource": "customer_database",
                "action": "query_personal_data",
                "outcome": "success",
                "compliance_standards": [ComplianceStandard.GDPR]
            },
            {
                "event_type": AuditEventType.COMPLIANCE_VIOLATION,
                "severity": AuditSeverity.HIGH,
                "user_id": "temp_user",
                "resource": "financial_reports",
                "action": "unauthorized_access",
                "outcome": "blocked",
                "compliance_standards": [ComplianceStandard.SOX]
            }
        ]
        
        for event in events:
            event_id = audit_system.audit_log.log_event(**event)
            print(f"✓ Logged audit event: {event_id} ({event['event_type'].value})")
        
        print("\n6. Compliance Assessment and Reporting")
        print("-" * 50)
        
        # Run comprehensive compliance assessment
        assessment_results = framework.run_compliance_assessment()
        print("✓ Compliance assessment completed:")
        for standard, report_id in assessment_results.items():
            print(f"  - {standard}: Report {report_id}")
        
        # Generate compliance dashboard
        dashboard_data = framework.generate_compliance_dashboard()
        print("\n✓ Compliance Dashboard Data:")
        print(f"  - Enabled Standards: {dashboard_data['compliance_overview']['enabled_standards']}")
        print(f"  - Overall Status: {dashboard_data['compliance_overview']['overall_status']}")
        
        # Display standard-specific status
        for standard, status in dashboard_data['standards'].items():
            print(f"  - {standard} Status: {status}")
        
        # Display audit summary
        audit_summary = dashboard_data['audit']
        print(f"  - Total Audit Events: {audit_summary['total_events']}")
        print(f"  - Recent Events (24h): {audit_summary['recent_events_24h']}")
        print(f"  - Critical Events (24h): {audit_summary['critical_events_24h']}")
        
        print("\n7. Compliance Scores")
        print("-" * 50)
        
        # Calculate compliance scores
        scores = framework.get_compliance_score()
        print("✓ Compliance Scores:")
        for standard, score in scores.items():
            status = "✓" if score >= 80 else "⚠" if score >= 60 else "✗"
            print(f"  {status} {standard}: {score:.1f}/100")
        
        print("\n8. Risk Assessment")
        print("-" * 50)
        
        # Conduct risk assessments
        for standard_name in framework.standards:
            try:
                standard = ComplianceStandard(standard_name.lower())
                assessment_id = framework.auditor.conduct_risk_assessment(standard)
                
                # Get assessment details
                with framework.auditor.lock:
                    assessment = framework.auditor.risk_assessments.get(assessment_id)
                    if assessment:
                        print(f"✓ {standard_name} Risk Assessment: {assessment.overall_risk.upper()} risk")
                        print(f"  - Risk Factors: {len(assessment.risk_factors)}")
                        print(f"  - Mitigation Strategies: {len(assessment.mitigation_strategies)}")
            except Exception as e:
                print(f"✗ Error in {standard_name} risk assessment: {e}")
        
        print("\n9. Data Cleanup and Maintenance")
        print("-" * 50)
        
        # Cleanup expired data
        cleanup_stats = framework.cleanup_expired_data()
        print("✓ Data cleanup completed:")
        for component, count in cleanup_stats.items():
            print(f"  - {component}: {count} items cleaned")
        
        print("\n10. Violation Handling Demo")
        print("-" * 50)
        
        # Add violation handler
        def violation_handler(violation_type, message, context):
            print(f"🚨 COMPLIANCE VIOLATION DETECTED:")
            print(f"   Type: {violation_type}")
            print(f"   Message: {message}")
            print(f"   Context: {context}")
        
        framework.add_violation_handler(violation_handler)
        
        # Simulate a violation by trying to process data without proper context
        try:
            framework.process_data(
                data_type="personal_sensitive_data",
                data_value={"ssn": "123-45-6789"},
                subject_id="user_456",
                processing_context={
                    "user_id": "unauthorized_user"
                    # Missing required compliance context
                }
            )
        except Exception as e:
            print(f"✓ Violation properly caught and handled: {e}")
        
        print("\n" + "=" * 80)
        print("Compliance Framework Demo Completed Successfully!")
        print("=" * 80)
        
        # Final summary
        print(f"\nSUMMARY:")
        print(f"- Compliance Standards: {len(framework.standards)}")
        print(f"- Total Audit Events: {len(framework.audit_log.events)}")
        print(f"- Compliance Reports: {len(framework.auditor.compliance_reports)}")
        print(f"- Risk Assessments: {len(framework.auditor.risk_assessments)}")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please ensure the compliance module is properly installed.")
    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        print(f"❌ Demo failed: {e}")


def demonstrate_individual_standards():
    """Demonstrate individual compliance standards."""
    print("\n" + "=" * 80)
    print("Individual Compliance Standards Demo")
    print("=" * 80)
    
    try:
        from datalineagepy.compliance import (
            create_gdpr_compliance,
            create_sox_compliance,
            create_hipaa_compliance,
            LegalBasis,
            ProcessingPurpose,
            ControlType,
            PHIType,
            AccessPurpose
        )
        
        print("\n1. GDPR Standalone Demo")
        print("-" * 30)
        
        gdpr = create_gdpr_compliance()
        
        # Record consent
        consent_id = gdpr.consent_manager.record_consent(
            subject_id="user_789",
            purpose=ProcessingPurpose.MARKETING,
            legal_basis=LegalBasis.CONSENT
        )
        print(f"✓ GDPR consent recorded: {consent_id}")
        
        # Process personal data
        processing_id = gdpr.process_personal_data(
            subject_id="user_789",
            data_type="email_address",
            data_value="user789@example.com",
            legal_basis=LegalBasis.CONSENT,
            purpose=ProcessingPurpose.MARKETING
        )
        print(f"✓ GDPR personal data processed: {processing_id}")
        
        print("\n2. SOX Standalone Demo")
        print("-" * 30)
        
        sox = create_sox_compliance()
        
        # Add internal control
        control_id = sox.internal_controls.add_control(
            control_type=ControlType.PREVENTIVE,
            description="Segregation of duties for financial reporting",
            owner="CFO",
            frequency="continuous"
        )
        print(f"✓ SOX internal control added: {control_id}")
        
        print("\n3. HIPAA Standalone Demo")
        print("-" * 30)
        
        hipaa = create_hipaa_compliance()
        
        # Process PHI
        phi_id = hipaa.process_phi(
            patient_id="patient_456",
            phi_type=PHIType.MEDICAL_RECORDS,
            data_value={"diagnosis": "Diabetes", "treatment": "Insulin"},
            user_id="doctor_brown",
            purpose=AccessPurpose.TREATMENT
        )
        print(f"✓ HIPAA PHI processed: {phi_id}")
        
        print("\n✓ Individual standards demo completed!")
        
    except Exception as e:
        logger.error(f"Individual standards demo error: {e}", exc_info=True)
        print(f"❌ Individual standards demo failed: {e}")


if __name__ == "__main__":
    # Run main compliance framework demo
    main()
    
    # Run individual standards demo
    demonstrate_individual_standards()
    
    print(f"\n🎉 All compliance demos completed at {datetime.now()}")
