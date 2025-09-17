"""
Language Model Integration for DataLineagePy

Provides integration with language models for natural language processing
of data lineage queries and documentation generation.
"""

import uuid
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import threading
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported language model types."""
    OPENAI_GPT = "openai_gpt"
    HUGGINGFACE = "huggingface"
    ANTHROPIC = "anthropic"
    LOCAL_MODEL = "local_model"
    MOCK = "mock"


@dataclass
class ModelConfig:
    """Configuration for language model."""
    model_type: ModelType = ModelType.MOCK
    model_name: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    system_prompt: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Response from language model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    tokens_used: int = 0
    model_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    success: bool = True


class LanguageModel:
    """Language model integration for NLP tasks."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._lock = threading.RLock()
        self._client = None
        self._conversation_history: List[Dict[str, str]] = []
        
        # Initialize model client based on type
        self._initialize_client()
        
        logger.info(f"LanguageModel initialized with {config.model_type.value}")
    
    def _initialize_client(self) -> None:
        """Initialize the appropriate model client."""
        if self.config.model_type == ModelType.OPENAI_GPT:
            self._initialize_openai_client()
        elif self.config.model_type == ModelType.HUGGINGFACE:
            self._initialize_huggingface_client()
        elif self.config.model_type == ModelType.ANTHROPIC:
            self._initialize_anthropic_client()
        elif self.config.model_type == ModelType.LOCAL_MODEL:
            self._initialize_local_client()
        else:
            # Mock client for testing
            self._client = MockLanguageClient()
    
    def _initialize_openai_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            # In production, use: import openai
            # self._client = openai.OpenAI(api_key=self.config.api_key)
            logger.warning("OpenAI client not implemented - using mock client")
            self._client = MockLanguageClient()
        except ImportError:
            logger.warning("OpenAI library not available - using mock client")
            self._client = MockLanguageClient()
    
    def _initialize_huggingface_client(self) -> None:
        """Initialize Hugging Face client."""
        try:
            # In production, use: from transformers import pipeline
            # self._client = pipeline("text-generation", model=self.config.model_name)
            logger.warning("Hugging Face client not implemented - using mock client")
            self._client = MockLanguageClient()
        except ImportError:
            logger.warning("Transformers library not available - using mock client")
            self._client = MockLanguageClient()
    
    def _initialize_anthropic_client(self) -> None:
        """Initialize Anthropic client."""
        try:
            # In production, use: import anthropic
            # self._client = anthropic.Anthropic(api_key=self.config.api_key)
            logger.warning("Anthropic client not implemented - using mock client")
            self._client = MockLanguageClient()
        except ImportError:
            logger.warning("Anthropic library not available - using mock client")
            self._client = MockLanguageClient()
    
    def _initialize_local_client(self) -> None:
        """Initialize local model client."""
        # For local models, you might use libraries like:
        # - llama-cpp-python
        # - transformers with local models
        # - ONNX runtime
        logger.warning("Local model client not implemented - using mock client")
        self._client = MockLanguageClient()
    
    def generate_text(self, prompt: str, context: Optional[str] = None, 
                     max_tokens: Optional[int] = None) -> ModelResponse:
        """Generate text using the language model."""
        with self._lock:
            try:
                # Prepare the full prompt
                full_prompt = self._prepare_prompt(prompt, context)
                
                # Generate response
                response = self._client.generate(
                    prompt=full_prompt,
                    max_tokens=max_tokens or self.config.max_tokens,
                    temperature=self.config.temperature
                )
                
                # Add to conversation history
                self._conversation_history.append({
                    "role": "user",
                    "content": prompt
                })
                self._conversation_history.append({
                    "role": "assistant", 
                    "content": response.content
                })
                
                logger.debug(f"Generated text response: {len(response.content)} characters")
                return response
                
            except Exception as e:
                logger.error(f"Error generating text: {e}")
                return ModelResponse(
                    content="",
                    error=str(e),
                    success=False
                )
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the intent of a natural language query."""
        with self._lock:
            prompt = f"""
            Analyze the following data lineage query and determine its intent:
            
            Query: "{query}"
            
            Please classify the intent as one of:
            - search: Looking for specific data or nodes
            - trace: Following data lineage upstream or downstream
            - analyze: Analyzing data relationships or impact
            - document: Requesting documentation or description
            - monitor: Checking status or health
            - other: Other intent
            
            Also extract any entities mentioned (table names, column names, etc.)
            
            Respond in JSON format with 'intent', 'confidence', and 'entities' fields.
            """
            
            response = self.generate_text(prompt)
            
            if response.success:
                try:
                    # Try to parse JSON response
                    result = json.loads(response.content)
                    return result
                except json.JSONDecodeError:
                    # Fallback to simple analysis
                    return self._simple_intent_analysis(query)
            else:
                return self._simple_intent_analysis(query)
    
    def generate_documentation(self, node_data: Dict[str, Any]) -> ModelResponse:
        """Generate documentation for a data node."""
        with self._lock:
            prompt = f"""
            Generate comprehensive documentation for the following data node:
            
            Node Information:
            - Name: {node_data.get('name', 'Unknown')}
            - Type: {node_data.get('type', 'Unknown')}
            - Description: {node_data.get('description', 'No description')}
            - Metadata: {json.dumps(node_data.get('metadata', {}), indent=2)}
            
            Please generate:
            1. A clear overview of what this node represents
            2. Its purpose and role in the data pipeline
            3. Key properties and characteristics
            4. Usage examples or common operations
            5. Any important considerations or limitations
            
            Format the response in markdown.
            """
            
            return self.generate_text(prompt)
    
    def explain_lineage_path(self, path_data: List[Dict[str, Any]]) -> ModelResponse:
        """Generate explanation for a data lineage path."""
        with self._lock:
            path_description = "\n".join([
                f"- {node.get('name', 'Unknown')} ({node.get('type', 'unknown')})"
                for node in path_data
            ])
            
            prompt = f"""
            Explain the following data lineage path in plain English:
            
            Data Flow Path:
            {path_description}
            
            Please provide:
            1. A clear explanation of how data flows through this path
            2. The transformation or processing that occurs at each step
            3. The business purpose of this data flow
            4. Any potential issues or bottlenecks
            
            Make the explanation accessible to both technical and non-technical users.
            """
            
            return self.generate_text(prompt)
    
    def suggest_data_quality_checks(self, node_data: Dict[str, Any]) -> ModelResponse:
        """Suggest data quality checks for a node."""
        with self._lock:
            prompt = f"""
            Based on the following data node information, suggest appropriate data quality checks:
            
            Node: {node_data.get('name', 'Unknown')}
            Type: {node_data.get('type', 'Unknown')}
            Schema: {json.dumps(node_data.get('schema', {}), indent=2)}
            Metadata: {json.dumps(node_data.get('metadata', {}), indent=2)}
            
            Please suggest:
            1. Completeness checks (null values, missing data)
            2. Validity checks (data types, formats, ranges)
            3. Consistency checks (referential integrity, business rules)
            4. Uniqueness checks (duplicates, primary keys)
            5. Timeliness checks (freshness, latency)
            
            Provide specific, actionable recommendations.
            """
            
            return self.generate_text(prompt)
    
    def _prepare_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Prepare the full prompt with system prompt and context."""
        full_prompt = ""
        
        # Add system prompt if configured
        if self.config.system_prompt:
            full_prompt += f"System: {self.config.system_prompt}\n\n"
        
        # Add context if provided
        if context:
            full_prompt += f"Context: {context}\n\n"
        
        # Add the main prompt
        full_prompt += f"User: {prompt}"
        
        return full_prompt
    
    def _simple_intent_analysis(self, query: str) -> Dict[str, Any]:
        """Simple rule-based intent analysis as fallback."""
        query_lower = query.lower()
        
        # Intent keywords
        intent_keywords = {
            'search': ['find', 'search', 'look for', 'show me', 'get', 'list'],
            'trace': ['trace', 'follow', 'upstream', 'downstream', 'lineage', 'path'],
            'analyze': ['analyze', 'impact', 'effect', 'relationship', 'dependency'],
            'document': ['document', 'describe', 'explain', 'what is', 'tell me about'],
            'monitor': ['status', 'health', 'monitor', 'check', 'alert']
        }
        
        # Find matching intent
        intent_scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent] / len(query.split())
        else:
            best_intent = 'other'
            confidence = 0.1
        
        # Simple entity extraction
        entities = []
        # Look for quoted strings (table names, etc.)
        import re
        quoted_entities = re.findall(r'"([^"]*)"', query)
        entities.extend([{'type': 'quoted', 'value': entity} for entity in quoted_entities])
        
        # Look for SQL-like patterns
        sql_patterns = {
            'table': r'\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            'column': r'\bSELECT\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        }
        
        for entity_type, pattern in sql_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend([{'type': entity_type, 'value': match} for match in matches])
        
        return {
            'intent': best_intent,
            'confidence': min(1.0, confidence),
            'entities': entities
        }
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        with self._lock:
            self._conversation_history.clear()
            logger.debug("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        with self._lock:
            return self._conversation_history.copy()
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt."""
        with self._lock:
            self.config.system_prompt = prompt
            logger.debug("System prompt updated")


class MockLanguageClient:
    """Mock language model client for testing."""
    
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> ModelResponse:
        """Generate a mock response."""
        # Simple mock responses based on prompt content
        prompt_lower = prompt.lower()
        
        if 'documentation' in prompt_lower:
            content = """# Data Node Documentation

This is a mock documentation response for the data node. In a production environment, this would be generated by a real language model with comprehensive analysis and insights.

## Overview
The data node represents a key component in the data pipeline with specific characteristics and relationships.

## Key Properties
- Type: Data processing node
- Purpose: Transform and process data
- Status: Active

## Usage
This node is typically used for data transformation operations in the pipeline."""
        
        elif 'intent' in prompt_lower:
            content = """{
    "intent": "search",
    "confidence": 0.8,
    "entities": [
        {"type": "table", "value": "example_table"},
        {"type": "column", "value": "example_column"}
    ]
}"""
        
        elif 'lineage' in prompt_lower:
            content = """This data lineage path shows the flow of data through multiple processing stages:

1. **Source Data**: Raw data is ingested from the source system
2. **Transformation**: Data is cleaned and transformed according to business rules
3. **Aggregation**: Data is aggregated and summarized for reporting
4. **Output**: Final processed data is made available for consumption

The flow ensures data quality and consistency throughout the pipeline."""
        
        elif 'quality' in prompt_lower:
            content = """## Recommended Data Quality Checks

### Completeness Checks
- Check for null values in required fields
- Verify record counts match expected volumes

### Validity Checks
- Validate data types and formats
- Check value ranges and constraints

### Consistency Checks
- Verify referential integrity
- Check business rule compliance

### Uniqueness Checks
- Identify duplicate records
- Validate primary key constraints

### Timeliness Checks
- Monitor data freshness
- Check processing latency"""
        
        else:
            content = "This is a mock response from the language model. In a production environment, this would be replaced with actual AI-generated content based on the specific prompt and context provided."
        
        return ModelResponse(
            content=content,
            tokens_used=len(content.split()),
            model_name="mock-model",
            success=True
        )


def create_language_model(config: Optional[ModelConfig] = None) -> LanguageModel:
    """Factory function to create a language model instance."""
    if config is None:
        config = ModelConfig()
    return LanguageModel(config)
