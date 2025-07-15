"""
Timesheet Report Generator

This module generates comprehensive reports of work rule violations
found in employee timesheet data.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from pathlib import Path
import json

from .pdf_extractor import TimesheetExtractor
from .timesheet_validator import TimesheetValidator


class TimesheetReportGenerator:
    """Generates reports for timesheet violations."""
    
    def __init__(self):
        self.extractor = TimesheetExtractor()
        self.validator = TimesheetValidator()
        self.report_data = {}
    
    def generate_full_report(self, pdf_path: str, output_dir: str = "reports") -> Dict:
        """
        Generate a complete report from PDF extraction through violation reporting.
        
        Args:
            pdf_path (str): Path to the PDF timesheet file
            output_dir (str): Directory to save report files
            
        Returns:
            Dict: Complete report data
        """
        # Ensure output directory exists
        Path(output_dir).mkdir(exist_ok=True)
        
        # Extract timesheet data from PDF
        print("Extracting timesheet data from PDF...")
        timesheet_data = self.extractor.extract_from_pdf(pdf_path)
        
        if not timesheet_data:
            print("No timesheet data found in PDF")
            return {'error': 'No timesheet data found'}
        
        print(f"Extracted {len(timesheet_data)} timesheet entries")
        
        # Validate timesheet data
        print("Validating timesheet data...")
        violations = self.validator.validate_timesheet(timesheet_data)
        
        # Generate comprehensive report
        report_data = self._generate_report_data(timesheet_data, violations)
        
        # Save reports in multiple formats
        self._save_reports(report_data, output_dir)
        
        self.report_data = report_data
        return report_data
    
    def _generate_report_data(self, timesheet_data: List[Dict], violations: Dict[str, List[Dict]]) -> Dict:
        """
        Generate comprehensive report data structure.
        
        Args:
            timesheet_data (List[Dict]): Original timesheet data
            violations (Dict): Violations by type
            
        Returns:
            Dict: Complete report data
        """
        # Basic statistics
        total_days = len(timesheet_data)
        total_violations = sum(len(v) for v in violations.values())
        
        # Calculate date range
        dates = [entry['date'] for entry in timesheet_data if entry.get('date')]
        date_range = {
            'start_date': min(dates) if dates else None,
            'end_date': max(dates) if dates else None
        }
        
        # Violation statistics
        violation_stats = {
            'lunch_break_violations': len(violations.get('lunch_violations', [])),
            'daily_hours_violations': len(violations.get('daily_hours_violations', [])),
            'rest_period_violations': len(violations.get('rest_period_violations', []))
        }
        
        # Compliance rate
        compliance_rate = (total_days - total_violations) / total_days * 100 if total_days > 0 else 0
        
        # Generate detailed violation reports
        detailed_violations = self._generate_detailed_violations(violations)
        
        # Generate summary by date
        daily_summary = self._generate_daily_summary(timesheet_data, violations)
        
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_days_analyzed': total_days,
                'date_range': date_range,
                'total_violations': total_violations,
                'compliance_rate': round(compliance_rate, 2)
            },
            'violation_statistics': violation_stats,
            'detailed_violations': detailed_violations,
            'daily_summary': daily_summary,
            'recommendations': self._generate_recommendations(violation_stats)
        }
        
        return report_data
    
    def _generate_detailed_violations(self, violations: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Generate detailed violation reports with human-readable descriptions.
        
        Args:
            violations (Dict): Raw violations data
            
        Returns:
            Dict: Detailed violation reports
        """
        detailed = {}
        
        for violation_type, violation_list in violations.items():
            detailed[violation_type] = []
            
            for violation in violation_list:
                detailed_violation = {
                    'date': violation.get('date') or violation.get('current_date'),
                    'type': violation.get('type'),
                    'description': violation.get('description'),
                    'severity': self._determine_severity(violation),
                    'details': {}
                }
                
                # Add specific details based on violation type
                if violation.get('type') == 'lunch_break':
                    lunch_duration = violation.get('lunch_duration')
                    detailed_violation['details'] = {
                        'morning_end': str(violation.get('morning_end', '')),
                        'afternoon_start': str(violation.get('afternoon_start', '')),
                        'actual_lunch_duration': str(lunch_duration) if lunch_duration else 'Unknown',
                        'required_duration': '1:00:00',
                        'shortage': str(timedelta(hours=1) - lunch_duration) if lunch_duration else 'Unknown'
                    }
                
                elif violation.get('type') == 'daily_hours':
                    total_hours = violation.get('total_hours')
                    detailed_violation['details'] = {
                        'morning_start': str(violation.get('times', {}).get('morning_start', '')),
                        'morning_end': str(violation.get('times', {}).get('morning_end', '')),
                        'afternoon_start': str(violation.get('times', {}).get('afternoon_start', '')),
                        'afternoon_end': str(violation.get('times', {}).get('afternoon_end', '')),
                        'total_hours_worked': str(total_hours) if total_hours else 'Unknown',
                        'max_allowed_hours': '8:00:00',
                        'excess_hours': str(total_hours - timedelta(hours=8)) if total_hours else 'Unknown'
                    }
                
                elif violation.get('type') == 'rest_period':
                    rest_duration = violation.get('rest_duration')
                    detailed_violation['details'] = {
                        'previous_date': str(violation.get('previous_date', '')),
                        'previous_end_time': str(violation.get('previous_end', '')),
                        'current_start_time': str(violation.get('current_start', '')),
                        'actual_rest_duration': str(rest_duration) if rest_duration else 'Unknown',
                        'required_duration': '11:00:00',
                        'shortage': str(timedelta(hours=11) - rest_duration) if rest_duration else 'Unknown'
                    }
                
                detailed[violation_type].append(detailed_violation)
        
        return detailed
    
    def _determine_severity(self, violation: Dict) -> str:
        """
        Determine the severity level of a violation.
        
        Args:
            violation (Dict): Violation data
            
        Returns:
            str: Severity level (low, medium, high)
        """
        violation_type = violation.get('type')
        
        if violation_type == 'lunch_break':
            lunch_duration = violation.get('lunch_duration')
            if lunch_duration and lunch_duration < timedelta(minutes=30):
                return 'high'
            elif lunch_duration and lunch_duration < timedelta(minutes=45):
                return 'medium'
            else:
                return 'low'
        
        elif violation_type == 'daily_hours':
            total_hours = violation.get('total_hours')
            if total_hours and total_hours > timedelta(hours=10):
                return 'high'
            elif total_hours and total_hours > timedelta(hours=9):
                return 'medium'
            else:
                return 'low'
        
        elif violation_type == 'rest_period':
            rest_duration = violation.get('rest_duration')
            if rest_duration and rest_duration < timedelta(hours=8):
                return 'high'
            elif rest_duration and rest_duration < timedelta(hours=10):
                return 'medium'
            else:
                return 'low'
        
        return 'medium'
    
    def _generate_daily_summary(self, timesheet_data: List[Dict], violations: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Generate a day-by-day summary of timesheet data and violations.
        
        Args:
            timesheet_data (List[Dict]): Original timesheet data
            violations (Dict): Violations by type
            
        Returns:
            List[Dict]: Daily summary data
        """
        # Create a map of violations by date
        violations_by_date = {}
        
        for violation_type, violation_list in violations.items():
            for violation in violation_list:
                date = violation.get('date') or violation.get('current_date')
                if date:
                    if date not in violations_by_date:
                        violations_by_date[date] = []
                    violations_by_date[date].append({
                        'type': violation_type,
                        'violation': violation
                    })
        
        # Generate daily summary
        daily_summary = []
        for entry in sorted(timesheet_data, key=lambda x: x.get('date', datetime.min.date())):
            date = entry.get('date')
            day_violations = violations_by_date.get(date, [])
            
            summary = {
                'date': str(date),
                'times': {
                    'morning_start': str(entry.get('morning_start', '')),
                    'morning_end': str(entry.get('morning_end', '')),
                    'afternoon_start': str(entry.get('afternoon_start', '')),
                    'afternoon_end': str(entry.get('afternoon_end', ''))
                },
                'violations_count': len(day_violations),
                'violations': [v['type'] for v in day_violations],
                'compliance_status': 'compliant' if not day_violations else 'non-compliant',
                'raw_text': entry.get('raw_text', '')
            }
            
            daily_summary.append(summary)
        
        return daily_summary
    
    def _generate_recommendations(self, violation_stats: Dict[str, int]) -> List[str]:
        """
        Generate recommendations based on violation patterns.
        
        Args:
            violation_stats (Dict): Violation statistics
            
        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        
        if violation_stats.get('lunch_break_violations', 0) > 0:
            recommendations.append(
                "Ensure employees take a minimum 1-hour lunch break each day. "
                "Consider implementing automated reminders or blocking work systems during lunch hours."
            )
        
        if violation_stats.get('daily_hours_violations', 0) > 0:
            recommendations.append(
                "Monitor daily working hours to prevent employees from exceeding the 8-hour limit. "
                "Implement overtime approval processes and workload management."
            )
        
        if violation_stats.get('rest_period_violations', 0) > 0:
            recommendations.append(
                "Ensure employees have at least 11 hours of rest between consecutive work days. "
                "Review scheduling practices and avoid back-to-back late/early shifts."
            )
        
        if sum(violation_stats.values()) == 0:
            recommendations.append(
                "Excellent compliance! All work rules are being followed properly. "
                "Continue monitoring to maintain these standards."
            )
        
        return recommendations
    
    def _save_reports(self, report_data: Dict, output_dir: str) -> None:
        """
        Save reports in multiple formats.
        
        Args:
            report_data (Dict): Report data to save
            output_dir (str): Output directory
        """
        output_path = Path(output_dir)
        
        # Save JSON report
        json_path = output_path / "timesheet_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        print(f"JSON report saved to {json_path}")
        
        # Save CSV reports
        self._save_csv_reports(report_data, output_path)
        
        # Save human-readable text report
        self._save_text_report(report_data, output_path)
    
    def _save_csv_reports(self, report_data: Dict, output_path: Path) -> None:
        """Save CSV format reports."""
        # Daily summary CSV
        daily_df = pd.DataFrame(report_data['daily_summary'])
        daily_csv_path = output_path / "daily_summary.csv"
        daily_df.to_csv(daily_csv_path, index=False)
        print(f"Daily summary CSV saved to {daily_csv_path}")
        
        # Violations CSV
        violations_data = []
        for violation_type, violation_list in report_data['detailed_violations'].items():
            for violation in violation_list:
                violations_data.append({
                    'date': violation['date'],
                    'type': violation['type'],
                    'severity': violation['severity'],
                    'description': violation['description'],
                    'details': str(violation['details'])
                })
        
        if violations_data:
            violations_df = pd.DataFrame(violations_data)
            violations_csv_path = output_path / "violations.csv"
            violations_df.to_csv(violations_csv_path, index=False)
            print(f"Violations CSV saved to {violations_csv_path}")
    
    def _save_text_report(self, report_data: Dict, output_path: Path) -> None:
        """Save human-readable text report."""
        text_path = output_path / "timesheet_report.txt"
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write("TIMESHEET COMPLIANCE REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Metadata
            metadata = report_data['metadata']
            f.write(f"Report Generated: {metadata['generated_at']}\n")
            f.write(f"Analysis Period: {metadata['date_range']['start_date']} to {metadata['date_range']['end_date']}\n")
            f.write(f"Total Days Analyzed: {metadata['total_days_analyzed']}\n")
            f.write(f"Total Violations: {metadata['total_violations']}\n")
            f.write(f"Compliance Rate: {metadata['compliance_rate']}%\n\n")
            
            # Violation Statistics
            f.write("VIOLATION SUMMARY\n")
            f.write("-" * 20 + "\n")
            stats = report_data['violation_statistics']
            f.write(f"Lunch Break Violations: {stats['lunch_break_violations']}\n")
            f.write(f"Daily Hours Violations: {stats['daily_hours_violations']}\n")
            f.write(f"Rest Period Violations: {stats['rest_period_violations']}\n\n")
            
            # Detailed Violations
            f.write("DETAILED VIOLATIONS\n")
            f.write("-" * 20 + "\n")
            for violation_type, violation_list in report_data['detailed_violations'].items():
                if violation_list:
                    f.write(f"\n{violation_type.replace('_', ' ').title()}:\n")
                    for violation in violation_list:
                        f.write(f"  • {violation['date']}: {violation['description']} (Severity: {violation['severity']})\n")
            
            # Recommendations
            f.write("\nRECOMMENDATIONS\n")
            f.write("-" * 15 + "\n")
            for i, rec in enumerate(report_data['recommendations'], 1):
                f.write(f"{i}. {rec}\n\n")
        
        print(f"Text report saved to {text_path}")


def main():
    """Example usage of the TimesheetReportGenerator."""
    generator = TimesheetReportGenerator()
    
    # Generate full report from PDF
    pdf_path = "test_sample/Ficha Ponto Simplificada André Luis.pdf"
    report = generator.generate_full_report(pdf_path)
    
    if 'error' not in report:
        print("\nReport Summary:")
        print(f"Compliance Rate: {report['metadata']['compliance_rate']}%")
        print(f"Total Violations: {report['metadata']['total_violations']}")
        
        violation_stats = report['violation_statistics']
        print(f"Lunch Break Violations: {violation_stats['lunch_break_violations']}")
        print(f"Daily Hours Violations: {violation_stats['daily_hours_violations']}")
        print(f"Rest Period Violations: {violation_stats['rest_period_violations']}")


if __name__ == "__main__":
    main()
