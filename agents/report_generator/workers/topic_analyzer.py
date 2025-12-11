"""TopicAnalyzer Worker - Analyze narrative to extract key topics.

Responsibility:
- Parse narrative text
- Extract key topics and themes
- Identify narrative sections
- Score topic importance/confidence
- Return structured topic data

Integrated with Week 1 systems:
- Structured logging
- Error handling with validation
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import WorkerError


class TopicAnalyzer:
    """Analyzes narrative to extract topics and sections."""

    # Topic keywords mapping - what indicates each topic
    TOPIC_KEYWORDS = {
        'anomalies': [
            'anomal', 'outlier', 'unusual', 'abnormal', 'irregular',
            'unexpected', 'deviant', 'exception', 'rare', 'distinct'
        ],
        'trends': [
            'trend', 'pattern', 'direction', 'increasing', 'decreasing',
            'rising', 'falling', 'growth', 'decline', 'momentum'
        ],
        'distribution': [
            'distributed', 'distribution', 'spread', 'histogram', 'density',
            'skewed', 'concentrated', 'dispersed', 'scattered'
        ],
        'correlation': [
            'correlat', 'relationship', 'associated', 'linked', 'connected',
            'dependent', 'influence', 'impact', 'affect'
        ],
        'patterns': [
            'pattern', 'recurring', 'cycle', 'seasonal', 'periodic',
            'repetition', 'sequence', 'consistency', 'rhythm'
        ],
        'comparison': [
            'compar', 'differ', 'similar', 'versus', 'against', 'higher',
            'lower', 'greater', 'less', 'exceed', 'surpass'
        ],
        'recommendations': [
            'recommend', 'suggest', 'advise', 'action', 'should', 'must',
            'consider', 'implement', 'improve', 'optimize'
        ],
        'risk': [
            'risk', 'danger', 'threat', 'concern', 'problem', 'issue',
            'critical', 'urgent', 'severe', 'warning'
        ],
        'performance': [
            'perform', 'efficient', 'effective', 'productivity', 'capability',
            'strength', 'weakness', 'success', 'failure', 'quality'
        ]
    }

    # Narrative section indicators
    SECTION_PATTERNS = {
        'executive_summary': r'(?:executive\s+summary|overview|at\s+a\s+glance)',
        'problem_statement': r'(?:problem|issue|challenge|concern)',
        'key_findings': r'(?:findings?|discovery|observation|result)',
        'action_plan': r'(?:action|recommendation|suggest|next\s+step)',
        'conclusion': r'(?:conclusion|summary|final|takeaway)'
    }

    def __init__(self) -> None:
        """Initialize TopicAnalyzer."""
        self.name = "TopicAnalyzer"
        self.logger = get_logger("TopicAnalyzer")
        self.structured_logger = get_structured_logger("TopicAnalyzer")
        self.logger.info(f"{self.name} initialized")

    def analyze_narrative(self, narrative: str) -> Dict[str, Any]:
        """Analyze narrative and extract topics.
        
        Args:
            narrative: Full narrative text to analyze
        
        Returns:
            Dict with topics, confidence scores, and structured data
        
        Raises:
            WorkerError: If analysis fails
        """
        if not narrative or not isinstance(narrative, str):
            raise WorkerError("Narrative must be non-empty string")
        
        try:
            self.logger.info("Analyzing narrative for topics")
            
            # Extract topics with confidence scores
            topics = self._extract_topics(narrative)
            
            # Identify sections
            sections = self._identify_sections(narrative)
            
            # Extract narrative structure
            structure = self._analyze_structure(narrative)
            
            result = {
                'topics': topics,
                'sections': sections,
                'structure': structure,
                'narrative_length': len(narrative),
                'word_count': len(narrative.split())
            }
            
            self.structured_logger.info("Narrative analysis complete", {
                'topic_count': len(topics),
                'section_count': len(sections),
                'word_count': result['word_count']
            })
            
            return result
        
        except WorkerError:
            raise
        except Exception as e:
            self.logger.error(f"Topic analysis failed: {e}")
            raise WorkerError(f"Analysis failed: {e}")

    def _extract_topics(self, narrative: str) -> Dict[str, float]:
        """Extract topics from narrative text.
        
        Args:
            narrative: Text to analyze
        
        Returns:
            Dict with topic names and confidence scores (0-1)
        """
        text_lower = narrative.lower()
        topics = {}
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            # Count keyword occurrences
            matches = 0
            for keyword in keywords:
                pattern = r'\b' + keyword + r'\w*'
                matches += len(re.findall(pattern, text_lower))
            
            if matches > 0:
                # Calculate confidence based on keyword density
                word_count = len(narrative.split())
                confidence = min(matches / (word_count / 10), 1.0)
                topics[topic] = round(confidence, 2)
        
        # Sort by confidence
        return dict(sorted(
            topics.items(),
            key=lambda x: x[1],
            reverse=True
        ))

    def _identify_sections(self, narrative: str) -> Dict[str, str]:
        """Identify narrative sections.
        
        Args:
            narrative: Text to analyze
        
        Returns:
            Dict with section names as keys, indicators as values
        """
        sections = {}
        text_lower = narrative.lower()
        
        for section_name, pattern in self.SECTION_PATTERNS.items():
            if re.search(pattern, text_lower):
                sections[section_name] = 'detected'
        
        return sections

    def _analyze_structure(self, narrative: str) -> Dict[str, Any]:
        """Analyze narrative structure.
        
        Args:
            narrative: Text to analyze
        
        Returns:
            Dict with structure information
        """
        lines = narrative.split('\n')
        sentences = re.split(r'[.!?]+', narrative)
        
        return {
            'line_count': len([l for l in lines if l.strip()]),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_line_length': sum(len(l) for l in lines) / max(len(lines), 1),
            'avg_sentence_length': sum(len(s.split()) for s in sentences) / max(len(sentences), 1),
            'has_lists': bool(re.search(r'[\n•\-\*]\s+\w', narrative)),
            'has_numbers': bool(re.search(r'\d+', narrative))
        }

    def extract_narrative_sections(self, narrative: str) -> List[Dict[str, Any]]:
        """Break narrative into sections with topic annotations.
        
        Args:
            narrative: Full narrative text
        
        Returns:
            List of sections with topics and importance
        """
        if not narrative or not isinstance(narrative, str):
            raise WorkerError("Narrative must be non-empty string")
        
        try:
            # Split by major breaks (double newlines or section headers)
            section_texts = re.split(r'\n\n+|^#+\s+', narrative, flags=re.MULTILINE)
            
            sections = []
            for i, section_text in enumerate(section_texts):
                if not section_text.strip():
                    continue
                
                # Extract topics from this section
                topics = self._extract_topics(section_text)
                
                # Determine section importance
                importance = self._determine_importance(section_text, topics)
                
                sections.append({
                    'index': i,
                    'text': section_text.strip(),
                    'topics': topics,
                    'importance': importance,
                    'length': len(section_text.split())
                })
            
            self.logger.info(f"Extracted {len(sections)} sections")
            return sections
        
        except Exception as e:
            self.logger.error(f"Section extraction failed: {e}")
            raise WorkerError(f"Section extraction failed: {e}")

    def _determine_importance(self, section_text: str, topics: Dict[str, float]) -> str:
        """Determine section importance based on topics and content.
        
        Args:
            section_text: Section text
            topics: Topics found in section
        
        Returns:
            Importance level: 'critical', 'high', 'medium', 'low'
        """
        # Critical topics increase importance
        critical_topics = ['risk', 'recommendations', 'anomalies']
        has_critical = any(t in topics for t in critical_topics)
        
        # Length matters
        word_count = len(section_text.split())
        
        # Keywords matter
        urgent_keywords = ['critical', 'urgent', 'must', 'immediately']
        has_urgent = any(k in section_text.lower() for k in urgent_keywords)
        
        # Determine level
        if has_critical and (has_urgent or word_count > 100):
            return 'critical'
        elif has_critical or len(topics) > 3:
            return 'high'
        elif word_count > 50 or len(topics) > 1:
            return 'medium'
        else:
            return 'low'

    def get_topic_summary(self, topics: Dict[str, float]) -> Dict[str, Any]:
        """Get summary of topics.
        
        Args:
            topics: Topics dict with confidence scores
        
        Returns:
            Summary dict
        """
        if not topics:
            return {
                'total_topics': 0,
                'primary_topics': [],
                'secondary_topics': [],
                'avg_confidence': 0.0
            }
        
        # Separate by confidence threshold
        primary = {t: c for t, c in topics.items() if c >= 0.6}
        secondary = {t: c for t, c in topics.items() if 0.3 <= c < 0.6}
        
        avg_confidence = sum(topics.values()) / len(topics) if topics else 0
        
        return {
            'total_topics': len(topics),
            'primary_topics': list(primary.keys()),
            'secondary_topics': list(secondary.keys()),
            'avg_confidence': round(avg_confidence, 2),
            'top_topic': max(topics.items(), key=lambda x: x[1])[0] if topics else None
        }
