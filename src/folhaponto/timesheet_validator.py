"""
Timesheet Validator

This module validates employee timesheet data against work rules:
1. Minimum 1 hour lunch break
2. Maximum 8 hours work per day
3. Minimum 11 hours rest between consecutive work days
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd


class TimesheetValidator:
    """Validates timesheet data against work rules."""
    
    def __init__(self):
        self.violations = {}
    
    def validate_timesheet(self, timesheet_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Validate all timesheet entries against work rules.
        
        Args:
            timesheet_data (List[Dict]): List of timesheet entries
            
        Returns:
            Dict[str, List[Dict]]: Dictionary containing violations by type
        """
        self.violations = []
        
        # Sort timesheet data by date
        sorted_data = sorted(timesheet_data, key=lambda x: x['date'])
        
        violations = {
            'lunch_violations': [],
            'daily_hours_violations': [],
            'rest_period_violations': []
        }
        
        for i, entry in enumerate(sorted_data):
            # Validate lunch break
            lunch_violation = self._validate_lunch_break(entry)
            if lunch_violation:
                violations['lunch_violations'].append(lunch_violation)
            
            # Validate daily working hours
            hours_violation = self._validate_daily_hours(entry)
            if hours_violation:
                violations['daily_hours_violations'].append(hours_violation)
            
            # Validate rest period between days (if not the first entry)
            if i > 0:
                rest_violation = self._validate_rest_period(sorted_data[i-1], entry)
                if rest_violation:
                    violations['rest_period_violations'].append(rest_violation)
        
        self.violations = violations
        return violations
    
    def _validate_lunch_break(self, entry: Dict) -> Optional[Dict]:
        """
        Validate that the employee had at least 1 hour lunch break.
        
        Args:
            entry (Dict): Timesheet entry for a single day
            
        Returns:
            Dict: Violation details if lunch break < 1 hour, None otherwise
        """
        try:
            morning_end = entry.get('morning_end')
            afternoon_start = entry.get('afternoon_start')
            
            if not morning_end or not afternoon_start:
                return {
                    'date': entry['date'],
                    'type': 'lunch_break',
                    'description': 'Missing lunch break times',
                    'morning_end': morning_end,
                    'afternoon_start': afternoon_start,
                    'lunch_duration': None
                }
            
            # Calculate lunch break duration
            lunch_duration = self._calculate_time_difference(morning_end, afternoon_start)
            
            if lunch_duration < timedelta(hours=1):
                return {
                    'date': entry['date'],
                    'type': 'lunch_break',
                    'description': f'Lunch break too short: {lunch_duration}',
                    'morning_end': morning_end,
                    'afternoon_start': afternoon_start,
                    'lunch_duration': lunch_duration,
                    'required_duration': timedelta(hours=1)
                }
            
            return None
            
        except Exception as e:
            return {
                'date': entry['date'],
                'type': 'lunch_break',
                'description': f'Error validating lunch break: {e}',
                'morning_end': entry.get('morning_end'),
                'afternoon_start': entry.get('afternoon_start'),
                'lunch_duration': None
            }
    
    def _validate_daily_hours(self, entry: Dict) -> Optional[Dict]:
        """
        Validate that the employee didn't work more than 8 hours per day.
        
        Args:
            entry (Dict): Timesheet entry for a single day
            
        Returns:
            Dict: Violation details if daily hours > 8, None otherwise
        """
        try:
            morning_start = entry.get('morning_start')
            morning_end = entry.get('morning_end')
            afternoon_start = entry.get('afternoon_start')
            afternoon_end = entry.get('afternoon_end')
            
            if not all([morning_start, morning_end, afternoon_start, afternoon_end]):
                return {
                    'date': entry['date'],
                    'type': 'daily_hours',
                    'description': 'Missing time entries for daily hours calculation',
                    'total_hours': None,
                    'times': {
                        'morning_start': morning_start,
                        'morning_end': morning_end,
                        'afternoon_start': afternoon_start,
                        'afternoon_end': afternoon_end
                    }
                }
            
            # Calculate total working hours (we know all times are not None here)
            morning_hours = self._calculate_time_difference(morning_start, morning_end)  # type: ignore
            afternoon_hours = self._calculate_time_difference(afternoon_start, afternoon_end)  # type: ignore
            total_hours = morning_hours + afternoon_hours
            
            if total_hours > timedelta(hours=8):
                return {
                    'date': entry['date'],
                    'type': 'daily_hours',
                    'description': f'Exceeded daily work limit: {total_hours}',
                    'total_hours': total_hours,
                    'morning_hours': morning_hours,
                    'afternoon_hours': afternoon_hours,
                    'max_allowed': timedelta(hours=8),
                    'times': {
                        'morning_start': morning_start,
                        'morning_end': morning_end,
                        'afternoon_start': afternoon_start,
                        'afternoon_end': afternoon_end
                    }
                }
            
            return None
            
        except Exception as e:
            return {
                'date': entry['date'],
                'type': 'daily_hours',
                'description': f'Error validating daily hours: {e}',
                'total_hours': None
            }
    
    def _validate_rest_period(self, previous_entry: Dict, current_entry: Dict) -> Optional[Dict]:
        """
        Validate that the employee had at least 11 hours rest between consecutive work days.
        
        Args:
            previous_entry (Dict): Previous day's timesheet entry
            current_entry (Dict): Current day's timesheet entry
            
        Returns:
            Dict: Violation details if rest period < 11 hours, None otherwise
        """
        try:
            previous_end = previous_entry.get('afternoon_end')
            current_start = current_entry.get('morning_start')
            
            if not previous_end or not current_start:
                return {
                    'previous_date': previous_entry['date'],
                    'current_date': current_entry['date'],
                    'type': 'rest_period',
                    'description': 'Missing times for rest period calculation',
                    'previous_end': previous_end,
                    'current_start': current_start,
                    'rest_duration': None
                }
            
            # Calculate rest period between days
            previous_datetime = datetime.combine(previous_entry['date'], previous_end)
            current_datetime = datetime.combine(current_entry['date'], current_start)
            
            rest_duration = current_datetime - previous_datetime
            
            if rest_duration < timedelta(hours=11):
                return {
                    'previous_date': previous_entry['date'],
                    'current_date': current_entry['date'],
                    'type': 'rest_period',
                    'description': f'Insufficient rest period: {rest_duration}',
                    'previous_end': previous_end,
                    'current_start': current_start,
                    'rest_duration': rest_duration,
                    'required_duration': timedelta(hours=11)
                }
            
            return None
            
        except Exception as e:
            return {
                'previous_date': previous_entry['date'],
                'current_date': current_entry['date'],
                'type': 'rest_period',
                'description': f'Error validating rest period: {e}',
                'rest_duration': None
            }
    
    def _calculate_time_difference(self, start_time: time, end_time: time) -> timedelta:
        """
        Calculate time difference between two time objects.
        
        Args:
            start_time (time): Start time
            end_time (time): End time
            
        Returns:
            timedelta: Time difference
        """
        start_datetime = datetime.combine(datetime.min, start_time)
        end_datetime = datetime.combine(datetime.min, end_time)
        
        # Handle case where end time is on the next day
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)
        
        return end_datetime - start_datetime
    
    def get_violation_summary(self) -> Dict[str, int]:
        """
        Get a summary of violations by type.
        
        Returns:
            Dict[str, int]: Count of violations by type
        """
        if not self.violations:
            return {}
        
        return {
            'lunch_violations': len(self.violations.get('lunch_violations', [])),
            'daily_hours_violations': len(self.violations.get('daily_hours_violations', [])),
            'rest_period_violations': len(self.violations.get('rest_period_violations', []))
        }
    
    def get_all_violations(self) -> List[Dict]:
        """
        Get all violations as a flat list.
        
        Returns:
            List[Dict]: All violations
        """
        all_violations = []
        if self.violations:
            for violation_type, violations in self.violations.items():
                all_violations.extend(violations)
        return all_violations
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert violations to a pandas DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame with violation data
        """
        all_violations = self.get_all_violations()
        if not all_violations:
            return pd.DataFrame()
        
        # Flatten violations for DataFrame
        df_data = []
        for violation in all_violations:
            row_data = {
                'date': violation.get('date') or violation.get('current_date'),
                'type': violation.get('type'),
                'description': violation.get('description'),
                'violation_details': str(violation)
            }
            
            # Add specific fields based on violation type
            if violation.get('type') == 'lunch_break':
                row_data['lunch_duration'] = str(violation.get('lunch_duration', ''))
            elif violation.get('type') == 'daily_hours':
                row_data['total_hours'] = str(violation.get('total_hours', ''))
            elif violation.get('type') == 'rest_period':
                row_data['rest_duration'] = str(violation.get('rest_duration', ''))
                row_data['previous_date'] = violation.get('previous_date')
            
            df_data.append(row_data)
        
        return pd.DataFrame(df_data)


def main():
    """Example usage of the TimesheetValidator."""
    # Example timesheet data (would come from pdf_extractor.py)
    sample_data = [
        {
            'date': datetime(2025, 1, 15).date(),
            'morning_start': time(8, 0),
            'morning_end': time(12, 0),
            'afternoon_start': time(12, 30),  # Only 30 minutes lunch
            'afternoon_end': time(18, 0)
        },
        {
            'date': datetime(2025, 1, 16).date(),
            'morning_start': time(7, 30),  # Too close to previous day
            'morning_end': time(12, 0),
            'afternoon_start': time(13, 0),
            'afternoon_end': time(19, 0)  # More than 8 hours
        }
    ]
    
    validator = TimesheetValidator()
    violations = validator.validate_timesheet(sample_data)
    
    print("Validation Results:")
    print(f"Lunch violations: {len(violations['lunch_violations'])}")
    print(f"Daily hours violations: {len(violations['daily_hours_violations'])}")
    print(f"Rest period violations: {len(violations['rest_period_violations'])}")
    
    # Print detailed violations
    for violation_type, violation_list in violations.items():
        if violation_list:
            print(f"\n{violation_type.replace('_', ' ').title()}:")
            for violation in violation_list:
                print(f"  - {violation['description']}")


if __name__ == "__main__":
    main()
