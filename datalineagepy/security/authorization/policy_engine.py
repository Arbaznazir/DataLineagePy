"""
Policy Engine for Complex Access Rules
Advanced authorization engine supporting attribute-based access control (ABAC) and policy-based decisions.
"""

import json
import re
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
import ipaddress
from abc import ABC, abstractmethod


class PolicyEffect(Enum):
    """Policy decision effects."""
    ALLOW = "allow"
    DENY = "deny"


class ComparisonOperator(Enum):
    """Comparison operators for conditions."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "ge"
    LESS_THAN = "lt"
    LESS_EQUAL = "le"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCH = "regex"


@dataclass
class Condition:
    """Represents a single condition in a policy."""
    attribute: str  # e.g., "user.department", "resource.classification", "context.time"
    operator: ComparisonOperator
    value: Any
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context."""
        actual_value = self._get_nested_value(context, self.attribute)
        
        if actual_value is None:
            return False
        
        return self._compare_values(actual_value, self.operator, self.value)
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _compare_values(self, actual: Any, operator: ComparisonOperator, expected: Any) -> bool:
        """Compare values using the specified operator."""
        try:
            if operator == ComparisonOperator.EQUALS:
                return actual == expected
            elif operator == ComparisonOperator.NOT_EQUALS:
                return actual != expected
            elif operator == ComparisonOperator.GREATER_THAN:
                return actual > expected
            elif operator == ComparisonOperator.GREATER_EQUAL:
                return actual >= expected
            elif operator == ComparisonOperator.LESS_THAN:
                return actual < expected
            elif operator == ComparisonOperator.LESS_EQUAL:
                return actual <= expected
            elif operator == ComparisonOperator.IN:
                return actual in expected if isinstance(expected, (list, tuple, set)) else False
            elif operator == ComparisonOperator.NOT_IN:
                return actual not in expected if isinstance(expected, (list, tuple, set)) else True
            elif operator == ComparisonOperator.CONTAINS:
                return str(expected) in str(actual)
            elif operator == ComparisonOperator.STARTS_WITH:
                return str(actual).startswith(str(expected))
            elif operator == ComparisonOperator.ENDS_WITH:
                return str(actual).endswith(str(expected))
            elif operator == ComparisonOperator.REGEX_MATCH:
                return bool(re.match(str(expected), str(actual)))
            
            return False
        except Exception:
            return False


