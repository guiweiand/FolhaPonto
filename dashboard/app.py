import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Cronoanálise da Jornada de Trabalho",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        padding: 2rem 0;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .alert-critical {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .alert-warning {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .alert-success {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares
@st.cache_data
def load_json_data(file_path):
    """Carrega dados JSON com cache"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {file_path}")
        return None
    except json.JSONDecodeError:
        st.error(f"Erro ao decodificar JSON: {file_path}")
        return None

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

def get_risk_color(level):
    """Retorna cor baseada no nível de risco"""
    colors = {
        'BAIXO': '#4CAF50',
        'MÉDIO': '#FF9800', 
        'ALTO': '#FF5722',
        'CRÍTICO': '#F44336'
    }
    return colors.get(level, '#757575')

def find_data_files():
    """Busca os arquivos de dados em múltiplos locais possíveis"""
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent
    
    # Locais possíveis para os arquivos
    possible_locations = [
        # Diretório pai do projeto
        parent_dir,
        # Diretório src/folhaponto
        parent_dir / "src" / "folhaponto",
        # Diretório atual
        current_dir,
    ]
    
    # Arquivos específicos a buscar
    target_files = [
        ("timesheet_clean_final.json", "Dados Limpos do Timesheet"),
        ("dashboard_data_complete.json", "Dados Completos do Dashboard"), 
        ("compliance_dashboard.json", "Relatório de Conformidade")
    ]
    
    found_files = []
    
    for location in possible_locations:
        if location.exists():
            for filename, file_type in target_files:
                file_path = location / filename
                if file_path.exists():
                    # Evitar duplicatas
                    if not any(existing_type == file_type for existing_type, _ in found_files):
                        found_files.append((file_type, str(file_path)))
    
    return found_files

# Título principal
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard - Cronoanálise da Jornada de Trabalho</h1>
    <p>Análise completa de conformidade trabalhista e gestão de jornadas</p>
</div>
""", unsafe_allow_html=True)

# Carregar dados usando a função de busca
available_files = find_data_files()

# Debug temporário: mostrar informações detalhadas
st.write("**🔍 DEBUG - Informações de busca:**")
current_dir = Path(__file__).parent
parent_dir = current_dir.parent

st.write(f"📁 Diretório atual do script: `{current_dir}`")
st.write(f"📁 Diretório pai: `{parent_dir}`")

# Verificar cada local
locations_to_check = [
    parent_dir,
    parent_dir / "src" / "folhaponto",
    current_dir,
]

st.write("**📂 Verificando locais:**")
for i, location in enumerate(locations_to_check, 1):
    st.write(f"{i}. `{location}` - {'✅ Existe' if location.exists() else '❌ Não existe'}")
    
    if location.exists():
        # Listar arquivos JSON no diretório
        json_files = list(location.glob("*.json"))
        if json_files:
            st.write(f"   📄 Arquivos JSON encontrados:")
            for json_file in json_files:
                st.write(f"   - {json_file.name}")
        else:
            st.write(f"   📄 Nenhum arquivo JSON encontrado")

st.write(f"**📊 Total de arquivos disponíveis encontrados: {len(available_files)}**")
for file_type, file_path in available_files:
    st.write(f"✅ {file_type}: `{file_path}`")

# Se não encontrou arquivos, tentar carregamento direto
if not available_files:
    st.write("**🔧 Tentando carregamento direto dos arquivos específicos:**")
    
    # Tentar caminhos absolutos conhecidos
    direct_paths = [
        r"c:\Users\Guilh\Documents\VSCode Projects\FolhaPonto\timesheet_clean_final.json",
        r"c:\Users\Guilh\Documents\VSCode Projects\FolhaPonto\dashboard_data_complete.json",
        r"c:\Users\Guilh\Documents\VSCode Projects\FolhaPonto\src\folhaponto\compliance_dashboard.json",
        r"c:\Users\Guilh\Documents\VSCode Projects\FolhaPonto\src\folhaponto\timesheet_clean_final.json",
        r"c:\Users\Guilh\Documents\VSCode Projects\FolhaPonto\src\folhaponto\dashboard_data_complete.json"
    ]
    
    direct_available = []
    for path in direct_paths:
        file_path = Path(path)
        if file_path.exists():
            filename = file_path.name
            if "timesheet_clean_final" in filename:
                file_type = "Dados Limpos do Timesheet"
            elif "compliance_dashboard" in filename:
                file_type = "Relatório de Conformidade"
            elif "dashboard_data_complete" in filename:
                file_type = "Dados Completos do Dashboard"
            else:
                file_type = "Dados"
            
            # Evitar duplicatas
            if not any(existing_type == file_type for existing_type, _ in direct_available):
                direct_available.append((file_type, str(file_path)))
                st.write(f"✅ Encontrado diretamente: {file_type} em `{path}`")
    
    if direct_available:
        st.write(f"**🎉 Usando carregamento direto! Encontrados {len(direct_available)} arquivos.**")
        available_files = direct_available

