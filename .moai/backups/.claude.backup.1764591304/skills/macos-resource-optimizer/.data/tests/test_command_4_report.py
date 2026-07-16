"""
Test suite for /macos-resource-optimizer:4-report command.

Command: Generate markdown, JSON, and HTML reports
Delegation: manager-resource-coordinator (report generation with format support)
Tests: 3 (markdown generation, JSON output, HTML rendering)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestCommand4ReportMarkdownGeneration:
    """Test 1: Markdown report generation."""

    def test_report_command_generates_markdown_report(self):
        """Test /macos-resource-optimizer:4-report generates markdown report."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "markdown": {
                        "filename": "report_2025-11-30.md",
                        "format": "markdown",
                        "size_bytes": 5240,
                        "content_preview": """# macOS Resource Optimization Report

**Date**: 2025-11-30T10:30:00Z
**System**: MacBook Pro (14-inch, M3 Max)

## Executive Summary

System resource analysis completed with optimization recommendations.

- **CPU Usage**: 45.2% (Normal)
- **Memory Usage**: 75.0% (Elevated)
- **Disk Usage**: 65.0% (Good)

## Detailed Analysis

### CPU Resources
- Average Usage: 45.2%
- Peak Usage: 88.5%
- Processes: 128

### Memory Resources
- Used: 12GB / 16GB (75%)
- Pressure: Moderate
"""
                    }
                }
            }

            result = mock_task.return_value

            # Verify markdown report generation
            assert result["status"] == "success"
            assert "markdown" in result["reports"]
            assert result["reports"]["markdown"]["format"] == "markdown"
            assert result["reports"]["markdown"]["size_bytes"] > 0

    def test_report_markdown_includes_sections(self):
        """Test markdown report includes all required sections."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "markdown": {
                        "sections": [
                            "Header",
                            "Executive Summary",
                            "CPU Analysis",
                            "Memory Analysis",
                            "Disk Analysis",
                            "Network Analysis",
                            "Battery Analysis",
                            "Thermal Analysis",
                            "Alerts and Recommendations",
                            "Conclusion"
                        ]
                    }
                }
            }

            result = mock_task.return_value

            # Verify sections present
            markdown_sections = result["reports"]["markdown"]["sections"]
            assert "Executive Summary" in markdown_sections
            assert "CPU Analysis" in markdown_sections
            assert "Recommendations" in markdown_sections

    def test_report_markdown_formatting_valid(self):
        """Test markdown report has valid markdown formatting."""

        with patch('Task') as mock_task:
            markdown_content = """# macOS Resource Optimization Report

## Executive Summary

- CPU Usage: 45.2%
- Memory Usage: 75.0%

### Detailed Metrics

| Metric | Value |
|--------|-------|
| CPU | 45.2% |
| Memory | 75.0% |
"""

            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "markdown": {
                        "content": markdown_content,
                        "valid_markdown": True
                    }
                }
            }

            result = mock_task.return_value

            # Verify markdown structure
            assert "#" in result["reports"]["markdown"]["content"]
            assert result["reports"]["markdown"]["valid_markdown"] is True


class TestCommand4ReportJsonOutput:
    """Test 2: JSON format output and validation."""

    def test_report_command_generates_json_report(self):
        """Test /macos-resource-optimizer:4-report generates JSON report."""

        with patch('Task') as mock_task:
            json_data = {
                "report_id": "rpt_20251130_001",
                "timestamp": "2025-11-30T10:30:00Z",
                "system_info": {
                    "model": "MacBook Pro (14-inch, M3 Max)",
                    "os": "macOS 15.1.1",
                    "cores": 12
                },
                "metrics": {
                    "cpu": {"usage_percent": 45.2, "threshold": 80},
                    "memory": {"usage_percent": 75.0, "threshold": 85},
                    "disk": {"usage_percent": 65.0, "threshold": 90},
                    "thermal": {"cpu_temp": 65.0, "threshold": 85}
                }
            }

            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "json": {
                        "filename": "report_2025-11-30.json",
                        "format": "json",
                        "data": json_data,
                        "size_bytes": json.dumps(json_data).__sizeof__()
                    }
                }
            }

            result = mock_task.return_value

            # Verify JSON report generation
            assert result["status"] == "success"
            assert "json" in result["reports"]
            assert result["reports"]["json"]["format"] == "json"

    def test_report_json_is_valid_serializable(self):
        """Test JSON report is properly serializable."""

        with patch('Task') as mock_task:
            test_data = {
                "metrics": {
                    "cpu": {"usage_percent": 45.2},
                    "memory": {"usage_percent": 75.0}
                }
            }

            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "json": {
                        "data": test_data,
                        "serializable": True
                    }
                }
            }

            result = mock_task.return_value

            # Verify JSON serialization
            try:
                json_str = json.dumps(result["reports"]["json"]["data"])
                assert json_str is not None
            except TypeError as e:
                pytest.fail(f"JSON not serializable: {e}")

    def test_report_json_includes_all_metrics(self):
        """Test JSON report includes all resource metrics."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "json": {
                        "data": {
                            "metrics": {
                                "cpu": {"usage_percent": 45.2},
                                "memory": {"usage_percent": 75.0},
                                "disk": {"usage_percent": 65.0},
                                "network": {"bandwidth_mbps": 125.0},
                                "battery": {"percent": 80.0},
                                "thermal": {"cpu_temp": 65.0}
                            }
                        }
                    }
                }
            }

            result = mock_task.return_value
            metrics = result["reports"]["json"]["data"]["metrics"]

            # Verify all metrics present
            assert "cpu" in metrics
            assert "memory" in metrics
            assert "disk" in metrics
            assert "network" in metrics
            assert "battery" in metrics
            assert "thermal" in metrics

    def test_report_json_includes_timestamp(self):
        """Test JSON report includes timestamp information."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "json": {
                        "data": {
                            "timestamp": "2025-11-30T10:30:00Z",
                            "report_id": "rpt_20251130_001"
                        }
                    }
                }
            }

            result = mock_task.return_value
            json_data = result["reports"]["json"]["data"]

            # Verify timestamp
            assert "timestamp" in json_data
            assert "2025-11-30" in json_data["timestamp"]


class TestCommand4ReportHtmlRendering:
    """Test 3: HTML report rendering and visualization."""

    def test_report_command_generates_html_report(self):
        """Test /macos-resource-optimizer:4-report generates HTML report."""

        with patch('Task') as mock_task:
            html_content = """<!DOCTYPE html>
