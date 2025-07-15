"""
Basic tests for the FolhaPonto timesheet analysis package.

Run with: python -m pytest tests/ -v
"""

import unittest
from datetime import datetime, time, timedelta
from pathlib import Path

from src.folhaponto import TimesheetExtractor, TimesheetValidator, TimesheetReportGenerator


class TestTimesheetExtractor(unittest.TestCase):
    """Test cases for TimesheetExtractor."""
    
    def setUp(self):
        self.extractor = TimesheetExtractor()
    
    def test_extractor_initialization(self):
        """Test that extractor initializes correctly."""
        self.assertEqual(len(self.extractor.timesheet_data), 0)
    
    def test_to_dataframe_empty(self):
        """Test DataFrame creation with empty data."""
        df = self.extractor.to_dataframe()
        self.assertTrue(df.empty)


class TestTimesheetValidator(unittest.TestCase):
    """Test cases for TimesheetValidator."""
    
    def setUp(self):
        self.validator = TimesheetValidator()
    
    def test_validator_initialization(self):
        """Test that validator initializes correctly."""
        self.assertEqual(self.validator.violations, {})
    
    def test_lunch_break_validation_pass(self):
        """Test lunch break validation with compliant data."""
        entry = {
            'date': datetime(2025, 1, 15).date(),
            'morning_start': time(8, 0),
            'morning_end': time(12, 0),
            'afternoon_start': time(13, 0),  # 1 hour lunch
            'afternoon_end': time(17, 0)
        }
        
        violation = self.validator._validate_lunch_break(entry)
        self.assertIsNone(violation)
    
    def test_lunch_break_validation_fail(self):
        """Test lunch break validation with non-compliant data."""
        entry = {
            'date': datetime(2025, 1, 15).date(),
            'morning_start': time(8, 0),
            'morning_end': time(12, 0),
            'afternoon_start': time(12, 30),  # Only 30 minutes lunch
            'afternoon_end': time(17, 0)
        }
        
        violation = self.validator._validate_lunch_break(entry)
        self.assertIsNotNone(violation)
        self.assertEqual(violation['type'], 'lunch_break')
    
    def test_daily_hours_validation_pass(self):
        """Test daily hours validation with compliant data."""
        entry = {
            'date': datetime(2025, 1, 15).date(),
            'morning_start': time(8, 0),
            'morning_end': time(12, 0),      # 4 hours
            'afternoon_start': time(13, 0),
            'afternoon_end': time(17, 0)     # 4 hours = 8 total
        }
        
        violation = self.validator._validate_daily_hours(entry)
        self.assertIsNone(violation)
    
    def test_daily_hours_validation_fail(self):
        """Test daily hours validation with non-compliant data."""
        entry = {
            'date': datetime(2025, 1, 15).date(),
            'morning_start': time(7, 0),
            'morning_end': time(12, 0),      # 5 hours
            'afternoon_start': time(13, 0),
            'afternoon_end': time(18, 0)     # 5 hours = 10 total
        }
        
        violation = self.validator._validate_daily_hours(entry)
        self.assertIsNotNone(violation)
        self.assertEqual(violation['type'], 'daily_hours')
    
    def test_calculate_time_difference(self):
        """Test time difference calculation."""
        start = time(8, 0)
        end = time(17, 0)
        
        diff = self.validator._calculate_time_difference(start, end)
        self.assertEqual(diff, timedelta(hours=9))


class TestTimesheetReportGenerator(unittest.TestCase):
    """Test cases for TimesheetReportGenerator."""
    
    def setUp(self):
        self.generator = TimesheetReportGenerator()
    
    def test_generator_initialization(self):
        """Test that generator initializes correctly."""
        self.assertIsInstance(self.generator.extractor, TimesheetExtractor)
        self.assertIsInstance(self.generator.validator, TimesheetValidator)
        self.assertEqual(self.generator.report_data, {})
    
    def test_severity_determination(self):
        """Test violation severity determination."""
        # High severity lunch violation
        violation = {
            'type': 'lunch_break',
            'lunch_duration': timedelta(minutes=15)
        }
        severity = self.generator._determine_severity(violation)
        self.assertEqual(severity, 'high')
        
        # Medium severity lunch violation
        violation = {
            'type': 'lunch_break',
            'lunch_duration': timedelta(minutes=40)
        }
        severity = self.generator._determine_severity(violation)
        self.assertEqual(severity, 'medium')


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    def test_sample_data_workflow(self):
        """Test the complete workflow with sample data."""
        # Sample timesheet data
        sample_data = [
            {
                'date': datetime(2025, 1, 15).date(),
                'morning_start': time(8, 0),
                'morning_end': time(12, 0),
                'afternoon_start': time(13, 0),
                'afternoon_end': time(17, 0),
                'raw_text': '15/01/2025 08:00 12:00 13:00 17:00'
            },
            {
                'date': datetime(2025, 1, 16).date(),
                'morning_start': time(8, 0),
                'morning_end': time(12, 0),
                'afternoon_start': time(12, 30),  # Short lunch
                'afternoon_end': time(18, 0),     # Long day
                'raw_text': '16/01/2025 08:00 12:00 12:30 18:00'
            }
        ]
        
        # Validate the data
        validator = TimesheetValidator()
        violations = validator.validate_timesheet(sample_data)
        
        # Should have violations
        self.assertGreater(len(violations['lunch_violations']), 0)
        self.assertGreater(len(violations['daily_hours_violations']), 0)
        
        # Generate report data
        generator = TimesheetReportGenerator()
        report_data = generator._generate_report_data(sample_data, violations)
        
        # Verify report structure
        self.assertIn('metadata', report_data)
        self.assertIn('violation_statistics', report_data)
        self.assertIn('detailed_violations', report_data)
        self.assertIn('daily_summary', report_data)
        self.assertIn('recommendations', report_data)
        
        # Check compliance rate
        compliance_rate = report_data['metadata']['compliance_rate']
        self.assertLess(compliance_rate, 100)  # Should have violations


if __name__ == '__main__':
    unittest.main()