# Verificar arquivos disponíveis
if not available_files:
    st.error("❌ Nenhum arquivo de dados encontrado! Verifique se os arquivos JSON estão na localização correta.")
    st.info("Arquivos esperados:")
    st.write("- timesheet_clean_final.json")
    st.write("- compliance_dashboard.json") 
    st.write("- dashboard_data_complete.json")
    st.stop()

# Sidebar para seleção de arquivos
st.sidebar.header("📁 Seleção de Dados")
selected_file = st.sidebar.selectbox(
    "Escolha o arquivo de dados:",
    options=[file[1] for file in available_files],
    format_func=lambda x: next((name for name, path in available_files if path == x), x)
)

# Carregar dados selecionados
data = load_json_data(selected_file)
if data is None:
    st.stop()

# Extrair informações básicas
employee_info = data.get('employee', {})
company_info = data.get('company', {})
period_info = data.get('period', {})
summary_info = data.get('summary', {})

# Sidebar - Informações do funcionário
st.sidebar.markdown("---")
st.sidebar.header("👤 Informações do Funcionário")
st.sidebar.write(f"**Nome:** {employee_info.get('name', 'N/A')}")
st.sidebar.write(f"**CPF:** {employee_info.get('cpf', 'N/A')}")
st.sidebar.write(f"**Empresa:** {company_info.get('name', 'N/A')}")
st.sidebar.write(f"**CNPJ:** {company_info.get('cnpj', 'N/A')}")
st.sidebar.write(f"**Período:** {period_info.get('description', 'N/A')}")

# Mostrar status dos arquivos carregados
st.sidebar.markdown("---")
st.sidebar.header("📊 Dados Carregados")
for file_type, _ in available_files:
    st.sidebar.write(f"✅ {file_type}")

# Verificar se há dados de compliance
compliance_data = None
if 'risk_assessment' in data:
    compliance_data = data
else:
    # Buscar arquivo de compliance separadamente
    for file_type, file_path in available_files:
        if "Conformidade" in file_type:
            compliance_data = load_json_data(file_path)
            break

# Métricas principais
st.header("📊 Visão Geral")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_days = summary_info.get('total_days', 0)
    st.metric("📅 Total de Dias", total_days)

with col2:
    work_days = summary_info.get('work_days', 0)
    st.metric("🏢 Dias Trabalhados", work_days)

with col3:
    total_hours = summary_info.get('total_hours_worked', 0)
    st.metric("⏰ Horas Trabalhadas", f"{total_hours:.1f}h")

with col4:
    meal_hours = summary_info.get('total_meal_break_hours', 0)
    st.metric("🍽️ Horas de Intervalo", f"{meal_hours:.1f}h")

with col5:
    issues_count = summary_info.get('compliance_issues_count', 0)
    st.metric("⚠️ Problemas de Conformidade", issues_count)

# Análise de risco (se disponível)
if compliance_data and 'risk_assessment' in compliance_data:
    st.markdown("---")
    st.header("🎯 Análise de Risco")
    
    risk_data = compliance_data['risk_assessment']
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_level = risk_data.get('level', 'N/A')
        risk_color = get_risk_color(risk_level)
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background: {risk_color}; color: white; border-radius: 10px;'>
            <h3>Nível de Risco</h3>
            <h1>{risk_level}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        compliance_rate = risk_data.get('compliance_rate', 0)
        st.metric("📈 Taxa de Conformidade", f"{compliance_rate:.1f}%")
    
    with col3:
        violations = risk_data.get('total_violations', 0)
        st.metric("🚨 Total de Violações", violations)

