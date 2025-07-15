# FolhaPonto - Employee Timesheet Analysis

A comprehensive Python application for extracting, validating, and reporting on employee timesheet data from PDF files. This tool helps ensure compliance with labor regulations including lunch breaks, daily work hours, and rest periods between work days.

## Features

### 🔍 PDF Data Extraction
- Extract timesheet tables from PDF files using PyMuPDF
- Parse dates, times, and work schedules automatically
- Handle various PDF timesheet formats
- Export extracted data to CSV format

### ✅ Work Rules Validation
- **Lunch Break Rule**: Validate minimum 1-hour lunch break
- **Daily Hours Rule**: Ensure employees don't work more than 8 hours per day
- **Rest Period Rule**: Verify minimum 11 hours rest between consecutive work days
- Detailed violation tracking with timestamps

### 📊 Comprehensive Reporting
- Generate detailed violation reports in multiple formats (JSON, CSV, TXT)
- Daily compliance summary
- Violation severity classification (low, medium, high)
- Compliance rate calculation
- Actionable recommendations for improvement

## Installation

Since you're using `uv`, install the dependencies with:

```bash
uv pip install PyMuPDF pandas
```

Or install from requirements.txt:

```bash
uv pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```bash
python main.py
```

This will process the default sample file: `test_sample/Ficha Ponto Simplificada André Luis.pdf`

### Custom PDF File

```bash
python main.py "path/to/your/timesheet.pdf"
```

### Specify Output Directory

```bash
python main.py "your_timesheet.pdf" --output-dir "custom_reports"
```

### Verbose Output

```bash
python main.py --verbose
```

## Module Usage

### 1. PDF Extraction (`pdf_extractor.py`)

```python
from src.folhaponto import TimesheetExtractor

# Extract timesheet data from PDF
extractor = TimesheetExtractor()
timesheet_data = extractor.extract_from_pdf("timesheet.pdf")

# Convert to DataFrame
df = extractor.to_dataframe()

# Save to CSV
extractor.save_to_csv("extracted_data.csv")
```

### 2. Validation (`timesheet_validator.py`)

```python
from src.folhaponto import TimesheetValidator

# Validate timesheet data
validator = TimesheetValidator()
violations = validator.validate_timesheet(timesheet_data)

# Get violation summary
summary = validator.get_violation_summary()
print(f"Total violations: {sum(summary.values())}")
```

### 3. Report Generation (`report_generator.py`)

```python
from src.folhaponto import TimesheetReportGenerator

# Generate complete report
generator = TimesheetReportGenerator()
report = generator.generate_full_report("timesheet.pdf", "reports")

# Access report data
compliance_rate = report['metadata']['compliance_rate']
print(f"Compliance Rate: {compliance_rate}%")
```

## Work Rules Validated

### 1. Lunch Break Rule
- **Requirement**: Minimum 1 hour lunch break
- **Validation**: Checks time between morning end and afternoon start
- **Violation**: When lunch break < 60 minutes

### 2. Daily Hours Rule
- **Requirement**: Maximum 8 hours work per day
- **Validation**: Sums morning and afternoon working hours
- **Violation**: When total daily hours > 8 hours

### 3. Rest Period Rule
- **Requirement**: Minimum 11 hours rest between consecutive work days
- **Validation**: Checks time from previous day end to current day start
- **Violation**: When rest period < 11 hours

## Report Outputs

The application generates several report files:

### 1. `timesheet_report.json`
Complete report data in JSON format with:
- Metadata and statistics
- Detailed violations
- Daily summary
- Recommendations

### 2. `daily_summary.csv`
Day-by-day breakdown with:
- Date and times
- Violation count
- Compliance status

### 3. `violations.csv`
Detailed violation list with:
- Date and type
- Severity level
- Description and details

### 4. `timesheet_report.txt`
Human-readable report with:
- Executive summary
- Violation details
- Recommendations

## Project Structure

```
FolhaPonto/
├── src/
│   └── folhaponto/
│       ├── __init__.py              # Package initialization
│       ├── pdf_extractor.py         # PDF data extraction
│       ├── timesheet_validator.py   # Work rules validation
│       └── report_generator.py      # Report generation
├── test_sample/                     # Sample PDF files
├── tests/                          # Unit tests
├── main.py                         # Main application script
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Sample Output

```
EMPLOYEE TIMESHEET ANALYSIS
============================================================
Processing: test_sample/Ficha Ponto Simplificada André Luis.pdf
Output directory: reports

Step 1: Extracting timesheet data from PDF...
✅ Successfully extracted 22 timesheet entries

Step 2: Validating timesheet data against work rules...
✅ Validation complete. Found 3 violations
   • Lunch break violations: 1
   • Daily hours violations: 2
   • Rest period violations: 0

Step 3: Generating comprehensive reports...
✅ Reports generated successfully!

ANALYSIS SUMMARY
============================================================
Analysis Period: 2025-01-01 to 2025-01-31
Days Analyzed: 22
Total Violations: 3
Compliance Rate: 86.4%
🟡 GOOD COMPLIANCE - Some improvements needed
```

## Error Handling

The application includes comprehensive error handling for:
- Invalid or corrupted PDF files
- Missing timesheet data
- Malformed time entries
- File system errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information