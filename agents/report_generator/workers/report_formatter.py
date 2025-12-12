"""ReportFormatter Worker - Format narrative and charts into professional reports.

Responsibility:
- Create HTML reports with narrative and charts
- Create Markdown reports
- Create PDF reports (when supported)
- Professional styling and layout
- Responsive design

Integrated with Week 1 systems:
- Structured logging
- Error handling with validation
- Error Intelligence monitoring
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from core.exceptions import WorkerError
from agents.error_intelligence.main import ErrorIntelligence


class ReportFormatter:
    """Formats reports into professional output."""

    def __init__(self) -> None:
        """Initialize ReportFormatter."""
        self.name = "ReportFormatter"
        self.logger = get_logger("ReportFormatter")
        self.structured_logger = get_structured_logger("ReportFormatter")
        self.error_intelligence = ErrorIntelligence()
        self.logger.info(f"{self.name} initialized")

    def format_to_html(
        self,
        narrative: str,
        selected_charts: Dict[str, List[Dict[str, Any]]],
        title: str = "Data Analysis Report",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format report to HTML.
        
        Args:
            narrative: Full narrative text
            selected_charts: Charts selected by section
            title: Report title
            metadata: Optional metadata (author, date, etc)
        
        Returns:
            HTML string
        
        Raises:
            WorkerError: If formatting fails
        """
        if not narrative:
            raise WorkerError("Narrative is required")
        
        try:
            self.logger.info("Formatting report to HTML")
            
            # Build HTML
            html_parts = []
            
            # Header
            html_parts.append(self._build_html_header(title, metadata))
            
            # Body
            html_parts.append('<body>')
            html_parts.append(self._build_html_navigation())
            html_parts.append(self._build_html_title(title, metadata))
            
            # Content
            html_parts.append('<main class="report-content">')
            html_parts.append(self._format_narrative_html(narrative))
            html_parts.append('</main>')
            
            # Charts section
            if selected_charts:
                html_parts.append(self._build_html_charts_section(selected_charts))
            
            # Footer
            html_parts.append(self._build_html_footer())
            html_parts.append('</body>')
            html_parts.append('</html>')
            
            html_content = '\n'.join(html_parts)
            self.structured_logger.info("HTML formatting complete", {
                'size_kb': len(html_content) / 1024,
                'sections': len(selected_charts) if selected_charts else 0
            })
            
            self.error_intelligence.track_success(
                agent_name="report_generator",
                worker_name="ReportFormatter",
                operation="format_to_html",
                context={
                    'title': title,
                    'html_size_kb': round(len(html_content) / 1024, 2),
                    'chart_sections': len(selected_charts) if selected_charts else 0
                }
            )
            
            return html_content
        
        except WorkerError:
            raise
        except Exception as e:
            self.logger.error(f"HTML formatting failed: {e}")
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="ReportFormatter",
                error_type=type(e).__name__,
                error_message=str(e),
                context={'title': title, 'format': 'html'}
            )
            raise WorkerError(f"HTML formatting failed: {e}")

    def format_to_markdown(
        self,
        narrative: str,
        selected_charts: Dict[str, List[Dict[str, Any]]],
        title: str = "Data Analysis Report",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format report to Markdown.
        
        Args:
            narrative: Full narrative text
            selected_charts: Charts selected by section
            title: Report title
            metadata: Optional metadata
        
        Returns:
            Markdown string
        
        Raises:
            WorkerError: If formatting fails
        """
        if not narrative:
            raise WorkerError("Narrative is required")
        
        try:
            self.logger.info("Formatting report to Markdown")
            
            parts = []
            
            # Title
            parts.append(f"# {title}")
            parts.append("")
            
            # Metadata
            if metadata:
                parts.append("## Report Information")
                for key, value in metadata.items():
                    parts.append(f"- **{key}:** {value}")
                parts.append("")
            
            # Narrative
            parts.append("## Analysis")
            parts.append(narrative)
            parts.append("")
            
            # Charts section
            if selected_charts:
                parts.append("## Visualizations")
                parts.append("")
                
                for section, charts in selected_charts.items():
                    parts.append(f"### {section}")
                    for chart in charts:
                        chart_name = chart.get('name', 'Chart')
                        chart_path = chart.get('path', '')
                        if chart_path:
                            parts.append(f"![{chart_name}]({chart_path})")
                        else:
                            parts.append(f"- {chart_name}")
                    parts.append("")
            
            # Footer
            parts.append("---")
            parts.append(f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
            
            markdown_content = '\n'.join(parts)
            self.structured_logger.info("Markdown formatting complete", {
                'size_kb': len(markdown_content) / 1024
            })
            
            self.error_intelligence.track_success(
                agent_name="report_generator",
                worker_name="ReportFormatter",
                operation="format_to_markdown",
                context={
                    'title': title,
                    'markdown_size_kb': round(len(markdown_content) / 1024, 2),
                    'chart_sections': len(selected_charts) if selected_charts else 0
                }
            )
            
            return markdown_content
        
        except WorkerError:
            raise
        except Exception as e:
            self.logger.error(f"Markdown formatting failed: {e}")
            self.error_intelligence.track_error(
                agent_name="report_generator",
                worker_name="ReportFormatter",
                error_type=type(e).__name__,
                error_message=str(e),
                context={'title': title, 'format': 'markdown'}
            )
            raise WorkerError(f"Markdown formatting failed: {e}")

    def _build_html_header(self, title: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Build HTML head section."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}
        
        header {{
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .report-meta {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        nav {{
            background-color: #34495e;
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        nav a {{
            color: white;
            text-decoration: none;
            margin-right: 1.5rem;
            font-size: 0.95rem;
        }}
        
        nav a:hover {{
            color: #3498db;
        }}
        
        main {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        main h2 {{
            color: #2c3e50;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #3498db;
        }}
        
        main h3 {{
            color: #34495e;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }}
        
        main p {{
            margin-bottom: 1rem;
            text-align: justify;
        }}
        
        .charts-section {{
            background-color: #ecf0f1;
            padding: 2rem;
            margin: 2rem 0;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        
        .chart-container {{
            background: white;
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: 6px;
            border: 1px solid #ddd;
        }}
        
        .chart-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 1rem;
        }}
        
        footer {{
            background-color: #34495e;
            color: white;
            text-align: center;
            padding: 1rem;
            margin-top: 2rem;
        }}
        
        .metadata {{
            background: #ecf0f1;
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 2rem;
        }}
        
        .metadata p {{
            margin: 0.25rem 0;
        }}
        
        @media (max-width: 768px) {{
            header h1 {{ font-size: 1.8rem; }}
            main {{ padding: 1rem; }}
            .charts-section {{ padding: 1rem; }}
        }}
    </style>
</head>
"""

    def _build_html_navigation(self) -> str:
        """Build HTML navigation."""
        return """<nav>
    <a href="#top">Overview</a>
    <a href="#content">Analysis</a>
    <a href="#charts">Visualizations</a>
</nav>
"""

    def _build_html_title(self, title: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Build HTML title section."""
        meta_html = ""
        if metadata:
            meta_html = "<div class='metadata'>"
            for key, value in metadata.items():
                meta_html += f"<p><strong>{key}:</strong> {value}</p>"
            meta_html += "</div>"
        
        return f"""<header id="top">
    <h1>{title}</h1>
    <div class="report-meta">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
</header>
{meta_html}
"""

    def _build_html_charts_section(self, selected_charts: Dict[str, List[Dict[str, Any]]]) -> str:
        """Build HTML charts section."""
        html = "<section class='charts-section' id='charts'><h2>Visualizations</h2>"
        
        for section, charts in selected_charts.items():
            html += f"<h3>{section}</h3>"
            for chart in charts:
                chart_name = chart.get('name', 'Chart')
                chart_path = chart.get('path', '')
                html += f"<div class='chart-container'>"
                html += f"<div class='chart-title'>{chart_name}</div>"
                if chart_path:
                    html += f"<img src='{chart_path}' style='max-width: 100%; height: auto;' alt='{chart_name}'>"
                html += "</div>"
        
        html += "</section>"
        return html

    def _build_html_footer(self) -> str:
        """Build HTML footer."""
        return f"""<footer>
    <p>&copy; {datetime.now().year} Data Analysis Report. All rights reserved.</p>
    <p><small>Generated by GOAT Data Analyst</small></p>
</footer>
"""

    def _format_narrative_html(self, narrative: str) -> str:
        """Format narrative text to HTML.
        
        Args:
            narrative: Narrative text
        
        Returns:
            Formatted HTML
        """
        # Escape HTML special characters
        narrative = (
            narrative
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
        )
        
        # Convert common markdown to HTML
        lines = narrative.split('\n')
        html_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                html_lines.append('<br>')
            elif line.startswith('# '):
                html_lines.append(f"<h2>{line[2:]}</h2>")
            elif line.startswith('## '):
                html_lines.append(f"<h3>{line[3:]}</h3>")
            elif line.startswith('- '):
                html_lines.append(f"<li>{line[2:]}</li>")
            else:
                html_lines.append(f"<p>{line}</p>")
        
        return ''.join(html_lines)

    def get_format_options(self) -> Dict[str, Any]:
        """Get available format options.
        
        Returns:
            Dict with format options
        """
        return {
            'formats': ['html', 'markdown', 'pdf'],
            'html': {
                'responsive': True,
                'includes_charts': True,
                'styling': 'professional'
            },
            'markdown': {
                'responsive': False,
                'includes_charts': True,
                'styling': 'basic'
            },
            'pdf': {
                'responsive': False,
                'includes_charts': True,
                'styling': 'print'
            }
        }
