"""
Example demonstrating the core integration components for DataLineagePy.
This example shows how to use the event handler, metadata extractor, and data flow mapper.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from datalineagepy.integrations.core import (
        EventHandler, EventType, EventPriority, IntegrationEvent,
        MetadataExtractor, MetadataSchema, MetadataType, ColumnMetadata, DataType,
        DataFlowMapper, DataFlow, FlowType, DataEntity, FlowDirection,
        create_event_handler, create_metadata_extractor, create_data_flow_mapper
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Running in demo mode with mock implementations...")
    
    # Mock implementations for demo
    class MockEventHandler:
        def __init__(self):
            self.events = []
        
        async def emit(self, event_type, source, **kwargs):
            event = {
                'event_type': event_type,
                'source': source,
                'timestamp': datetime.utcnow(),
                **kwargs
            }
            self.events.append(event)
            print(f"Event emitted: {event_type} from {source}")
        
        def get_events(self, limit=None):
            return self.events[-limit:] if limit else self.events
    
    class MockMetadataExtractor:
        def __init__(self):
            self.metadata_cache = {}
        
        async def extract_all_metadata(self):
            return {
                'mock_system': [
                    {
                        'entity_id': 'table1',
                        'name': 'users',
                        'entity_type': 'table',
                        'system': 'mock_system'
                    }
                ]
            }
        
        async def get_metadata_summary(self):
            return {
                'total_entities': 1,
                'systems': {'mock_system': 1},
                'entity_types': {'table': 1}
            }
    
    class MockDataFlowMapper:
        def __init__(self):
            self.flow_cache = {}
        
        async def discover_all_flows(self):
            return {
                'mock_system': [
                    {
                        'flow_id': 'flow1',
                        'source_entity': 'table1',
                        'target_entity': 'table2',
                        'flow_type': 'transform'
                    }
                ]
            }
        
        async def get_flow_summary(self):
            return {
                'total_flows': 1,
                'total_entities': 2,
                'systems': {'mock_system': 1},
                'flow_types': {'transform': 1}
            }
    
    # Use mock implementations
    EventHandler = MockEventHandler
    MetadataExtractor = MockMetadataExtractor
    DataFlowMapper = MockDataFlowMapper
    
    def create_event_handler():
        return MockEventHandler()
    
    def create_metadata_extractor():
        return MockMetadataExtractor()
    
    def create_data_flow_mapper():
        return MockDataFlowMapper()


async def demonstrate_event_handling():
    """Demonstrate event handling capabilities."""
    print("\n" + "="*60)
    print("DEMONSTRATING EVENT HANDLING")
    print("="*60)
    
    # Create event handler
    event_handler = create_event_handler()
    
    # Add event listeners
    async def connection_listener(event):
        print(f"Connection event: {event.event_type.value if hasattr(event, 'event_type') else event.get('event_type')}")
    
    async def error_listener(event):
        print(f"Error event: {event.error if hasattr(event, 'error') else event.get('error', 'Unknown error')}")
    
    if hasattr(event_handler, 'add_listener'):
        event_handler.add_listener(EventType.CONNECTION_ESTABLISHED, connection_listener)
        event_handler.add_global_listener(error_listener)
    
    # Emit various events
    events_to_emit = [
        (EventType.CONNECTION_ESTABLISHED if 'EventType' in globals() else 'connection_established', 
         "snowflake_connector", {"connector_name": "snowflake", "priority": "normal"}),
        (EventType.AUTHENTICATION_SUCCESS if 'EventType' in globals() else 'authentication_success', 
         "databricks_connector", {"connector_name": "databricks", "priority": "normal"}),
        (EventType.METADATA_EXTRACTED if 'EventType' in globals() else 'metadata_extracted', 
         "bigquery_connector", {"connector_name": "bigquery", "entities_count": 150}),
        (EventType.ERROR_OCCURRED if 'EventType' in globals() else 'error_occurred', 
         "redshift_connector", {"connector_name": "redshift", "error": "Connection timeout", "priority": "high"}),
    ]
    
    for event_type, source, data in events_to_emit:
        await event_handler.emit(event_type, source, **data)
        await asyncio.sleep(0.1)  # Small delay for demonstration
    
    # Get event statistics
    recent_events = event_handler.get_events(limit=5)
    print(f"\nRecent events count: {len(recent_events)}")
    
    if hasattr(event_handler, 'get_stats'):
        stats = event_handler.get_stats()
        print(f"Event handler stats: {stats}")
    
    print("✓ Event handling demonstration completed")


async def demonstrate_metadata_extraction():
    """Demonstrate metadata extraction capabilities."""
    print("\n" + "="*60)
    print("DEMONSTRATING METADATA EXTRACTION")
    print("="*60)
    
    # Create metadata extractor
    metadata_extractor = create_metadata_extractor()
    
    # Extract metadata from all systems
    print("Extracting metadata from all systems...")
    metadata_results = await metadata_extractor.extract_all_metadata()
    
    for system, metadata_list in metadata_results.items():
        print(f"\nSystem: {system}")
        print(f"Entities extracted: {len(metadata_list)}")
        
        for metadata in metadata_list[:3]:  # Show first 3 entities
            if isinstance(metadata, dict):
                print(f"  - {metadata.get('name', 'Unknown')} ({metadata.get('entity_type', 'Unknown')})")
            else:
                print(f"  - {metadata.name} ({metadata.entity_type.value})")
    
    # Get metadata summary
    summary = await metadata_extractor.get_metadata_summary()
    print(f"\nMetadata Summary:")
    print(f"  Total entities: {summary.get('total_entities', 0)}")
    print(f"  Systems: {list(summary.get('systems', {}).keys())}")
    print(f"  Entity types: {list(summary.get('entity_types', {}).keys())}")
    
    if hasattr(metadata_extractor, 'get_stats'):
        stats = metadata_extractor.get_stats()
        print(f"  Extraction stats: {stats}")
    
    print("✓ Metadata extraction demonstration completed")


async def demonstrate_data_flow_mapping():
    """Demonstrate data flow mapping capabilities."""
    print("\n" + "="*60)
    print("DEMONSTRATING DATA FLOW MAPPING")
    print("="*60)
    
    # Create data flow mapper
    flow_mapper = create_data_flow_mapper()
    
    # Discover flows from all systems
    print("Discovering data flows from all systems...")
    flow_results = await flow_mapper.discover_all_flows()
    
    for system, flows in flow_results.items():
        print(f"\nSystem: {system}")
        print(f"Flows discovered: {len(flows)}")
        
        for flow in flows[:3]:  # Show first 3 flows
            if isinstance(flow, dict):
                print(f"  - {flow.get('source_entity', 'Unknown')} → {flow.get('target_entity', 'Unknown')} ({flow.get('flow_type', 'Unknown')})")
            else:
                print(f"  - {flow.source_entity.name} → {flow.target_entity.name} ({flow.flow_type.value})")
    
    # Get flow summary
    summary = await flow_mapper.get_flow_summary()
    print(f"\nFlow Summary:")
    print(f"  Total flows: {summary.get('total_flows', 0)}")
    print(f"  Total entities: {summary.get('total_entities', 0)}")
    print(f"  Systems: {list(summary.get('systems', {}).keys())}")
    print(f"  Flow types: {list(summary.get('flow_types', {}).keys())}")
    
    if hasattr(flow_mapper, 'get_stats'):
        stats = flow_mapper.get_stats()
        print(f"  Mapping stats: {stats}")
    
    print("✓ Data flow mapping demonstration completed")


async def demonstrate_integrated_workflow():
    """Demonstrate integrated workflow using all components."""
    print("\n" + "="*60)
    print("DEMONSTRATING INTEGRATED WORKFLOW")
    print("="*60)
    
    # Create all components
    event_handler = create_event_handler()
    metadata_extractor = create_metadata_extractor()
    flow_mapper = create_data_flow_mapper()
    
    # Simulate a complete data discovery workflow
    print("Starting integrated data discovery workflow...")
    
    # Step 1: Emit workflow start event
    await event_handler.emit(
        EventType.CONNECTION_ESTABLISHED if 'EventType' in globals() else 'workflow_started',
        "integrated_workflow",
        data={"workflow": "data_discovery", "step": "start"}
    )
    
    # Step 2: Extract metadata
    print("  Step 1: Extracting metadata...")
    metadata_results = await metadata_extractor.extract_all_metadata()
    total_entities = sum(len(entities) for entities in metadata_results.values())
    
    await event_handler.emit(
        EventType.METADATA_EXTRACTED if 'EventType' in globals() else 'metadata_extracted',
        "integrated_workflow",
        data={"entities_extracted": total_entities}
    )
    
    # Step 3: Discover data flows
    print("  Step 2: Discovering data flows...")
    flow_results = await flow_mapper.discover_all_flows()
    total_flows = sum(len(flows) for flows in flow_results.values())
    
    await event_handler.emit(
        EventType.LINEAGE_DISCOVERED if 'EventType' in globals() else 'lineage_discovered',
        "integrated_workflow",
        data={"flows_discovered": total_flows}
    )
    
    # Step 4: Generate summary report
    print("  Step 3: Generating summary report...")
    
    metadata_summary = await metadata_extractor.get_metadata_summary()
    flow_summary = await flow_mapper.get_flow_summary()
    
    workflow_summary = {
        "workflow_completed": datetime.utcnow().isoformat(),
        "metadata": {
            "total_entities": metadata_summary.get('total_entities', 0),
            "systems": len(metadata_summary.get('systems', {})),
            "entity_types": len(metadata_summary.get('entity_types', {}))
        },
        "flows": {
            "total_flows": flow_summary.get('total_flows', 0),
            "total_entities": flow_summary.get('total_entities', 0),
            "systems": len(flow_summary.get('systems', {})),
            "flow_types": len(flow_summary.get('flow_types', {}))
        }
    }
    
    print("\nWorkflow Summary:")
    print(f"  Metadata entities discovered: {workflow_summary['metadata']['total_entities']}")
    print(f"  Data flows discovered: {workflow_summary['flows']['total_flows']}")
    print(f"  Systems analyzed: {workflow_summary['metadata']['systems']}")
    print(f"  Entity types found: {workflow_summary['metadata']['entity_types']}")
    print(f"  Flow types found: {workflow_summary['flows']['flow_types']}")
    
    # Step 5: Emit workflow completion event
    await event_handler.emit(
        EventType.CONNECTION_ESTABLISHED if 'EventType' in globals() else 'workflow_completed',
        "integrated_workflow",
        data=workflow_summary
    )
    
    print("✓ Integrated workflow demonstration completed")


async def main():
    """Main demonstration function."""
    print("DataLineagePy Core Components Demonstration")
    print("==========================================")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    try:
        # Run all demonstrations
        await demonstrate_event_handling()
        await demonstrate_metadata_extraction()
        await demonstrate_data_flow_mapping()
        await demonstrate_integrated_workflow()
        
        print("\n" + "="*60)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        print("="*60)
        
        print("\nKey Features Demonstrated:")
        print("✓ Event handling with listeners and priorities")
        print("✓ Metadata extraction from multiple systems")
        print("✓ Data flow discovery and mapping")
        print("✓ Integrated workflow coordination")
        print("✓ Statistics and monitoring capabilities")
        
        print("\nNext Steps:")
        print("- Implement specific connector classes for your data platforms")
        print("- Add custom event listeners for monitoring and alerting")
        print("- Extend metadata extractors for platform-specific schemas")
        print("- Create custom flow mappers for complex transformations")
        print("- Integrate with external monitoring and visualization tools")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())