# Gráficos de análise diária
if 'analise_diaria' in data:
    st.markdown("---")
    st.header("📈 Análise Diária")
    
    daily_data = data['analise_diaria']
    df_daily = pd.DataFrame(daily_data)
    
    # Converter datas
    df_daily['data'] = pd.to_datetime(df_daily['data'])
    df_daily['data_str'] = df_daily['data'].dt.strftime('%d/%m')
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de horas trabalhadas por dia
        fig_hours = px.bar(
            df_daily, 
            x='data_str', 
            y='horas_trabalhadas',
            title="Horas Trabalhadas por Dia",
            color='horas_trabalhadas',
            color_continuous_scale='RdYlGn_r'
        )
        fig_hours.add_hline(y=8, line_dash="dash", line_color="red", annotation_text="Limite 8h")
        fig_hours.add_hline(y=10, line_dash="dash", line_color="orange", annotation_text="Limite 10h")
        fig_hours.update_layout(
            xaxis_title="Data",
            yaxis_title="Horas",
            showlegend=False
        )
        st.plotly_chart(fig_hours, use_container_width=True)
    
    with col2:
        # Gráfico de intervalos de almoço
        fig_meal = px.bar(
            df_daily,
            x='data_str',
            y='intervalo_almoco',
            title="Intervalos de Almoço por Dia",
            color_discrete_sequence=['#2E86AB']
        )
        fig_meal.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Mínimo 1h")
        fig_meal.update_layout(
            xaxis_title="Data",
            yaxis_title="Horas",
            showlegend=False
        )
        st.plotly_chart(fig_meal, use_container_width=True)

# KPIs de desempenho
if compliance_data and 'kpis' in compliance_data:
    st.markdown("---")
    st.header("🎯 Indicadores de Desempenho (KPIs)")
    
    kpis = compliance_data['kpis']
    col1, col2, col3 = st.columns(3)
    
    with col1:
        punctuality = kpis.get('punctuality', 0)
        st.metric("⏰ Pontualidade", f"{punctuality:.1f}%")
        
    with col2:
        consistency = kpis.get('consistency', 0)
        st.metric("📊 Consistência", f"{consistency:.1f}%")
        
    with col3:
        overtime_freq = kpis.get('overtime_frequency', 0)
        st.metric("⏱️ Frequência Horas Extras", f"{overtime_freq:.1f}%")

# Plano de ação
if compliance_data and 'action_plan' in compliance_data:
    st.markdown("---")
    st.header("📋 Plano de Ação")
    
    action_plan = compliance_data['action_plan']
    
    # Resumo do plano de ação
    summary = action_plan.get('summary', {})
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🚨 Alertas Críticos", summary.get('critical_alerts', 0))
    with col2:
        st.metric("⚠️ Alertas Urgentes", summary.get('urgent_alerts', 0))
    with col3:
        st.metric("📊 Total de Alertas", summary.get('total_alerts', 0))
    with col4:
        st.metric("💡 Recomendações", summary.get('recommendations', 0))
    
    # Ações imediatas
    immediate_actions = action_plan.get('immediate_actions', [])
    if immediate_actions:
        st.subheader("🚨 Ações Imediatas")
        for action in immediate_actions:
            level = action.get('level', '')
            if level == 'CRÍTICO':
                alert_class = 'alert-critical'
            elif level == 'ALTO':
                alert_class = 'alert-warning'
            else:
                alert_class = 'alert-success'
                
            st.markdown(f"""
            <div class="{alert_class}">
                <strong>{action.get('title', '')}</strong><br>
                {action.get('message', '')}<br>
                <em>Ação necessária: {action.get('action_required', '')}</em><br>
                <em>Prazo: {action.get('deadline', '')}</em>
            </div>
            """, unsafe_allow_html=True)
    
    # Ações urgentes
    urgent_actions = action_plan.get('urgent_actions', [])
    if urgent_actions:
        st.subheader("⚠️ Ações Urgentes")
        for action in urgent_actions:
            st.markdown(f"""
            <div class="alert-warning">
                <strong>{action.get('title', '')}</strong><br>
                {action.get('message', '')}<br>
                <em>Ação necessária: {action.get('action_required', '')}</em><br>
                <em>Prazo: {action.get('deadline', '')}</em>
            </div>
            """, unsafe_allow_html=True)

