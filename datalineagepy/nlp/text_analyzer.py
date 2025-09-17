"""
Text Analyzer for DataLineagePy

Provides text analysis capabilities for data lineage documentation,
including entity extraction, sentiment analysis, and text metrics.
"""

import re
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading
import logging
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class TextMetrics:
    """Metrics for analyzed text."""
    word_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    character_count: int = 0
    unique_words: int = 0
    readability_score: float = 0.0
    complexity_score: float = 0.0
    sentiment_score: float = 0.0
    entities: List[Dict[str, Any]] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)


@dataclass
class EntityExtractor:
    """Configuration for entity extraction."""
    extract_emails: bool = True
    extract_urls: bool = True
    extract_phone_numbers: bool = True
    extract_dates: bool = True
    extract_numbers: bool = True
    extract_file_paths: bool = True
    extract_sql_tables: bool = True
    extract_column_names: bool = True
    custom_patterns: Dict[str, str] = field(default_factory=dict)


class TextAnalyzer:
    """Analyzes text content for data lineage documentation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.entity_extractor = EntityExtractor()
        self._lock = threading.RLock()
        
        # Common data-related keywords
        self.data_keywords = {
            'database', 'table', 'column', 'field', 'record', 'row', 'schema',
            'index', 'primary key', 'foreign key', 'join', 'query', 'select',
            'insert', 'update', 'delete', 'create', 'drop', 'alter', 'view',
            'procedure', 'function', 'trigger', 'constraint', 'dataframe',
            'dataset', 'csv', 'json', 'xml', 'parquet', 'avro', 'orc',
            'etl', 'pipeline', 'transformation', 'aggregation', 'filter',
            'sort', 'group by', 'having', 'where', 'order by', 'limit'
        }
        
        # Sentiment words (simplified)
        self.positive_words = {
            'good', 'great', 'excellent', 'perfect', 'amazing', 'wonderful',
            'fantastic', 'outstanding', 'superb', 'brilliant', 'awesome',
            'successful', 'efficient', 'effective', 'optimal', 'improved'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst',
            'failed', 'error', 'problem', 'issue', 'bug', 'broken',
            'slow', 'inefficient', 'problematic', 'difficult', 'complex'
        }
        
        logger.info("TextAnalyzer initialized")
    
    def analyze_text(self, text: str) -> TextMetrics:
        """Perform comprehensive text analysis."""
        with self._lock:
            if not text:
                return TextMetrics()
            
            # Basic metrics
            words = self._extract_words(text)
            sentences = self._extract_sentences(text)
            paragraphs = self._extract_paragraphs(text)
            
            # Calculate metrics
            word_count = len(words)
            sentence_count = len(sentences)
            paragraph_count = len(paragraphs)
            character_count = len(text)
            unique_words = len(set(word.lower() for word in words))
            
            # Advanced metrics
            readability_score = self._calculate_readability(text, words, sentences)
            complexity_score = self._calculate_complexity(text, words)
            sentiment_score = self._calculate_sentiment(words)
            
            # Entity extraction
            entities = self._extract_entities(text)
            
            # Keywords and topics
            keywords = self._extract_keywords(words)
            topics = self._extract_topics(text, words)
            
            metrics = TextMetrics(
                word_count=word_count,
                sentence_count=sentence_count,
                paragraph_count=paragraph_count,
                character_count=character_count,
                unique_words=unique_words,
                readability_score=readability_score,
                complexity_score=complexity_score,
                sentiment_score=sentiment_score,
                entities=entities,
                keywords=keywords,
                topics=topics
            )
            
            logger.debug(f"Analyzed text: {word_count} words, {sentence_count} sentences")
            return metrics
    
    def extract_data_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract data-related entities from text."""
        with self._lock:
            entities = []
            
            # SQL table names (basic pattern)
            table_pattern = r'\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\b'
            tables = re.findall(table_pattern, text, re.IGNORECASE)
            for table in tables:
                entities.append({
                    'type': 'table',
                    'value': table,
                    'context': 'SQL statement'
                })
            
            # Column names in SELECT statements
            select_pattern = r'SELECT\s+(.*?)\s+FROM'
            select_matches = re.findall(select_pattern, text, re.IGNORECASE | re.DOTALL)
            for match in select_matches:
                columns = [col.strip() for col in match.split(',')]
                for col in columns:
                    if col and col != '*':
                        entities.append({
                            'type': 'column',
                            'value': col,
                            'context': 'SELECT statement'
                        })
            
            # File paths
            if self.entity_extractor.extract_file_paths:
                file_pattern = r'[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*|/(?:[^/\s]+/)*[^/\s]+'
                files = re.findall(file_pattern, text)
                for file_path in files:
                    entities.append({
                        'type': 'file_path',
                        'value': file_path,
                        'context': 'File reference'
                    })
            
            # Database names (schema.table pattern)
            db_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\.[a-zA-Z_][a-zA-Z0-9_]*\b'
            databases = re.findall(db_pattern, text)
            for db in set(databases):
                entities.append({
                    'type': 'database',
                    'value': db,
                    'context': 'Schema reference'
                })
            
            return entities
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text."""
        # Simple word extraction
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs from text."""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _calculate_readability(self, text: str, words: List[str], sentences: List[str]) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)."""
        if not words or not sentences:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        
        # Count syllables (simplified)
        syllable_count = 0
        for word in words:
            syllables = max(1, len(re.findall(r'[aeiouAEIOU]', word)))
            syllable_count += syllables
        
        avg_syllables_per_word = syllable_count / len(words)
        
        # Simplified Flesch Reading Ease formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(100, score))
    
    def _calculate_complexity(self, text: str, words: List[str]) -> float:
        """Calculate text complexity score."""
        if not words:
            return 0.0
        
        # Factors that increase complexity
        complexity_score = 0.0
        
        # Long words
        long_words = [w for w in words if len(w) > 6]
        complexity_score += (len(long_words) / len(words)) * 30
        
        # Technical terms
        technical_terms = [w for w in words if w in self.data_keywords]
        complexity_score += (len(technical_terms) / len(words)) * 20
        
        # Special characters and numbers
        special_chars = len(re.findall(r'[^a-zA-Z\s]', text))
        complexity_score += (special_chars / len(text)) * 50
        
        return min(100, complexity_score)
    
    def _calculate_sentiment(self, words: List[str]) -> float:
        """Calculate sentiment score (-1 to 1)."""
        if not words:
            return 0.0
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        sentiment_score = (positive_count - negative_count) / total_sentiment_words
        return sentiment_score
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract various entities from text."""
        entities = []
        
        # Email addresses
        if self.entity_extractor.extract_emails:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            for email in emails:
                entities.append({'type': 'email', 'value': email})
        
        # URLs
        if self.entity_extractor.extract_urls:
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, text)
            for url in urls:
                entities.append({'type': 'url', 'value': url})
        
        # Phone numbers (basic pattern)
        if self.entity_extractor.extract_phone_numbers:
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, text)
            for phone in phones:
                entities.append({'type': 'phone', 'value': phone})
        
        # Dates (basic patterns)
        if self.entity_extractor.extract_dates:
            date_patterns = [
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
                r'\b\d{4}-\d{2}-\d{2}\b',      # YYYY-MM-DD
                r'\b\d{1,2}-\d{1,2}-\d{4}\b'   # MM-DD-YYYY
            ]
            for pattern in date_patterns:
                dates = re.findall(pattern, text)
                for date in dates:
                    entities.append({'type': 'date', 'value': date})
        
        # Numbers
        if self.entity_extractor.extract_numbers:
            number_pattern = r'\b\d+(?:\.\d+)?\b'
            numbers = re.findall(number_pattern, text)
            for number in numbers:
                entities.append({'type': 'number', 'value': number})
        
        # Custom patterns
        for entity_type, pattern in self.entity_extractor.custom_patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                entities.append({'type': entity_type, 'value': match})
        
        return entities
    
    def _extract_keywords(self, words: List[str], top_n: int = 10) -> List[str]:
        """Extract keywords from text."""
        if not words:
            return []
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
            'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Filter words
        filtered_words = [
            word for word in words 
            if word not in stop_words and len(word) > 2
        ]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Get top keywords
        keywords = [word for word, count in word_counts.most_common(top_n)]
        return keywords
    
    def _extract_topics(self, text: str, words: List[str]) -> List[str]:
        """Extract topics from text based on keyword patterns."""
        topics = []
        
        # Data processing topics
        if any(word in words for word in ['etl', 'pipeline', 'transformation', 'processing']):
            topics.append('data_processing')
        
        # Database topics
        if any(word in words for word in ['database', 'table', 'query', 'sql']):
            topics.append('database')
        
        # Analytics topics
        if any(word in words for word in ['analytics', 'analysis', 'report', 'dashboard']):
            topics.append('analytics')
        
        # Machine learning topics
        if any(word in words for word in ['model', 'training', 'prediction', 'algorithm']):
            topics.append('machine_learning')
        
        # Data quality topics
        if any(word in words for word in ['quality', 'validation', 'cleansing', 'profiling']):
            topics.append('data_quality')
        
        # Security topics
        if any(word in words for word in ['security', 'encryption', 'authentication', 'authorization']):
            topics.append('security')
        
        return topics
    
    def analyze_code_comments(self, code: str) -> Dict[str, Any]:
        """Analyze comments in code for documentation insights."""
        with self._lock:
            # Extract comments
            single_line_comments = re.findall(r'#\s*(.*)', code)
            multi_line_comments = re.findall(r'"""(.*?)"""', code, re.DOTALL)
            
            all_comments = single_line_comments + multi_line_comments
            comment_text = ' '.join(all_comments)
            
            if not comment_text:
                return {
                    'comment_count': 0,
                    'comment_ratio': 0.0,
                    'metrics': TextMetrics()
                }
            
            # Analyze comment text
            metrics = self.analyze_text(comment_text)
            
            # Calculate comment ratio
            code_lines = len(code.split('\n'))
            comment_lines = len(single_line_comments) + sum(
                len(comment.split('\n')) for comment in multi_line_comments
            )
            comment_ratio = comment_lines / code_lines if code_lines > 0 else 0.0
            
            return {
                'comment_count': len(all_comments),
                'comment_ratio': comment_ratio,
                'metrics': metrics
            }
    
    def suggest_improvements(self, metrics: TextMetrics) -> List[str]:
        """Suggest improvements based on text analysis."""
        suggestions = []
        
        # Readability suggestions
        if metrics.readability_score < 30:
            suggestions.append("Consider simplifying sentences and using shorter words to improve readability")
        
        # Complexity suggestions
        if metrics.complexity_score > 70:
            suggestions.append("Text appears complex - consider breaking down technical concepts")
        
        # Length suggestions
        if metrics.word_count < 10:
            suggestions.append("Consider adding more detailed description")
        elif metrics.word_count > 500:
            suggestions.append("Consider breaking long text into sections")
        
        # Sentiment suggestions
        if metrics.sentiment_score < -0.3:
            suggestions.append("Consider using more positive language")
        
        # Entity suggestions
        if not metrics.entities:
            suggestions.append("Consider adding specific examples or references")
        
        return suggestions


def create_text_analyzer(config: Optional[Dict[str, Any]] = None) -> TextAnalyzer:
    """Factory function to create a text analyzer."""
    return TextAnalyzer(config)
