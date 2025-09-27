#!/usr/bin/env python3
"""
Gerador de Dashboard Estático para GitHub Pages
Converte os dados do dashboard Streamlit em um site estático HTML/CSS/JS
"""

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import base64

def time_to_hours(time_str):
    """Convert time string HH:MM to decimal hours"""
    if pd.isna(time_str) or time_str is None or time_str == 'None' or time_str == '':
        return 0
    try:
        hours, minutes = map(int, str(time_str).split(':'))
        return hours + minutes / 60
    except:
        return 0

def hours_to_time(hours):
    """Convert decimal hours to HH:MM format"""
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h:02d}:{m:02d}"

def find_data_file():
    """Busca o arquivo de dados unificado timesheet_webapp_data.json"""
    current_dir = Path(__file__).parent
    
    # Locais possíveis para o arquivo
    possible_locations = [
        current_dir,
        current_dir / "src" / "folhaponto",
        current_dir / "dashboard",
    ]
    
    target_filename = "timesheet_webapp_data.json"
    
    for location in possible_locations:
        if location.exists():
            file_path = location / target_filename
            if file_path.exists():
                return str(file_path)
    
    return None

def process_timesheet_data_for_charts(timesheet_data):
    """Converte os dados do timesheet para o formato esperado pelos gráficos"""
    daily_analysis = []
    
    for entry in timesheet_data:
        # Pular entradas que não são de trabalho
        if entry.get('tipo') not in ['Trabalho', 'Feriado']:
            continue
            
        # Pular entradas sem jornada
        if not entry.get('jornada_diaria'):
            continue
            
        # Extrair e converter data
        data_str = entry.get('data', '')
        try:
            data_parts = data_str.split(' ')[0]  # Pegar apenas a parte da data
            day, month, year = data_parts.split('/')
            if len(year) == 2:
                year = '20' + year
            data_iso = f"{year}-{month}-{day}"
            
            # Converter horas trabalhadas
            jornada_str = entry.get('jornada_diaria', '00:00')
            horas_trabalhadas = time_to_hours(jornada_str)
            
            # Converter intervalo de refeição
            refeicao_str = entry.get('total_refeicao', '00:00')
            intervalo_almoco = time_to_hours(refeicao_str)
            
            # Criar observações
            observacoes = ""
            if entry.get('tipo') == 'Feriado':
                observacoes = "Trabalho em feriado"
            elif horas_trabalhadas > 8:
                excesso = horas_trabalhadas - 8
                observacoes = f"Excesso de {excesso:.1f}h - possível irregularidade"
            elif horas_trabalhadas < 8:
                observacoes = "Jornada abaixo do normal"
            
            daily_entry = {
                'data': data_iso,
                'data_display': data_str,
                'entrada': entry.get('jornada_inicio', ''),
                'saida': entry.get('jornada_fim', ''),
                'horas_trabalhadas': horas_trabalhadas,
                'intervalo_almoco': intervalo_almoco,
                'observacoes': observacoes
            }
            
            daily_analysis.append(daily_entry)
            
        except (ValueError, IndexError, AttributeError):
            continue
    
    return daily_analysis

def generate_charts_json(data):
    """Gera dados para os gráficos em formato JSON"""
    timesheet_data = data.get('timesheet_data', [])
    daily_data = process_timesheet_data_for_charts(timesheet_data)
    
    if not daily_data:
        return {}
    
    df_daily = pd.DataFrame(daily_data)
    df_daily['data'] = pd.to_datetime(df_daily['data'])
    df_daily['data_str'] = df_daily['data'].dt.strftime('%d/%m')
    
    # Gráfico de horas trabalhadas
    fig_hours = px.bar(
        df_daily, 
        x='data_str', 
        y='horas_trabalhadas',
        title="Horas Trabalhadas por Dia"
    )
    
    # Gráfico de intervalos
    fig_meal = px.bar(
        df_daily,
        x='data_str',
        y='intervalo_almoco',
        title="Intervalos de Almoço por Dia"
    )
    
    # Gráfico de pizza para horas mensais
    working_days = len([entry for entry in timesheet_data if entry.get('tipo') == 'Trabalho'])
    total_hours = sum(time_to_hours(entry.get('jornada_diaria', '00:00')) for entry in timesheet_data if entry.get('jornada_diaria'))
    horas_contratuais = working_days * 8
    diferenca = max(0, total_hours - horas_contratuais)
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=['Horas Contratuais', 'Horas Extras'],
        values=[horas_contratuais, diferenca],
        hole=.3
    )])
    
    return {
        'hours_chart': fig_hours.to_json(),
        'meal_chart': fig_meal.to_json(),
        'pie_chart': fig_pie.to_json(),
        'daily_data': daily_data
    }

