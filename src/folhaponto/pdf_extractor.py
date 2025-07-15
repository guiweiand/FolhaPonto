"""
PDF Timesheet Extractor using PyMuPDF

This module extracts employee timesheet data from PDF files containing timesheet tables.
It uses PyMuPDF (fitz) to parse PDF content and extract structured timesheet data.
"""

import fitz  # PyMuPDF
import re
from datetime import datetime, time
from typing import List, Dict, Optional, Tuple
import pandas as pd


class TimesheetExtractor:
    """Extracts timesheet data from PDF files using PyMuPDF."""
    
    def __init__(self):
        self.timesheet_data = []
    
    def extract_from_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Extract timesheet data from a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            List[Dict]: List of dictionaries containing timesheet entries
        """
        try:
            doc = fitz.open(pdf_path)
            self.timesheet_data = []
            
            for page in doc:
                tabs = page.find_tables()

                for tab in tabs.tables:
                    print(tab.to_pandas())
                
                # # Extract tables from the page
                # tables = self._extract_tables_from_text(text)
                
                # # Process each table to extract timesheet entries
                # for table in tables:
                #     entries = self._parse_timesheet_table(table)
                #     self.timesheet_data.extend(entries)
            
            doc.close()
            return self.timesheet_data
            
        except Exception as e:
            print(f"Error extracting data from PDF: {e}")
            return []
    
    def _extract_tables_from_text(self, text: str) -> List[List[str]]:
        """
        Extract table-like structures from PDF text.
        
        Args:
            text (str): Raw text from PDF page
            
        Returns:
            List[List[str]]: List of table rows, each row is a list of cells
        """
        lines = text.split('\n')
        tables = []
        current_table = []
        
        # Pattern to identify timesheet rows (date + time entries)
        time_pattern = r'\d{1,2}:\d{2}'
        date_pattern = r'\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{1,2}'
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_table:
                    tables.append(current_table)
                    current_table = []
                continue
            
            # Check if line contains timesheet data
            if re.search(date_pattern, line) and re.search(time_pattern, line):
                # Split line into cells (assuming spaces/tabs separate columns)
                cells = re.split(r'\s{2,}|\t', line)
                current_table.append(cells)
            elif current_table and re.search(time_pattern, line):
                # Continuation of timesheet data
                cells = re.split(r'\s{2,}|\t', line)
                current_table.append(cells)
        
        if current_table:
            tables.append(current_table)
        
        return tables
    
    def _parse_timesheet_table(self, table: List[List[str]]) -> List[Dict]:
        """
        Parse a timesheet table and extract structured data.
        
        Args:
            table (List[List[str]]): Table rows as lists of cells
            
        Returns:
            List[Dict]: List of timesheet entries
        """
        entries = []
        
        for row in table:
            entry = self._parse_timesheet_row(row)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_timesheet_row(self, row: List[str]) -> Optional[Dict]:
        """
        Parse a single timesheet row and extract structured data.
        
        Args:
            row (List[str]): Row cells
            
        Returns:
            Dict: Timesheet entry or None if parsing fails
        """
        try:
            # Join all cells to work with the full row text
            row_text = ' '.join(row)
            
            # Extract date
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{1,2})', row_text)
            if not date_match:
                return None
            
            date_str = date_match.group(1)
            
            # Extract all time entries from the row
            time_matches = re.findall(r'(\d{1,2}:\d{2})', row_text)
            
            if len(time_matches) < 2:
                return None
            
            # Parse date
            try:
                if len(date_str.split('/')) == 2:
                    # Add current year if not specified
                    date_str += f"/{datetime.now().year}"
                date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                # Try different date format
                try:
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y').date()
                except ValueError:
                    return None
            
            # Parse times
            times = []
            for time_str in time_matches:
                try:
                    time_obj = datetime.strptime(time_str, '%H:%M').time()
                    times.append(time_obj)
                except ValueError:
                    continue
            
            # Structure the entry based on typical timesheet format
            entry = {
                'date': date_obj,
                'times': times,
                'raw_text': row_text.strip()
            }
            
            # Assign specific time slots if we have enough times
            if len(times) >= 2:
                entry['morning_start'] = times[0]
                entry['morning_end'] = times[1] if len(times) > 1 else None
                entry['afternoon_start'] = times[2] if len(times) > 2 else None
                entry['afternoon_end'] = times[3] if len(times) > 3 else None
            
            return entry
            
        except Exception as e:
            print(f"Error parsing row {row}: {e}")
            return None
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert extracted timesheet data to a pandas DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame with timesheet data
        """
        if not self.timesheet_data:
            return pd.DataFrame()
        
        # Flatten the data for DataFrame
        df_data = []
        for entry in self.timesheet_data:
            row_data = {
                'date': entry['date'],
                'morning_start': entry.get('morning_start'),
                'morning_end': entry.get('morning_end'),
                'afternoon_start': entry.get('afternoon_start'),
                'afternoon_end': entry.get('afternoon_end'),
                'raw_text': entry.get('raw_text', '')
            }
            df_data.append(row_data)
        
        return pd.DataFrame(df_data)
    
    def save_to_csv(self, output_path: str) -> None:
        """
        Save extracted timesheet data to CSV file.
        
        Args:
            output_path (str): Path for the output CSV file
        """
        df = self.to_dataframe()
        if not df.empty:
            df.to_csv(output_path, index=False)
            print(f"Timesheet data saved to {output_path}")
        else:
            print("No timesheet data to save")


def main():
    """Example usage of the TimesheetExtractor."""
    extractor = TimesheetExtractor()
    
    # Extract data from PDF
    pdf_path = "test_sample/Ficha Ponto Simplificada André Luis.pdf"
    timesheet_data = extractor.extract_from_pdf(pdf_path)
    
    print(f"Extracted {len(timesheet_data)} timesheet entries")
    
    # Display first few entries
    for i, entry in enumerate(timesheet_data[:5]):
        print(f"Entry {i+1}: {entry}")
    
    # Save to CSV
    extractor.save_to_csv("extracted_timesheet.csv")
    
    # Display as DataFrame
    df = extractor.to_dataframe()
    print("\nDataFrame:")
    print(df.head())


if __name__ == "__main__":
    main()