# Análise de jornada mensal
if 'jornada_mensal' in data:
    st.markdown("---")
    st.header("📊 Análise de Jornada Mensal")
    
    jornada = data['jornada_mensal']
    col1, col2 = st.columns(2)
    
    with col1:
        # Métricas de jornada
        horas_trabalhadas = jornada.get('horas_trabalhadas', 0)
        horas_contratuais = jornada.get('horas_contratuais', 0)
        diferenca = jornada.get('diferenca', 0)
        percentual = jornada.get('percentual_cumprimento', 0)
        
        st.metric("⏰ Horas Trabalhadas", f"{horas_trabalhadas:.1f}h")
        st.metric("📋 Horas Contratuais", f"{horas_contratuais:.1f}h")
        st.metric("➕ Diferença", f"{diferenca:.1f}h")
        st.metric("📈 % Cumprimento", f"{percentual:.1f}%")
    
    with col2:
        # Gráfico de pizza para comparação
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Horas Contratuais', 'Horas Extras'],
            values=[horas_contratuais, max(0, diferenca)],
            hole=.3
        )])
        fig_pie.update_layout(title="Distribuição das Horas")
        st.plotly_chart(fig_pie, use_container_width=True)

# Tabela detalhada dos dados diários
if 'analise_diaria' in data:
    st.markdown("---")
    st.header("📋 Dados Detalhados por Dia")
    
    # Recriar df_daily aqui para garantir que está disponível
    daily_data = data['analise_diaria']
    df_daily = pd.DataFrame(daily_data)
    
    # Converter datas se necessário
    if 'data' in df_daily.columns:
        df_daily['data'] = pd.to_datetime(df_daily['data'], errors='coerce')
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        show_only_issues = st.checkbox("Mostrar apenas dias com irregularidades")
    with col2:
        min_hours = st.slider("Filtrar por horas mínimas trabalhadas", 0.0, 24.0, 0.0)
    
    # Aplicar filtros
    filtered_df = df_daily.copy()
    
    if show_only_issues:
        filtered_df = filtered_df[filtered_df['observacoes'].str.contains('irregularidade', na=False)]
    
    if min_hours > 0:
        filtered_df = filtered_df[filtered_df['horas_trabalhadas'] >= min_hours]
    
    # Formatar colunas para exibição
    display_df = filtered_df.copy()
    display_df['data'] = display_df['data'].dt.strftime('%d/%m/%Y')
    display_df['horas_trabalhadas'] = display_df['horas_trabalhadas'].round(2)
    display_df['intervalo_almoco'] = display_df['intervalo_almoco'].round(2)
    
    # Renomear colunas
    column_names = {
        'data': 'Data',
        'entrada': 'Entrada',
        'saida_almoco': 'Saída Almoço',
        'retorno_almoco': 'Retorno Almoço',
        'saida': 'Saída',
        'horas_trabalhadas': 'Horas Trabalhadas',
        'intervalo_almoco': 'Intervalo Almoço',
        'observacoes': 'Observações'
    }
    display_df = display_df.rename(columns=column_names)
    
    st.dataframe(display_df, use_container_width=True)

# Exportar relatório
st.markdown("---")
st.header("📤 Exportar Relatório")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Gerar Relatório PDF"):
        st.info("Funcionalidade de exportação PDF em desenvolvimento")

with col2:
    if st.button("📧 Enviar por Email"):
        st.info("Funcionalidade de envio por email em desenvolvimento")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Dashboard de Cronoanálise da Jornada de Trabalho</p>
    <p>Desenvolvido para análise de conformidade trabalhista</p>
    <p><em>Dados atualizados em: {}</em></p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y às %H:%M")), unsafe_allow_html=True)
