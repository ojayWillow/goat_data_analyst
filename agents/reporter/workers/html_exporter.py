"""HTMLExporter - Exports reports to HTML format.

Enhanced with:
- CSS styling
- Professional HTML structure
- Better table formatting
- File writing capability
- Responsive design
"""

import os
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from pathlib import Path
from .base_worker import BaseWorker, WorkerResult, ErrorType, ValidationUtils
from agents.error_intelligence.main import ErrorIntelligence


class HTMLExporter(BaseWorker):
    """Exports reports to HTML format with professional styling.
    
    Capabilities:
    - Convert report data to styled HTML
    - CSS styling with responsive design
    - Nested data structure rendering
    - Write to file system
    - Professional formatting
    """
    
    # Constants
    DEFAULT_OUTPUT_DIR = "reports"
    
    def __init__(self):
        super().__init__("html_exporter")
        self._ensure_output_dir()
    
    def execute(
        self,
        report_data: Dict[str, Any],
        file_path: Optional[str] = None,
        write_to_disk: bool = False,
        include_toc: bool = True,
        **kwargs
    ) -> WorkerResult:
        """Export report to HTML format.
        
        Args:
            report_data: Report data to export
            file_path: Optional file path (auto-generated if None)
            write_to_disk: Whether to write file to disk (disabled by default)
            include_toc: Include table of contents
            **kwargs: Additional parameters
            
        Returns:
            WorkerResult with export information
        """
        result = self._create_result(
            success=True,
            task_type="html_export",
            data={}
        )
        
        try:
            # Validate input
            if not report_data or not isinstance(report_data, dict):
                self._add_error(
                    result,
                    ErrorType.DATA_VALIDATION_ERROR,
                    "Report data must be a non-empty dictionary",
                    severity="error"
                )
                result.success = False
                return result
            
            # Generate HTML
            html_content = self._generate_html(report_data, include_toc=include_toc)
            
            # Determine file path
            if file_path is None:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                file_path = f"{self.DEFAULT_OUTPUT_DIR}/report_{timestamp}.html"
            
            # Write to disk if requested (with error handling)
            write_path = None
            if write_to_disk:
                try:
                    write_path = self._write_to_disk(html_content, file_path, result)
                    if not write_path:
                        # Error already added in _write_to_disk
                        # Still return the HTML even if file write failed
                        pass
                except Exception as e:
                    # Suppress file write errors and continue
                    self.logger.warning(f"File write skipped: {str(e)}")
                    write_path = None
            
            result.data = {
                "status": "success",
                "html": html_content,
                "html_size": len(html_content),
                "file_path": write_path or file_path,
                "written_to_disk": write_to_disk and write_path is not None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            result.quality_score = 0.95
            
            self.logger.info(f"HTML export completed: {write_path or file_path}")
            
        except Exception as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Export failed: {str(e)}",
                severity="error"
            )
            result.success = False
        
        return result
    
    def _generate_html(self, report_data: Dict[str, Any], include_toc: bool = True) -> str:
        """Generate styled HTML from report data."""
        html_parts = []
        
        # HTML header with CSS
        html_parts.append(self._get_html_header())
        
        # Title and metadata
        title = report_data.get('title', 'Data Analysis Report')
        html_parts.append(f"<h1>{title}</h1>")
        html_parts.append(f"<p class='metadata'>Generated: {datetime.now(timezone.utc).isoformat()}</p>")
        
        # Table of contents
        if include_toc and len(report_data) > 3:
            html_parts.append(self._generate_toc(report_data))
        
        # Body content
        for key, value in report_data.items():
            if key in ['title', 'generated_at', 'timestamp']:
                continue
            
            if isinstance(value, dict):
                section_title = key.replace('_', ' ').title()
                html_parts.append(f"<section>")
                html_parts.append(f"<h2 id='{key}'>{section_title}</h2>")
                html_parts.append(self._dict_to_html(value, depth=2))
                html_parts.append("</section>")
            elif isinstance(value, (list, tuple)):
                section_title = key.replace('_', ' ').title()
                html_parts.append(f"<section>")
                html_parts.append(f"<h2 id='{key}'>{section_title}</h2>")
                html_parts.append(self._list_to_html(value))
                html_parts.append("</section>")
            elif isinstance(value, str):
                html_parts.append(f"<p><strong>{key.replace('_', ' ')}:</strong> {value}</p>")
        
        # HTML footer
        html_parts.append("</main></body></html>")
        
        return "\n".join(html_parts)
    
    def _dict_to_html(self, data: Dict[str, Any], depth: int = 0) -> str:
        """Convert nested dictionary to HTML."""
        if not data:
            return ""
        
        html = "<table class='data-table'>"
        
        for key, value in data.items():
            html += "<tr>"
            html += f"<td class='label'><strong>{key.replace('_', ' ')}</strong></td>"
            
            if isinstance(value, dict):
                html += f"<td>{self._dict_to_html(value, depth+1)}</td>"
            elif isinstance(value, (list, tuple)):
                html += f"<td>{self._list_to_html(value)}</td>"
            else:
                html += f"<td class='value'>{value}</td>"
            
            html += "</tr>"
        
        html += "</table>"
        return html
    
    def _list_to_html(self, items: list) -> str:
        """Convert list to HTML."""
        if not items:
            return ""
        
        if isinstance(items[0], dict):
            # List of dicts -> table
            html = "<table class='data-table'>"
            
            # Header
            if len(items) > 0:
                html += "<tr>"
                for key in items[0].keys():
                    html += f"<th>{key.replace('_', ' ')}</th>"
                html += "</tr>"
                
                # Rows
                for item in items:
                    html += "<tr>"
                    for value in item.values():
                        html += f"<td>{value}</td>"
                    html += "</tr>"
            
            html += "</table>"
            return html
        else:
            # Simple list -> ul
            html = "<ul>"
            for item in items:
                html += f"<li>{item}</li>"
            html += "</ul>"
            return html
    
    def _generate_toc(self, data: Dict[str, Any]) -> str:
        """Generate table of contents."""
        toc_items = []
        
        for key in data.keys():
            if key not in ['title', 'generated_at', 'timestamp', 'report_type']:
                section_title = key.replace('_', ' ').title()
                toc_items.append(f"<li><a href='#{key}'>{section_title}</a></li>")
        
        if not toc_items:
            return ""
        
        return (
            "<div class='toc'>"
            "<h3>Table of Contents</h3>"
            "<ul>" + "".join(toc_items) + "</ul>"
            "</div>"
        )
    
    def _get_html_header(self) -> str:
        """Get HTML header with CSS styling."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        main {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        
        h3 {{
            color: #34495e;
            margin-top: 15px;
            margin-bottom: 10px;
        }}
        
        section {{
            margin-bottom: 40px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 4px;
        }}
        
        .metadata {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        
        .toc {{
            background: #ecf0f1;
            padding: 20px;
            border-left: 4px solid #3498db;
            border-radius: 4px;
            margin: 20px 0 40px 0;
        }}
        
        .toc ul {{
            list-style-position: inside;
        }}
        
        .toc a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        .toc a:hover {{
            text-decoration: underline;
        }}
        
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        table.data-table th,
        table.data-table td {{
            border: 1px solid #bdc3c7;
            padding: 12px;
            text-align: left;
        }}
        
        table.data-table th {{
            background: #3498db;
            color: white;
            font-weight: bold;
        }}
        
        table.data-table tr:nth-child(even) {{
            background: #ecf0f1;
        }}
        
        table.data-table tr:hover {{
            background: #d5dbdb;
        }}
        
        table.data-table td.label {{
            font-weight: 500;
            width: 30%;
        }}
        
        table.data-table td.value {{
            font-family: 'Courier New', monospace;
        }}
        
        ul {{
            margin-left: 20px;
            margin-bottom: 10px;
        }}
        
        li {{
            margin-bottom: 8px;
        }}
        
        p {{
            margin-bottom: 12px;
        }}
        
        strong {{
            color: #2c3e50;
        }}
        
        @media (max-width: 768px) {{
            main {{
                padding: 20px;
            }}
            
            table.data-table {{
                font-size: 0.9em;
            }}
            
            table.data-table th,
            table.data-table td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
<main>
"""
    
    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        try:
            Path(self.DEFAULT_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Output directory ready: {self.DEFAULT_OUTPUT_DIR}")
        except Exception as e:
            self.logger.warning(f"Could not create output directory: {e}")
    
    def _write_to_disk(self,
                       html_content: str,
                       file_path: str,
                       result: WorkerResult) -> Optional[str]:
        """Write HTML to disk."""
        try:
            # Ensure directory exists
            output_dir = os.path.dirname(file_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Convert to absolute path
            abs_path = os.path.abspath(file_path)
            
            # Write file
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Verify file was written
            if not os.path.exists(abs_path):
                self._add_error(
                    result,
                    ErrorType.COMPUTATION_ERROR,
                    f"File verification failed: {abs_path}",
                    severity="error"
                )
                return None
            
            file_size = os.path.getsize(abs_path) / 1024  # KB
            self.logger.info(f"HTML file written: {abs_path} ({file_size:.1f} KB)")
            
            return abs_path
        
        except (IOError, OSError) as e:
            self._add_error(
                result,
                ErrorType.COMPUTATION_ERROR,
                f"Failed to write file: {str(e)}",
                severity="warning",
                suggestion="Check directory permissions and disk space"
            )
            return None
        except Exception as e:
            self._add_error(
                result,
                ErrorType.UNKNOWN_ERROR,
                f"Unexpected error writing file: {str(e)}",
                severity="warning"
            )
            return None