def encode_pdf_to_base64():
    """Codifica o PDF para base64 se existir"""
    pdf_path = Path(__file__).parent / "test_sample" / "Ficha_Ponto_Simplificada_André_Luis.pdf"
    
    if pdf_path.exists():
        try:
            with open(pdf_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except:
            return None
    return None

def generate_static_html():
    """Gera o dashboard estático em HTML"""
    
    # Carregar dados
    data_file_path = find_data_file()
    
    if not data_file_path:
        print("❌ Arquivo de dados 'timesheet_webapp_data.json' não encontrado!")
        return False
    
    with open(data_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extrair informações básicas
    employee_info = data.get('employee', {})
    company_info = data.get('company', {})
    period_info = data.get('period', 'N/A')
    
    # Calcular métricas
    timesheet_data = data.get('timesheet_data', [])
    working_days = len([entry for entry in timesheet_data if entry.get('tipo') == 'Trabalho'])
    total_days = len(timesheet_data)
    
    total_hours = sum(time_to_hours(entry.get('jornada_diaria', '00:00')) for entry in timesheet_data if entry.get('jornada_diaria'))
    total_meal_hours = sum(time_to_hours(entry.get('total_refeicao', '00:00')) for entry in timesheet_data if entry.get('total_refeicao'))
    
    compliance_summary = data.get('compliance_summary', {})
    issues_count = compliance_summary.get('total_compliance_issues', 0)
    compliance_rate = compliance_summary.get('compliance_rate', 0)
    
    # Determinar nível de risco
    if issues_count > 20:
        risk_level = 'CRÍTICO'
        risk_color = '#F44336'
    elif issues_count > 10:
        risk_level = 'ALTO'
        risk_color = '#FF5722'
    elif issues_count > 5:
        risk_level = 'MÉDIO'
        risk_color = '#FF9800'
    else:
        risk_level = 'BAIXO'
        risk_color = '#4CAF50'
    
    # Gerar dados dos gráficos
    charts_data = generate_charts_json(data)
    
    # Codificar PDF
    pdf_base64 = encode_pdf_to_base64()
    
    # Processar problemas detalhados
    detailed_problems = data.get('detailed_problems', {})
    excessive_hours = detailed_problems.get('excessive_daily_hours', [])
    meal_breaks = detailed_problems.get('insufficient_meal_breaks', [])
    rest_periods = detailed_problems.get('insufficient_rest_periods', [])
    
    # Template HTML
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Cronoanálise da Jornada de Trabalho</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .main-header {{
            padding: 2rem 0;
            text-align: center;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .main-header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .main-header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        
        .metric-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        
        .metric-card h3 {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }}
        
        .metric-card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }}
        
        .section {{
            background: white;
            margin: 2rem 0;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #333;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #667eea;
        }}
        
        .risk-analysis {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }}
        
        .risk-card {{
            text-align: center;
            padding: 1.5rem;
            background: {risk_color};
            color: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .risk-card h3 {{
            margin-bottom: 0.5rem;
        }}
        
        .risk-card .level {{
            font-size: 2rem;
            font-weight: bold;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }}
        
        .chart-container {{
            background: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .alert {{
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 5px;
            border-left: 5px solid;
        }}
        
        .alert-critical {{
            background-color: #ffebee;
            border-left-color: #f44336;
            color: #c62828;
        }}
        
        .alert-warning {{
            background-color: #fff3e0;
            border-left-color: #ff9800;
            color: #e65100;
        }}
        
        .alert-success {{
            background-color: #e8f5e8;
            border-left-color: #4caf50;
            color: #2e7d32;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        
        .data-table th,
        .data-table td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        .data-table th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #333;
        }}
        
        .data-table tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .sidebar {{
            position: fixed;
            left: -300px;
            top: 0;
            width: 300px;
            height: 100vh;
            background: white;
            box-shadow: 2px 0 5px rgba(0,0,0,0.1);
            transition: left 0.3s ease;
            z-index: 1000;
            overflow-y: auto;
            padding: 1rem;
        }}
        
        .sidebar.open {{
            left: 0;
        }}
        
        .sidebar-toggle {{
            position: fixed;
            top: 20px;
            left: 20px;
            background: #667eea;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 5px;
            cursor: pointer;
            z-index: 1001;
        }}
        
        .pdf-viewer {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 2000;
        }}
        
        .pdf-content {{
            position: relative;
            width: 90%;
            height: 90%;
            margin: 5% auto;
            background: white;
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .pdf-close {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: #f44336;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 5px;
            cursor: pointer;
            z-index: 2001;
        }}
        
        .footer {{
            text-align: center;
            color: #666;
            padding: 2rem;
            margin-top: 3rem;
            border-top: 1px solid #ddd;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .main-header h1 {{
                font-size: 1.8rem;
            }}
            
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .metrics-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }}
        }}
    </style>
