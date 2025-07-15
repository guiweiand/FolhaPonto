"""
FolhaPonto - Employee Timesheet Analysis Package

This package provides tools for extracting, validating, and reporting on
employee timesheet data from PDF files.

Main modules:
- pdf_extractor: Extract timesheet data from PDF files using PyMuPDF
- timesheet_validator: Validate timesheet data against work rules
- report_generator: Generate comprehensive violation reports
"""

from .pdf_extractor import TimesheetExtractor
from .timesheet_validator import TimesheetValidator
from .report_generator import TimesheetReportGenerator

__version__ = "1.0.0"
__author__ = "FolhaPonto Team"

__all__ = [
    "TimesheetExtractor",
    "TimesheetValidator", 
    "TimesheetReportGenerator"
]
