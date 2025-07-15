#!/usr/bin/env python3
"""
Main script for processing employee timesheet PDFs

This script demonstrates the complete workflow:
1. Extract timesheet data from PDF using PyMuPDF
2. Validate the data against work rules
3. Generate comprehensive reports of violations

Usage:
    python main.py [pdf_path] [output_dir]
    
    pdf_path: Path to the PDF timesheet file (default: test_sample/Ficha Ponto Simplificada André Luis.pdf)
    output_dir: Directory to save reports (default: reports)
"""

import sys
import argparse
from pathlib import Path

from src.folhaponto import TimesheetExtractor, TimesheetValidator, TimesheetReportGenerator


def main():
    """Main function to process timesheet PDF and generate reports."""
    parser = argparse.ArgumentParser(description="Process employee timesheet PDF and generate compliance reports")
    parser.add_argument("pdf_path", nargs="?", 
                       default="test_sample/Ficha_Ponto_Simplificada_André_Luis.pdf",
                       help="Path to the PDF timesheet file")
    parser.add_argument("--output-dir", "-o", 
                       default="reports",
                       help="Directory to save reports (default: reports)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("EMPLOYEE TIMESHEET ANALYSIS")
    print("=" * 60)
    print(f"Processing: {pdf_path}")
    print(f"Output directory: {args.output_dir}")
    print()
    
    try:
        # Step 1: Extract timesheet data from PDF
        print("Step 1: Extracting timesheet data from PDF...")
        extractor = TimesheetExtractor()
        timesheet_data = extractor.extract_from_pdf(str(pdf_path))
        
        if not timesheet_data:
            print("❌ No timesheet data found in the PDF file.")
            print("Please check if the PDF contains timesheet tables with dates and times.")
            sys.exit(1)
        
        print(f"✅ Successfully extracted {len(timesheet_data)} timesheet entries")
        
        if args.verbose:
            print("\nExtracted entries:")
            for i, entry in enumerate(timesheet_data[:5], 1):  # Show first 5 entries
                print(f"  {i}. {entry['date']}: {entry.get('raw_text', 'No raw text')[:50]}...")
            if len(timesheet_data) > 5:
                print(f"  ... and {len(timesheet_data) - 5} more entries")
        
        # Step 2: Validate timesheet data
        print("\nStep 2: Validating timesheet data against work rules...")
        validator = TimesheetValidator()
        violations = validator.validate_timesheet(timesheet_data)
        
        total_violations = sum(len(v) for v in violations.values())
        print(f"✅ Validation complete. Found {total_violations} violations")
        
        # Show violation summary
        violation_stats = validator.get_violation_summary()
        print(f"   • Lunch break violations: {violation_stats.get('lunch_violations', 0)}")
        print(f"   • Daily hours violations: {violation_stats.get('daily_hours_violations', 0)}")
        print(f"   • Rest period violations: {violation_stats.get('rest_period_violations', 0)}")
        
        if args.verbose and total_violations > 0:
            print("\nSample violations:")
            all_violations = validator.get_all_violations()
            for violation in all_violations[:3]:  # Show first 3 violations
                print(f"   • {violation.get('date', 'Unknown date')}: {violation.get('description', 'No description')}")
            if len(all_violations) > 3:
                print(f"   ... and {len(all_violations) - 3} more violations")
        
        # Step 3: Generate comprehensive reports
        print("\nStep 3: Generating comprehensive reports...")
        generator = TimesheetReportGenerator()
        
        # Use the already extracted data and violations to avoid re-processing
        generator.extractor.timesheet_data = timesheet_data
        generator.validator.violations = violations
        
        # Generate report data
        report_data = generator._generate_report_data(timesheet_data, violations)
        
        # Save reports
        generator._save_reports(report_data, args.output_dir)
        
        print("✅ Reports generated successfully!")
        
        # Display summary
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        
        metadata = report_data['metadata']
        print(f"Analysis Period: {metadata['date_range']['start_date']} to {metadata['date_range']['end_date']}")
        print(f"Days Analyzed: {metadata['total_days_analyzed']}")
        print(f"Total Violations: {metadata['total_violations']}")
        print(f"Compliance Rate: {metadata['compliance_rate']}%")
        
        # Compliance status
        if metadata['compliance_rate'] >= 95:
            print("🟢 EXCELLENT COMPLIANCE")
        elif metadata['compliance_rate'] >= 80:
            print("🟡 GOOD COMPLIANCE - Some improvements needed")
        elif metadata['compliance_rate'] >= 60:
            print("🟠 MODERATE COMPLIANCE - Attention required")
        else:
            print("🔴 POOR COMPLIANCE - Immediate action needed")
        
        print(f"\nReports saved to: {Path(args.output_dir).absolute()}")
        print("Files generated:")
        print("  • timesheet_report.json - Complete report data")
        print("  • daily_summary.csv - Day-by-day summary")
        print("  • violations.csv - Detailed violations")
        print("  • timesheet_report.txt - Human-readable report")
        
        # Show recommendations
        if report_data['recommendations']:
            print("\nRECOMMENDATIONS:")
            for i, rec in enumerate(report_data['recommendations'], 1):
                print(f"  {i}. {rec}")
        
    except Exception as e:
        print(f"❌ Error processing timesheet: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