@dataclass
class Policy:
    """Represents an access control policy."""
    id: str
    name: str
    description: str
    effect: PolicyEffect
    conditions: List[Condition] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)  # Resource patterns
    actions: List[str] = field(default_factory=list)  # Action patterns
    priority: int = 0  # Higher priority policies are evaluated first
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def matches_request(self, resource: str, action: str) -> bool:
        """Check if policy applies to the given resource and action."""
        resource_match = not self.resources or any(
            self._pattern_match(resource, pattern) for pattern in self.resources
        )
        
        action_match = not self.actions or any(
            self._pattern_match(action, pattern) for pattern in self.actions
        )
        
        return resource_match and action_match
    
    def _pattern_match(self, value: str, pattern: str) -> bool:
        """Match value against pattern (supports wildcards)."""
        if pattern == "*":
            return True
        
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex_pattern}$", value))
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate all conditions in the policy."""
        if not self.conditions:
            return True  # No conditions means always match
        
        # All conditions must be true (AND logic)
        return all(condition.evaluate(context) for condition in self.conditions)


class PolicyEngine:
    """
    Advanced policy engine for attribute-based access control.
    
    Features:
    - Attribute-based access control (ABAC)
    - Complex policy conditions
    - Policy priority and conflict resolution
    - Time-based access control
    - Location-based access control
    - Data classification policies
    """
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.policy_sets: Dict[str, List[str]] = {}  # Named groups of policies
        self.custom_functions: Dict[str, Callable] = {}
        
        # Initialize built-in policies
        self._initialize_builtin_policies()
    
    def _initialize_builtin_policies(self):
        """Initialize common built-in policies."""
        
        # Business hours access policy
        business_hours_policy = Policy(
            id="business_hours_access",
            name="Business Hours Access",
            description="Allow access only during business hours (9 AM - 6 PM)",
            effect=PolicyEffect.ALLOW,
            conditions=[
                Condition("context.time.hour", ComparisonOperator.GREATER_EQUAL, 9),
                Condition("context.time.hour", ComparisonOperator.LESS_THAN, 18),
                Condition("context.time.weekday", ComparisonOperator.LESS_THAN, 5)  # Mon-Fri
            ],
            priority=10
        )
        self.add_policy(business_hours_policy)
        
        # Admin override policy
        admin_override_policy = Policy(
            id="admin_override",
            name="Administrator Override",
            description="Administrators can access everything",
            effect=PolicyEffect.ALLOW,
            conditions=[
                Condition("user.roles", ComparisonOperator.CONTAINS, "admin")
            ],
            priority=100  # High priority
        )
        self.add_policy(admin_override_policy)
        
        # Sensitive data policy
        sensitive_data_policy = Policy(
            id="sensitive_data_protection",
            name="Sensitive Data Protection",
            description="Restrict access to sensitive data based on clearance",
            effect=PolicyEffect.DENY,
            resources=["*sensitive*", "*confidential*", "*pii*"],
            conditions=[
                Condition("user.clearance_level", ComparisonOperator.NOT_IN, 
                         ["high", "top_secret"])
            ],
            priority=90
        )
        self.add_policy(sensitive_data_policy)
        
        # IP whitelist policy
        ip_whitelist_policy = Policy(
            id="ip_whitelist",
            name="IP Address Whitelist",
            description="Allow access only from approved IP ranges",
            effect=PolicyEffect.DENY,
            conditions=[
                Condition("context.ip_address", ComparisonOperator.REGEX_MATCH, 
                         r"^(?!192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)")
            ],
            priority=80
        )
        # Note: This policy would need custom IP range checking
    
    def add_policy(self, policy: Policy):
        """Add a policy to the engine."""
        self.policies[policy.id] = policy
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy from the engine."""
        if policy_id in self.policies:
            del self.policies[policy_id]
            return True
        return False
    
    def create_policy_from_dict(self, policy_data: Dict[str, Any]) -> Policy:
        """Create policy from dictionary configuration."""
        conditions = []
        for cond_data in policy_data.get("conditions", []):
            condition = Condition(
                attribute=cond_data["attribute"],
                operator=ComparisonOperator(cond_data["operator"]),
                value=cond_data["value"]
            )
            conditions.append(condition)
        
        policy = Policy(
            id=policy_data["id"],
            name=policy_data["name"],
            description=policy_data.get("description", ""),
            effect=PolicyEffect(policy_data["effect"]),
            conditions=conditions,
            resources=policy_data.get("resources", []),
            actions=policy_data.get("actions", []),
            priority=policy_data.get("priority", 0),
            is_active=policy_data.get("is_active", True)
        )
        
        return policy
    
    def evaluate_access(self, user: Dict[str, Any], resource: str, action: str,
                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate access request against all applicable policies.
        
        Args:
            user: User information
            resource: Resource being accessed
            action: Action being performed
            context: Additional context (time, location, etc.)
            
        Returns:
            Decision with effect, reason, and applicable policies
        """
        context = context or {}
        
        # Build evaluation context
        eval_context = {
            "user": user,
            "resource": {"id": resource, "type": self._get_resource_type(resource)},
            "action": action,
            "context": {
                **context,
                "time": {
                    "hour": datetime.now().hour,
                    "weekday": datetime.now().weekday(),
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        # Find applicable policies
        applicable_policies = []
        for policy in self.policies.values():
            if policy.is_active and policy.matches_request(resource, action):
                applicable_policies.append(policy)
        
        # Sort by priority (highest first)
        applicable_policies.sort(key=lambda p: p.priority, reverse=True)
        
        # Evaluate policies
        decision_log = []
        final_effect = PolicyEffect.DENY  # Default deny
        
        for policy in applicable_policies:
            if policy.evaluate(eval_context):
                decision_log.append({
                    "policy_id": policy.id,
                    "policy_name": policy.name,
                    "effect": policy.effect.value,
                    "matched": True
                })
                
                # First matching policy determines the effect
                if policy.effect == PolicyEffect.ALLOW:
                    final_effect = PolicyEffect.ALLOW
                    break  # Allow takes precedence
                elif policy.effect == PolicyEffect.DENY:
                    final_effect = PolicyEffect.DENY
                    break  # Explicit deny
            else:
                decision_log.append({
                    "policy_id": policy.id,
                    "policy_name": policy.name,
                    "effect": policy.effect.value,
                    "matched": False
                })
        
        return {
            "effect": final_effect.value,
            "allowed": final_effect == PolicyEffect.ALLOW,
            "policies_evaluated": len(applicable_policies),
            "decision_log": decision_log,
            "context": eval_context
        }
    
    def _get_resource_type(self, resource: str) -> str:
        """Determine resource type from resource identifier."""
        if "lineage" in resource.lower():
            return "lineage_graph"
        elif "pipeline" in resource.lower():
            return "pipeline"
        elif "datasource" in resource.lower():
            return "data_source"
        elif "report" in resource.lower():
            return "report"
        else:
            return "unknown"
    
    def create_policy_set(self, name: str, policy_ids: List[str]):
        """Create a named set of policies."""
        self.policy_sets[name] = policy_ids
    
    def evaluate_policy_set(self, policy_set_name: str, user: Dict[str, Any], 
                           resource: str, action: str,
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evaluate access using only policies in a specific set."""
        if policy_set_name not in self.policy_sets:
            return {"effect": "deny", "allowed": False, "error": "Policy set not found"}
        
        # Temporarily filter policies
        original_policies = self.policies.copy()
        policy_ids = self.policy_sets[policy_set_name]
        self.policies = {pid: self.policies[pid] for pid in policy_ids if pid in self.policies}
        
        try:
            result = self.evaluate_access(user, resource, action, context)
            return result
        finally:
            # Restore original policies
            self.policies = original_policies
    
    def register_custom_function(self, name: str, func: Callable):
        """Register custom function for use in policy conditions."""
        self.custom_functions[name] = func
    
    def test_policy(self, policy_id: str, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test a policy against multiple test cases."""
        if policy_id not in self.policies:
            return [{"error": "Policy not found"}]
        
        policy = self.policies[policy_id]
        results = []
        
        for i, test_case in enumerate(test_cases):
            user = test_case.get("user", {})
            resource = test_case.get("resource", "")
            action = test_case.get("action", "")
            context = test_case.get("context", {})
            expected = test_case.get("expected")
            
            result = self.evaluate_access(user, resource, action, context)
            
            test_result = {
                "test_case": i + 1,
                "input": test_case,
                "result": result,
                "passed": result["allowed"] == expected if expected is not None else None
            }
            
            results.append(test_result)
        
        return results
    
    def export_policies(self) -> Dict[str, Any]:
        """Export all policies to dictionary format."""
        exported = {}
        
        for policy_id, policy in self.policies.items():
            exported[policy_id] = {
                "name": policy.name,
                "description": policy.description,
                "effect": policy.effect.value,
                "conditions": [
                    {
                        "attribute": cond.attribute,
                        "operator": cond.operator.value,
                        "value": cond.value
                    }
                    for cond in policy.conditions
                ],
                "resources": policy.resources,
                "actions": policy.actions,
                "priority": policy.priority,
                "is_active": policy.is_active
            }
        
        return exported
    
    def import_policies(self, policies_data: Dict[str, Any]):
        """Import policies from dictionary format."""
        for policy_id, policy_data in policies_data.items():
            policy_data["id"] = policy_id
            policy = self.create_policy_from_dict(policy_data)
            self.add_policy(policy)
    
    def get_policy_statistics(self) -> Dict[str, Any]:
        """Get statistics about policies in the engine."""
        total_policies = len(self.policies)
        active_policies = sum(1 for p in self.policies.values() if p.is_active)
        allow_policies = sum(1 for p in self.policies.values() if p.effect == PolicyEffect.ALLOW)
        deny_policies = sum(1 for p in self.policies.values() if p.effect == PolicyEffect.DENY)
        
        return {
            "total_policies": total_policies,
            "active_policies": active_policies,
            "inactive_policies": total_policies - active_policies,
            "allow_policies": allow_policies,
            "deny_policies": deny_policies,
            "policy_sets": len(self.policy_sets),
            "custom_functions": len(self.custom_functions)
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize policy engine
    engine = PolicyEngine()
    
    # Create a custom policy
    data_scientist_policy = Policy(
        id="data_scientist_access",
        name="Data Scientist Access",
        description="Data scientists can access non-sensitive lineage data",
        effect=PolicyEffect.ALLOW,
        resources=["lineage:*"],
        actions=["read", "export"],
        conditions=[
            Condition("user.department", ComparisonOperator.EQUALS, "data_science"),
            Condition("resource.classification", ComparisonOperator.NOT_IN, ["sensitive", "confidential"])
        ],
        priority=50
    )
    engine.add_policy(data_scientist_policy)
    
    # Test access evaluation
    user = {
        "id": "user123",
        "email": "scientist@company.com",
        "department": "data_science",
        "roles": ["data_scientist"],
        "clearance_level": "standard"
    }
    
    # Test cases
    test_cases = [
        {
            "resource": "lineage:customer_data",
            "action": "read",
            "expected": True
        },
        {
            "resource": "lineage:sensitive_pii",
            "action": "read",
            "expected": False
        }
    ]
    
    for test_case in test_cases:
        result = engine.evaluate_access(
            user, 
            test_case["resource"], 
            test_case["action"],
            {"classification": "public" if "sensitive" not in test_case["resource"] else "sensitive"}
        )
        
        print(f"Resource: {test_case['resource']}")
        print(f"Action: {test_case['action']}")
        print(f"Allowed: {result['allowed']}")
        print(f"Expected: {test_case['expected']}")
        print(f"Match: {result['allowed'] == test_case['expected']}")
        print("---")
    
    # Print statistics
    stats = engine.get_policy_statistics()
    print("Policy Engine Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
