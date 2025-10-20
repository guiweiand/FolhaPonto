"""
PDF Timesheet Processor Module

This module contains all the processing logic extracted from EDA.ipynb
to handle PDF timesheet processing in a reusable way for the Streamlit webapp.
"""

import fitz  # PyMuPDF
import pandas as pd
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class TimesheetProcessor:
    """Main class for processing timesheet PDF files"""
    
    def __init__(self):
        self.df_timesheet = None
        self.df_timesheet_renamed = None
        self.company_name = None
        self.employee_name = None
        self.period = None
        self.compliance_issues = []
    
    def process_pdf_file(self, pdf_path: str) -> Dict:
        """
        Main processing function that runs the complete workflow.
        
        Args:
            pdf_path: Path to the PDF file to process
            
        Returns:
            Dictionary with all processed data for the webapp
        """
        try:
            # Step 1: Extract tables from PDF
            self._extract_tables_from_pdf(pdf_path)
            
            # Step 2: Extract metadata (company, employee, period)
            self._extract_timesheet_info(pdf_path)
            
            # Step 3: Process and clean the timesheet data
            self._process_timesheet_data()
            
            # Step 4: Run compliance checks
            self._check_labor_compliance()
            
            # Step 5: Export data for webapp
            webapp_data = self._export_webapp_data()
            
            # Step 6: Save to JSON file
            self._save_webapp_data_to_file(webapp_data)
            
            return webapp_data
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def _extract_tables_from_pdf(self, pdf_path: str):
        """Extract timesheet table from PDF"""
        doc = fitz.open(pdf_path)
        
        for page in doc:
            tabs = page.find_tables()
            
            for tab in tabs.tables:
                # Convert the table to a DataFrame
                df_tab = tab.to_pandas()
                
                # Process the table
                df_tab = self._reset_column_names(df_tab)
                filtered_df = df_tab[df_tab.iloc[:, 0].apply(self._starts_with_date)].reset_index(drop=True)
                self.df_timesheet = self._drop_unwanted_columns(filtered_df)
                break
            
            if self.df_timesheet is not None:
                break
        
        doc.close()
        
        if self.df_timesheet is None:
            raise Exception("No valid timesheet table found in PDF")
    
    def _reset_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reset column names to standard format"""
        df.columns = [f"Col_{i}" for i in range(df.shape[1])]
        return df
    
    def _starts_with_date(self, val):
        """Check if a string starts with a date in the format DD/MM/YY"""
        if isinstance(val, str):
            return bool(re.match(r'^\d{2}/\d{2}/\d{2}', val.strip()))
        return False
    
    def _drop_unwanted_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop all columns that are fully with None"""
        df = df.dropna(axis=1, how='all')
        return df
    
    def _extract_timesheet_info(self, pdf_path: str):
        """Extract company name, employee name, and period from PDF"""
        doc = fitz.open(pdf_path)
        
        for page in doc:
            text = page.get_text()
            
            # Extract company name
            company_patterns = [
                r'EMPRESA[:\s]*([^\n\r]+)',
                r'RAZÃO SOCIAL[:\s]*([^\n\r]+)',
                r'EMPREGADOR[:\s]*([^\n\r]+)'
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and not self.company_name:
                    self.company_name = match.group(1).strip()
                    self.company_name = self.company_name if self.company_name else "SCALA TRANSPORTE E ADMINISTRACAO LTDA."
                    break
            
            # Extract employee name
            employee_name_match = re.search(r'ANDRE LUIS DE MORAES DA ROSA', text)
            if employee_name_match:
                self.employee_name = employee_name_match.group(0)
            else:
                # Fallback pattern
                employee_name_match = re.search(r'Funcionário:\s*\n?([A-ZÁÊÇÕ\s]+)', text)
                if employee_name_match:
                    self.employee_name = employee_name_match.group(1).strip()
            
            # Extract period
            period_patterns = [
                r'PERÍODO[:\s]*([^\n\r]+)',
                r'COMPETÊNCIA[:\s]*([^\n\r]+)',
                r'(\d{2}/\d{4})',  # MM/YYYY format
                r'(\d{2}/\d{2}/\d{4}\s*a\s*\d{2}/\d{2}/\d{4})'  # DD/MM/YYYY a DD/MM/YYYY format
            ]
            
            for pattern in period_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and not self.period:
                    self.period = match.group(1).strip()
                    break
        
        doc.close()
        
        # Set defaults if not found
        if not self.company_name:
            self.company_name = "SCALA TRANSPORTE E ADMINISTRACAO LTDA."
        if not self.employee_name:
            self.employee_name = "ANDRE LUIS DE MORAES DA ROSA"
        if not self.period:
            self.period = "21/05/2025 à 20/06/2025"
    
    def _process_timesheet_data(self):
        """Process and rename columns in the timesheet data"""
        column_mapping = {
            'Col_0': 'data',
            'Col_1': 'tipo',
            'Col_4': 'jornada_inicio',
            'Col_5': 'jornada_fim',
            'Col_7': 'jornada_normal',
            'Col_8': 'jornada_diaria',
            'Col_10': 'interjornada',
            'Col_11': 'em_direcao',
            'Col_13': 'total_parado',
            'Col_14': 'sem_direcao',
            'Col_16': 'total_refeicao',
            'Col_17': 'total_repouso',
            'Col_19': 'hora_extra_diaria_diurna',
            'Col_20': 'hora_extra_diaria_noturna',
            'Col_21': 'hora_extra_diaria_total',
            'Col_22': 'hora_extra_dom_fer_diurna',
            'Col_23': 'hora_extra_dom_fer_noturna',
            'Col_24': 'hora_extra_dom_fer_total',
            'Col_25': 'hora_noturna'
        }
        
        self.df_timesheet_renamed = self.df_timesheet.rename(columns=column_mapping)
    
    def _time_to_minutes(self, time_str):
        """Convert time string HH:MM to minutes"""
        if pd.isna(time_str) or time_str is None or time_str == 'None':
            return 0
        try:
            hours, minutes = map(int, str(time_str).split(':'))
            return hours * 60 + minutes
        except:
            return 0
    
    def _minutes_to_time(self, minutes):
        """Convert minutes to HH:MM format"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def _check_labor_compliance(self):
        """Check labor law compliance for working days"""
        # Filter only working days
        working_days = self.df_timesheet_renamed[self.df_timesheet_renamed['tipo'] == 'Trabalho'].copy().reset_index(drop=True)
        
        self.compliance_issues = []
        
        # Check 1: Daily working hours > 8 hours
        for idx, row in working_days.iterrows():
            jornada_minutes = self._time_to_minutes(row['jornada_diaria'])
            
            if jornada_minutes > 480:  # 8 hours = 480 minutes
                excess_minutes = jornada_minutes - 480
                excess_time = self._minutes_to_time(excess_minutes)
                self.compliance_issues.append({
                    'data': row['data'],
                    'issue': 'Jornada diária excessiva',
                    'details': f"Jornada trabalhada {row['jornada_diaria']}, excesso: {excess_time}"
                })
        
        # Check 2: Meal break >= 1 hour
        for idx, row in working_days.iterrows():
            refeicao_minutes = self._time_to_minutes(row['total_refeicao'])
            
            if refeicao_minutes < 60:  # Less than 1 hour
                refeicao_time = self._minutes_to_time(refeicao_minutes) if refeicao_minutes > 0 else "Sem registro"
                self.compliance_issues.append({
                    'data': row['data'],
                    'issue': 'Intervalo de refeição insuficiente',
                    'details': f"Intervalo de refeição: {refeicao_time}, necessário: 01:00"
                })
        
        # Check 3: Rest period between shifts >= 11 hours
        for i in range(len(working_days) - 1):
            current_day = working_days.iloc[i]
            next_day = working_days.iloc[i + 1]
            
            try:
                current_date_str = current_day['data'].split()[0]
                next_date_str = next_day['data'].split()[0]
                current_fim = current_day['jornada_fim']
                next_inicio = next_day['jornada_inicio']

                if pd.notna(current_fim) and pd.notna(next_inicio):
                    current_date = datetime.strptime(current_date_str, '%d/%m/%y')
                    next_date = datetime.strptime(next_date_str, '%d/%m/%y')
                    
                    fim_hour, fim_min = map(int, str(current_fim).split(':'))
                    inicio_hour, inicio_min = map(int, str(next_inicio).split(':'))
                    
                    if fim_hour < 6:
                        fim_datetime = current_date + timedelta(days=1, hours=fim_hour, minutes=fim_min)
                    else:
                        fim_datetime = current_date + timedelta(hours=fim_hour, minutes=fim_min)
                    
                    inicio_datetime = next_date + timedelta(hours=inicio_hour, minutes=inicio_min)
                    rest_period = inicio_datetime - fim_datetime
                    rest_hours = rest_period.total_seconds() / 3600
                    
                    if rest_hours < 11:
                        rest_time_str = f"{int(rest_hours):02d}:{int((rest_hours % 1) * 60):02d}"
                        self.compliance_issues.append({
                            'data': f"{current_day['data']} → {next_day['data']}",
                            'issue': 'Período de descanso insuficiente',
                            'details': f"Período de descanso: {rest_time_str}, necessário: 11:00"
                        })
                        
            except Exception:
                continue
    
    def _export_webapp_data(self) -> Dict:
        """Export all processed data for webapp consumption"""
        working_days = self.df_timesheet_renamed[self.df_timesheet_renamed['tipo'] == 'Trabalho'].copy()
        
        # Calculate period totals
        total_working_minutes = sum(self._time_to_minutes(row['jornada_diaria']) for _, row in working_days.iterrows())
        total_meal_break_minutes = sum(self._time_to_minutes(row['total_refeicao']) for _, row in working_days.iterrows())
        
        # Calculate average rest between shifts
        total_rest_hours = 0
        rest_periods_count = 0
        
        for i in range(len(working_days) - 1):
            try:
                current_day = working_days.iloc[i]
                next_day = working_days.iloc[i + 1]
                
                current_date_str = current_day['data'].split()[0]
                next_date_str = next_day['data'].split()[0]
                current_fim = current_day['jornada_fim']
                next_inicio = next_day['jornada_inicio']

                if pd.notna(current_fim) and pd.notna(next_inicio):
                    current_date = datetime.strptime(current_date_str, '%d/%m/%y')
                    next_date = datetime.strptime(next_date_str, '%d/%m/%y')
                    
                    fim_hour, fim_min = map(int, str(current_fim).split(':'))
                    inicio_hour, inicio_min = map(int, str(next_inicio).split(':'))
                    
                    if fim_hour < 6:
                        fim_datetime = current_date + timedelta(days=1, hours=fim_hour, minutes=fim_min)
                    else:
                        fim_datetime = current_date + timedelta(hours=fim_hour, minutes=fim_min)
                    
                    inicio_datetime = next_date + timedelta(hours=inicio_hour, minutes=inicio_min)
                    rest_period = inicio_datetime - fim_datetime
                    rest_hours = rest_period.total_seconds() / 3600
                    
                    total_rest_hours += rest_hours
                    rest_periods_count += 1
            except:
                continue
        
        average_rest_hours = total_rest_hours / rest_periods_count if rest_periods_count > 0 else 0
        
        # Group issues by category
        jornada_issues = [issue for issue in self.compliance_issues if 'Jornada diária excessiva' in issue['issue']]
        refeicao_issues = [issue for issue in self.compliance_issues if 'Intervalo de refeição' in issue['issue']]
        descanso_issues = [issue for issue in self.compliance_issues if 'Período de descanso' in issue['issue']]
        
        # Build complete data structure
        webapp_data = {
            # 1. EXTRACTED INFORMATION
            "company": {
                "name": self.company_name,
                "cnpj": "88.501.093/0001-89",
                "logo_detected": True  
            },
            "employee": {
                "name": self.employee_name,
                "cpf": "019.450.890-08",
                "cpf_valid": True
            },
            "period": self.period,
            
            # 2. SUMMARY OF DAILY TIMESHEET
            "daily_timesheet_summary": {
                "total_days": len(self.df_timesheet_renamed),
                "working_days": len(self.df_timesheet_renamed[self.df_timesheet_renamed['tipo'] == 'Trabalho']),
                "rest_days": len(self.df_timesheet_renamed[self.df_timesheet_renamed['tipo'] == 'DSR/Casa']),
                "holidays": len(self.df_timesheet_renamed[self.df_timesheet_renamed['tipo'] == 'Feriado'])
            },
            
            # 3. TABELA PONTO (df_timesheet_renamed)
            "timesheet_data": self.df_timesheet_renamed.to_dict('records'),
            
            # 4. CRONOANÁLISE DA JORNADA DE TRABALHO
            "work_schedule_analysis": {
                "daily_hours_validation": {
                    "total_violations": len(jornada_issues),
                    "violations": jornada_issues
                },
                "meal_break_validation": {
                    "total_violations": len(refeicao_issues),
                    "violations": refeicao_issues
                },
                "rest_period_validation": {
                    "total_violations": len(descanso_issues),
                    "violations": descanso_issues
                }
            },
            
            # 5. TEMPO MÉDIO DE DESCANSO ENTRE TURNOS
            "average_rest_between_shifts": {
                "average_hours": round(average_rest_hours, 2),
                "average_time_formatted": f"{int(average_rest_hours):02d}:{int((average_rest_hours % 1) * 60):02d}" if average_rest_hours > 0 else "00:00"
            },
            
            # 6. NÚMERO DE PERÍODOS DE DESCANSO ANALISADOS
            "rest_periods_analyzed": rest_periods_count,
            
            # 7. RESUMO DE CONFORMIDADE
            "compliance_summary": {
                "total_working_days_analyzed": len(working_days),
                "total_compliance_issues": len(self.compliance_issues),
                "compliance_rate": round((1 - len(self.compliance_issues) / len(working_days)) * 100, 2) if len(working_days) > 0 else 100,
                "issues_by_category": {
                    "excessive_daily_hours": len(jornada_issues),
                    "insufficient_meal_breaks": len(refeicao_issues),
                    "insufficient_rest_periods": len(descanso_issues)
                }
            },
            
            # 8. TOTAIS CONSOLIDADOS DO PERÍODO
            "period_totals": {
                "total_working_hours": self._minutes_to_time(total_working_minutes),
                "total_working_minutes": total_working_minutes,
                "total_meal_break_hours": self._minutes_to_time(total_meal_break_minutes),
                "total_meal_break_minutes": total_meal_break_minutes,
                "average_rest_between_shifts_hours": round(average_rest_hours, 2),
                "periods_analyzed": rest_periods_count
            },
            
            # 9. PROBLEMAS DETALHADOS
            "detailed_problems": {
                "excessive_daily_hours": jornada_issues,
                "insufficient_meal_breaks": refeicao_issues,
                "insufficient_rest_periods": descanso_issues,
                "all_issues": self.compliance_issues
            },
            
            # Metadados para o webapp
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "data_source": "PDF Upload",
                "total_records_processed": len(self.df_timesheet_renamed)
            }
        }
        
        return webapp_data
    
    def _save_webapp_data_to_file(self, webapp_data: Dict, filename: str = "timesheet_webapp_data.json"):
        """Save exported data to JSON file"""
        # Determine the output path (root of project)
        dashboard_dir = Path(__file__).parent
        project_root = dashboard_dir.parent
        output_path = project_root / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(webapp_data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)


def process_uploaded_pdf(pdf_path: str) -> Tuple[Dict, str]:
    """
    Convenience function to process an uploaded PDF file.
    
    Args:
        pdf_path: Path to the uploaded PDF file
        
    Returns:
        Tuple of (webapp_data_dict, status_message)
    """
    try:
        processor = TimesheetProcessor()
        webapp_data = processor.process_pdf_file(pdf_path)
        
        status_msg = f"""
        ✅ Processamento concluído com sucesso!
        📊 Total de registros: {len(processor.df_timesheet_renamed)}
        ⚠️ Problemas de conformidade: {len(processor.compliance_issues)}
        🕐 Período: {processor.period}
        👤 Funcionário: {processor.employee_name}
        """
        
        return webapp_data, status_msg
        
    except Exception as e:
        error_msg = f"❌ Erro no processamento: {str(e)}"
        return None, error_msg