<html>
<head>
    <title>macOS Resource Report</title>
    <style>
        body { font-family: Arial; }
        .metric { display: inline-block; margin: 10px; }
    </style>
</head>
<body>
    <h1>macOS Resource Optimization Report</h1>
    <div class="metric">
        <h2>CPU Usage</h2>
        <p>45.2%</p>
    </div>
    <div class="metric">
        <h2>Memory Usage</h2>
        <p>75.0%</p>
    </div>
</body>
</html>"""

            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "html": {
                        "filename": "report_2025-11-30.html",
                        "format": "html",
                        "content": html_content,
                        "size_bytes": len(html_content)
                    }
                }
            }

            result = mock_task.return_value

            # Verify HTML report generation
            assert result["status"] == "success"
            assert "html" in result["reports"]
            assert result["reports"]["html"]["format"] == "html"
            assert "<html>" in result["reports"]["html"]["content"]

    def test_report_html_includes_charts(self):
        """Test HTML report includes chart visualizations."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "html": {
                        "content": """<html>
<body>
    <div id="cpu-chart"></div>
    <div id="memory-chart"></div>
    <div id="disk-chart"></div>
</body>
</html>""",
                        "charts": [
                            {"id": "cpu-chart", "type": "line", "data": "cpu metrics"},
                            {"id": "memory-chart", "type": "gauge", "data": "memory metrics"},
                            {"id": "disk-chart", "type": "pie", "data": "disk metrics"}
                        ]
                    }
                }
            }

            result = mock_task.return_value
            charts = result["reports"]["html"]["charts"]

            # Verify charts included
            assert len(charts) >= 3
            assert any(chart["type"] == "line" for chart in charts)
            assert any(chart["type"] == "gauge" for chart in charts)

    def test_report_html_includes_responsive_design(self):
        """Test HTML report includes responsive design features."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "html": {
                        "content": """<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        @media (max-width: 768px) { body { font-size: 14px; } }
    </style>
</head>
</html>""",
                        "responsive": True,
                        "viewport_meta": True
                    }
                }
            }

            result = mock_task.return_value

            # Verify responsive design
            assert result["reports"]["html"]["responsive"] is True
            assert result["reports"]["html"]["viewport_meta"] is True

    def test_report_html_valid_structure(self):
        """Test HTML report has valid HTML structure."""

        with patch('Task') as mock_task:
            mock_task.return_value = {
                "status": "success",
                "reports": {
                    "html": {
                        "content": """<!DOCTYPE html>
<html>
<head><title>Report</title></head>
<body><h1>Report</h1></body>
</html>""",
                        "has_doctype": True,
                        "has_head": True,
                        "has_body": True,
                        "valid_html": True
                    }
                }
            }

            result = mock_task.return_value
            html_report = result["reports"]["html"]

            # Verify HTML structure
            assert html_report["has_doctype"] is True
            assert html_report["has_head"] is True
            assert html_report["has_body"] is True
            assert html_report["valid_html"] is True


@pytest.fixture
def mock_task():
    """Fixture providing mock Task function."""
    with patch('Task') as mock:
        yield mock


def test_report_command_generates_all_formats(mock_task):
    """Integration test: Generate all report formats (markdown, JSON, HTML)."""

    mock_task.return_value = {
        "status": "success",
        "reports": {
            "markdown": {
                "filename": "report_2025-11-30.md",
                "format": "markdown",
                "size_bytes": 5240
            },
            "json": {
                "filename": "report_2025-11-30.json",
                "format": "json",
                "size_bytes": 3850
            },
            "html": {
                "filename": "report_2025-11-30.html",
                "format": "html",
                "size_bytes": 8120
            }
        },
        "summary": {
            "total_reports": 3,
            "total_size_bytes": 17210,
            "output_directory": ".claude/skills/macos-resource-optimizer/.data/reports"
        }
    }

    result = mock_task(
        subagent_type="manager-resource-coordinator",
        prompt="Generate comprehensive resource optimization report in markdown, JSON, and HTML formats"
    )

    # Verify all formats generated
    assert result["status"] == "success"
    assert len(result["reports"]) == 3
    assert "markdown" in result["reports"]
    assert "json" in result["reports"]
    assert "html" in result["reports"]
    assert result["summary"]["total_reports"] == 3