</head>
<body>
    <button class="sidebar-toggle" onclick="toggleSidebar()">
        <i class="fas fa-bars"></i>
    </button>
    
    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <h3><i class="fas fa-folder"></i> Dados Carregados</h3>
        <div class="alert-success">✅ timesheet_webapp_data.json</div>
        
        <hr style="margin: 1rem 0;">
        
        <h3><i class="fas fa-user"></i> Informações do Funcionário</h3>
        <p><strong>Nome:</strong> {employee_info.get('name', 'N/A')}</p>
        <p><strong>CPF:</strong> {employee_info.get('cpf', 'N/A')}</p>
        <p><strong>Empresa:</strong> {company_info.get('name', 'N/A')}</p>
        <p><strong>CNPJ:</strong> {company_info.get('cnpj', 'N/A')}</p>
        <p><strong>Período:</strong> {period_info}</p>
        
        <hr style="margin: 1rem 0;">
        
        <h3><i class="fas fa-chart-bar"></i> Dados Carregados</h3>
        <p>✅ Dados Unificados do Timesheet</p>
        
        <hr style="margin: 1rem 0;">
        
        <h3><i class="fas fa-file-pdf"></i> Visualizar PDF</h3>
        {'<button onclick="showPDF()" style="width: 100%; padding: 10px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;"><i class="fas fa-file-pdf"></i> Ver Ficha de Ponto (PDF)</button>' if pdf_base64 else '<p style="color: #999;">PDF não disponível</p>'}
    </div>
    
    <!-- PDF Viewer -->
    {f'''<div class="pdf-viewer" id="pdfViewer">
        <div class="pdf-content">
            <button class="pdf-close" onclick="hidePDF()">
                <i class="fas fa-times"></i>
            </button>
            <iframe src="data:application/pdf;base64,{pdf_base64}" 
                    width="100%" height="100%" 
                    style="border: none;">
            </iframe>
        </div>
    </div>''' if pdf_base64 else ''}
    
    <div class="container">
        <!-- Título Principal -->
        <div class="main-header">
            <h1><i class="fas fa-clock"></i> Dashboard - Cronoanálise da Jornada de Trabalho</h1>
            <p>Análise completa de conformidade trabalhista e gestão de jornadas</p>
        </div>
        
        <!-- Métricas Principais -->
        <div class="section">
            <h2><i class="fas fa-chart-line"></i> Visão Geral</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3><i class="fas fa-calendar"></i> Total de Dias</h3>
                    <div class="value">{total_days}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-building"></i> Dias Trabalhados</h3>
                    <div class="value">{working_days}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-clock"></i> Horas Trabalhadas</h3>
                    <div class="value">{total_hours:.1f}h</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-utensils"></i> Horas de Intervalo</h3>
                    <div class="value">{total_meal_hours:.1f}h</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-exclamation-triangle"></i> Problemas de Conformidade</h3>
                    <div class="value">{issues_count}</div>
                </div>
            </div>
        </div>
        
        <!-- Análise de Risco -->
        <div class="section">
            <h2><i class="fas fa-crosshairs"></i> Análise de Risco</h2>
            <div class="risk-analysis">
                <div class="risk-card">
                    <h3>Nível de Risco</h3>
                    <div class="level">{risk_level}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-chart-line"></i> Taxa de Conformidade</h3>
                    <div class="value">{abs(compliance_rate):.1f}%</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-exclamation-circle"></i> Total de Violações</h3>
                    <div class="value">{issues_count}</div>
                </div>
            </div>
        </div>
        
        <!-- Gráficos -->
        <div class="section">
            <h2><i class="fas fa-chart-bar"></i> Análise Diária</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <div id="hoursChart"></div>
                </div>
                <div class="chart-container">
                    <div id="mealChart"></div>
                </div>
            </div>
        </div>
        
        <!-- KPIs -->
        {"" if 'metricas_qualidade' not in data else f'''
        <div class="section">
            <h2><i class="fas fa-target"></i> Indicadores de Desempenho (KPIs)</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3><i class="fas fa-clock"></i> Pontualidade</h3>
                    <div class="value">{data["metricas_qualidade"].get("pontualidade", 0):.1f}%</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-chart-bar"></i> Cumprimento Jornada</h3>
                    <div class="value">{data["metricas_qualidade"].get("cumprimento_jornada", 0):.1f}%</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-utensils"></i> Regularidade Intervalos</h3>
                    <div class="value">{data["metricas_qualidade"].get("regularidade_intervalos", 0):.1f}%</div>
                </div>
            </div>
        </div>'''}
        
        <!-- Plano de Ação -->
        {"" if not (excessive_hours or meal_breaks or rest_periods) else f'''
        <div class="section">
            <h2><i class="fas fa-clipboard-list"></i> Plano de Ação</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3><i class="fas fa-exclamation-circle"></i> Alertas Críticos</h3>
                    <div class="value">{len(excessive_hours)}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-exclamation-triangle"></i> Alertas Urgentes</h3>
                    <div class="value">{len(rest_periods)}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-chart-bar"></i> Total de Alertas</h3>
                    <div class="value">{len(excessive_hours) + len(meal_breaks) + len(rest_periods)}</div>
                </div>
                <div class="metric-card">
                    <h3><i class="fas fa-lightbulb"></i> Recomendações</h3>
                    <div class="value">{min(5, len(excessive_hours) + len(meal_breaks) + len(rest_periods))}</div>
                </div>
            </div>
            
            {"" if not excessive_hours else f'''
            <div class="alert alert-critical">
                <h4><i class="fas fa-exclamation-circle"></i> Ações Imediatas - Horas Excessivas</h4>
                <p><strong>Jornadas Excessivas Detectadas</strong><br>
                {len(excessive_hours)} dias com jornada superior ao limite legal foram identificados.<br>
                <em>Ação necessária: Revisar escalas e implementar controle de jornada</em><br>
                <em>Prazo: Imediato</em></p>
            </div>'''}
            
            {"" if not rest_periods else f'''
            <div class="alert alert-warning">
                <h4><i class="fas fa-exclamation-triangle"></i> Ações Urgentes - Períodos de Descanso</h4>
                <p><strong>Descanso Insuficiente Entre Jornadas</strong><br>
                {len(rest_periods)} ocorrências de descanso inferior a 11 horas entre jornadas.<br>
                <em>Ação necessária: Ajustar horários para garantir descanso adequado</em><br>
                <em>Prazo: 48 horas</em></p>
            </div>'''}
            
            {"" if not meal_breaks else f'''
            <div class="alert alert-warning">
                <h4><i class="fas fa-utensils"></i> Ações Preventivas - Intervalos de Refeição</h4>
                <p><strong>Intervalos de Refeição Irregulares</strong><br>
                {len(meal_breaks)} ocorrências de intervalos inadequados.<br>
                <em>Ação necessária: Orientar funcionário sobre obrigatoriedade dos intervalos</em><br>
                <em>Prazo: 7 dias</em></p>
            </div>'''}
        </div>'''}
        
        <!-- Análise Mensal -->
        {"" if 'period_totals' not in data else f'''
        <div class="section">
            <h2><i class="fas fa-chart-pie"></i> Análise de Jornada Mensal</h2>
            <div class="charts-grid">
                <div>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <h3><i class="fas fa-clock"></i> Horas Trabalhadas</h3>
                            <div class="value">{total_hours:.1f}h</div>
                        </div>
                        <div class="metric-card">
                            <h3><i class="fas fa-clipboard-list"></i> Horas Contratuais</h3>
                            <div class="value">{working_days * 8:.1f}h</div>
                        </div>
                        <div class="metric-card">
                            <h3><i class="fas fa-plus"></i> Diferença</h3>
                            <div class="value">{total_hours - (working_days * 8):.1f}h</div>
                        </div>
                        <div class="metric-card">
                            <h3><i class="fas fa-percentage"></i> % Cumprimento</h3>
                            <div class="value">{(total_hours / (working_days * 8) * 100) if working_days > 0 else 0:.1f}%</div>
                        </div>
                    </div>
                </div>
                <div class="chart-container">
                    <div id="pieChart"></div>
                </div>
            </div>
        </div>'''}
        
        <!-- Tabela Detalhada -->
        <div class="section">
            <h2><i class="fas fa-table"></i> Dados Detalhados por Dia</h2>
            <div style="overflow-x: auto;">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Entrada</th>
                            <th>Saída</th>
                            <th>Horas Trabalhadas</th>
                            <th>Intervalo Almoço</th>
                            <th>Observações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f'''
                        <tr>
                            <td>{entry["data_display"]}</td>
                            <td>{entry["entrada"]}</td>
                            <td>{entry["saida"]}</td>
                            <td>{entry["horas_trabalhadas"]:.2f}h</td>
                            <td>{entry["intervalo_almoco"]:.2f}h</td>
                            <td>{entry["observacoes"]}</td>
                        </tr>
                        ''' for entry in charts_data.get('daily_data', [])])}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Exportar -->
        <div class="section">
            <h2><i class="fas fa-download"></i> Exportar Relatório</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <button onclick="alert('Funcionalidade em desenvolvimento')" 
                        style="padding: 1rem; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    <i class="fas fa-file-pdf"></i> Gerar Relatório PDF
                </button>
                <button onclick="alert('Funcionalidade em desenvolvimento')" 
                        style="padding: 1rem; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    <i class="fas fa-envelope"></i> Enviar por Email
                </button>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>Dashboard de Cronoanálise da Jornada de Trabalho</p>
            <p>Desenvolvido para análise de conformidade trabalhista</p>
            <p><em>Dados atualizados em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}</em></p>
        </div>
    </div>
    
    <script>
        // Dados dos gráficos
        const chartsData = {json.dumps(charts_data)};
        
        // Renderizar gráficos
        if (chartsData.hours_chart) {{
            Plotly.newPlot('hoursChart', JSON.parse(chartsData.hours_chart));
        }}
        
        if (chartsData.meal_chart) {{
            Plotly.newPlot('mealChart', JSON.parse(chartsData.meal_chart));
        }}
        
        if (chartsData.pie_chart) {{
            Plotly.newPlot('pieChart', JSON.parse(chartsData.pie_chart));
        }}
        
        // Função para toggle da sidebar
        function toggleSidebar() {{
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('open');
        }}
        
        // Função para mostrar PDF
        function showPDF() {{
            const pdfViewer = document.getElementById('pdfViewer');
            if (pdfViewer) {{
                pdfViewer.style.display = 'block';
            }}
        }}
        
        // Função para esconder PDF
        function hidePDF() {{
            const pdfViewer = document.getElementById('pdfViewer');
            if (pdfViewer) {{
                pdfViewer.style.display = 'none';
            }}
        }}
        
        // Fechar sidebar ao clicar fora
        document.addEventListener('click', function(event) {{
            const sidebar = document.getElementById('sidebar');
            const toggle = document.querySelector('.sidebar-toggle');
            
            if (!sidebar.contains(event.target) && !toggle.contains(event.target)) {{
                sidebar.classList.remove('open');
            }}
        }});
        
        // Responsive charts
        window.addEventListener('resize', function() {{
            if (window.Plotly) {{
                Plotly.Plots.resize('hoursChart');
                Plotly.Plots.resize('mealChart');
                Plotly.Plots.resize('pieChart');
            }}
        }});
    </script>
</body>
</html>"""
    
    # Criar diretório docs se não existir
    docs_dir = Path(__file__).parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Salvar arquivo HTML
    output_file = docs_dir / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard estático gerado com sucesso!")
    print(f"📁 Arquivo: {output_file}")
    print(f"🌐 Para visualizar localmente: file://{output_file.absolute()}")
    
    return True

if __name__ == "__main__":
    print("🚀 Gerando Dashboard Estático...")
    success = generate_static_html()
    
    if success:
        print("\n📋 Próximos passos para publicar no GitHub Pages:")
        print("1. Faça commit dos arquivos gerados:")
        print("   git add docs/")
        print("   git commit -m 'Add static dashboard'")
        print("   git push origin main")
        print("\n2. Configure GitHub Pages:")
        print("   - Vá para Settings > Pages no seu repositório")
        print("   - Selecione 'Deploy from a branch'")
        print("   - Escolha 'main' branch e '/docs' folder")
        print("   - Clique em Save")
        print("\n3. Acesse seu dashboard em:")
        print("   https://seu-usuario.github.io/FolhaPonto/")
    else:
        print("❌ Erro ao gerar dashboard estático")
