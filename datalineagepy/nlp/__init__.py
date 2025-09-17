"""
Natural Language Processing Module for DataLineagePy

Provides natural language querying, semantic search, automated documentation,
and intelligent data discovery capabilities.
"""

# Import available modules with error handling
try:
    from .query_processor import QueryProcessor, NLQuery, QueryResult
except ImportError as e:
    print(f"Warning: Could not import query_processor: {e}")
    QueryProcessor = NLQuery = QueryResult = None

from .semantic_search import SemanticSearch, SearchIndex, SemanticResult
from .doc_generator import DocumentationGenerator, DocTemplate, DocSection
from .text_analyzer import TextAnalyzer, TextMetrics, EntityExtractor
from .language_model import LanguageModel, ModelConfig, ModelResponse
from .intent_classifier import IntentClassifier, Intent, IntentResult

# Factory functions
def create_query_processor(config=None):
    """Create a new query processor instance."""
    if QueryProcessor is None:
        raise ImportError("QueryProcessor is not available")
    return QueryProcessor(config)

def create_semantic_search(config=None):
    """Create a new semantic search instance."""
    return SemanticSearch(config)

def create_doc_generator(config=None):
    """Create a new documentation generator instance."""
    return DocumentationGenerator(config)

def create_text_analyzer(config=None):
    """Create a new text analyzer instance."""
    return TextAnalyzer(config)

def create_language_model(config=None):
    """Create a new language model instance."""
    return LanguageModel(config)

def create_intent_classifier(config=None):
    """Create a new intent classifier instance."""
    return IntentClassifier(config)

# Default configurations
DEFAULT_QUERY_CONFIG = {
    "max_query_length": 500,
    "supported_languages": ["en"],
    "enable_spell_check": True,
    "enable_autocomplete": True,
    "confidence_threshold": 0.7,
    "max_results": 50,
    "enable_caching": True,
    "cache_ttl": 3600
}

DEFAULT_SEARCH_CONFIG = {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "index_type": "faiss",
    "similarity_threshold": 0.5,
    "max_results": 100,
    "enable_reranking": True,
    "enable_filtering": True,
    "batch_size": 32
}

DEFAULT_DOC_CONFIG = {
    "output_format": "markdown",
    "include_diagrams": True,
    "include_examples": True,
    "include_metadata": True,
    "template_style": "technical",
    "auto_update": True,
    "version_control": True
}

DEFAULT_ANALYZER_CONFIG = {
    "enable_ner": True,
    "enable_sentiment": True,
    "enable_classification": True,
    "enable_summarization": True,
    "language": "en",
    "batch_size": 16,
    "max_text_length": 10000
}

DEFAULT_MODEL_CONFIG = {
    "model_type": "transformer",
    "model_name": "microsoft/DialoGPT-medium",
    "max_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "enable_streaming": True,
    "enable_caching": True
}

DEFAULT_INTENT_CONFIG = {
    "model_type": "classification",
    "confidence_threshold": 0.8,
    "max_intents": 10,
    "enable_multi_intent": True,
    "enable_context": True,
    "training_data_size": 1000
}

# Supported features
SUPPORTED_QUERY_TYPES = [
    "lineage_search", "data_discovery", "impact_analysis", "schema_search",
    "metadata_search", "relationship_search", "quality_search", "usage_search"
]

SUPPORTED_INTENTS = [
    "find_data", "trace_lineage", "analyze_impact", "search_schema",
    "get_metadata", "check_quality", "find_relationships", "get_usage"
]

SUPPORTED_ENTITIES = [
    "table", "column", "database", "schema", "pipeline", "job", "user",
    "application", "system", "metric", "dimension", "fact"
]

SUPPORTED_DOC_FORMATS = ["markdown", "html", "pdf", "docx", "json", "yaml"]

SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko"]

__all__ = [
    "QueryProcessor",
    "NLQuery",
    "QueryResult",
    "SemanticSearch",
    "SearchIndex",
    "SemanticResult",
    "DocumentationGenerator",
    "DocTemplate",
    "DocSection",
    "TextAnalyzer",
    "TextMetrics",
    "EntityExtractor",
    "LanguageModel",
    "ModelConfig",
    "ModelResponse",
    "IntentClassifier",
    "Intent",
    "IntentResult",
    "create_query_processor",
    "create_semantic_search",
    "create_doc_generator",
    "create_text_analyzer",
    "create_language_model",
    "create_intent_classifier",
    "DEFAULT_QUERY_CONFIG",
    "DEFAULT_SEARCH_CONFIG",
    "DEFAULT_DOC_CONFIG",
    "DEFAULT_ANALYZER_CONFIG",
    "DEFAULT_MODEL_CONFIG",
    "DEFAULT_INTENT_CONFIG",
    "SUPPORTED_QUERY_TYPES",
    "SUPPORTED_INTENTS",
    "SUPPORTED_ENTITIES",
    "SUPPORTED_DOC_FORMATS",
    "SUPPORTED_LANGUAGES"
]
