import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import base64
import tempfile
from pathlib import Path
from pdf_processor import process_uploaded_pdf

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
        color: #c62828;
        font-weight: 500;
    }
    .alert-warning {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
        color: #e65100;
        font-weight: 500;
    }
    .alert-success {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
        color: #2e7d32;
        font-weight: 500;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 2px dashed #dee2e6;
        margin-bottom: 1rem;
    }
    .upload-success {
        background-color: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
    .upload-error {
        background-color: #f8d7da;
        border-color: #dc3545;
        color: #721c24;
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

def display_pdf(file_path, width="100%", height="900px"):
    """Display PDF file in Streamlit with customizable size"""
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # PDF viewer HTML with customizable dimensions
        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" 
                width="{width}" height="{height}" type="application/pdf"
                style="border: none;">
        </iframe>
        """
        
        st.markdown(pdf_display, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo PDF não encontrado: {file_path}")
    except Exception as e:
        st.error(f"Erro ao carregar PDF: {str(e)}")

def get_risk_color(level):
    """Retorna cor baseada no nível de risco"""
    colors = {
        'BAIXO': '#4CAF50',
        'MÉDIO': '#FF9800', 
        'ALTO': '#FF5722',
        'CRÍTICO': '#F44336'
    }
    return colors.get(level, '#757575')

def find_data_file():
    """Busca o arquivo de dados unificado timesheet_webapp_data.json"""
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent
    
    # Locais possíveis para o arquivo
    possible_locations = [
        # Diretório pai do projeto
        parent_dir,
        # Diretório src/folhaponto
        parent_dir / "src" / "folhaponto",
        # Diretório atual
        current_dir,
    ]
    
    # Arquivo específico a buscar
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
        # Converter formato "21/05/25 qua" para datetime
        try:
            data_parts = data_str.split(' ')[0]  # Pegar apenas a parte da data
            day, month, year = data_parts.split('/')
            # Assumir que anos de 2 dígitos são 20XX
            if len(year) == 2:
                year = '20' + year
            data_iso = f"{year}-{month}-{day}"
            
            # Converter horas trabalhadas de "HH:MM" para decimal
            jornada_str = entry.get('jornada_diaria', '00:00')
            horas_trabalhadas = time_to_hours(jornada_str)
            
            # Converter intervalo de refeição
            refeicao_str = entry.get('total_refeicao', '00:00')
            intervalo_almoco = time_to_hours(refeicao_str)
            
            # Criar observações baseadas no tipo e problemas
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
                'entrada': entry.get('jornada_inicio', ''),
                'saida_almoco': '',  # Não disponível nos dados atuais
                'retorno_almoco': '',  # Não disponível nos dados atuais
                'saida': entry.get('jornada_fim', ''),
                'horas_trabalhadas': horas_trabalhadas,
                'intervalo_almoco': intervalo_almoco,
                'observacoes': observacoes
            }
            
            daily_analysis.append(daily_entry)
            
        except (ValueError, IndexError, AttributeError):
            # Pular entradas com problemas na data
            continue
    
    return daily_analysis

def handle_pdf_upload(uploaded_file):
    """Handle the uploaded PDF file and process it"""
    if uploaded_file is not None:
        try:
            # Create a temporary file to save the uploaded PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name
            
            # Process the PDF using our processor
            webapp_data, status_msg = process_uploaded_pdf(temp_file_path)
            
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
            return webapp_data, status_msg
            
        except Exception as e:
            return None, f"❌ Erro no processamento: {str(e)}"
    
    return None, "❌ Nenhum arquivo enviado"

def refresh_dashboard_data():
    """Force refresh of the dashboard data"""
    # Clear any cached data
    if 'data_cache' in st.session_state:
        del st.session_state.data_cache
    
    # Trigger a rerun to refresh the dashboard
    st.rerun()

# Título principal
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard - Cronoanálise da Jornada de Trabalho</h1>
    <p>Análise completa de conformidade trabalhista e gestão de jornadas</p>
</div>
""", unsafe_allow_html=True)

# Inicializar o estado da página se não existir
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"

# Initialize session state for upload status
if 'upload_status' not in st.session_state:
    st.session_state.upload_status = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# === SIDEBAR FILE UPLOAD SECTION ===
st.sidebar.header("📤 Upload Nova Ficha de Ponto")

uploaded_file = st.sidebar.file_uploader(
    "Selecione o arquivo PDF da ficha de ponto:",
    type=['pdf'],
    help="Faça upload de um arquivo PDF contendo a ficha de ponto para análise."
)

if uploaded_file is not None:
    st.sidebar.info(f"📄 Arquivo selecionado: {uploaded_file.name}")
    
    # Process button
    if st.sidebar.button("🔄 Processar Arquivo", use_container_width=True, type="primary"):
        with st.sidebar:
            with st.spinner("Processando arquivo PDF..."):
                webapp_data, status_msg = handle_pdf_upload(uploaded_file)
                
                if webapp_data:
                    st.session_state.upload_status = "success"
                    st.session_state.processing_complete = True
                    st.sidebar.success("✅ Processamento concluído!")
                    st.sidebar.info("📊 Dashboard será atualizado com os novos dados.")
                    # Force refresh to show new data
                    st.rerun()
                else:
                    st.session_state.upload_status = "error"
                    st.sidebar.error("❌ Erro no processamento!")
                    st.sidebar.error(status_msg)

# Display upload status
if st.session_state.upload_status == "success":
    st.sidebar.success("✅ Último upload processado com sucesso!")
    if st.sidebar.button("🔄 Novo Upload", use_container_width=True):
        st.session_state.upload_status = None
        st.session_state.processing_complete = False
        st.rerun()
elif st.session_state.upload_status == "error":
    st.sidebar.error("❌ Erro no último upload!")
    if st.sidebar.button("🔄 Tentar Novamente", use_container_width=True):
        st.session_state.upload_status = None
        st.rerun()

st.sidebar.markdown("---")

# === DATA LOADING SECTION ===
# Try to load data, with fallback handling
data_file_path = find_data_file()
data = None

if data_file_path:
    data = load_json_data(data_file_path)

if data is None:
    st.sidebar.warning("⚠️ Nenhum dado carregado")
    st.error("Arquivo de dados 'timesheet_webapp_data.json' não encontrado!")
    st.info("**Opções disponíveis:**")
    st.info("1. 📤 Faça upload de uma ficha de ponto PDF usando o formulário na barra lateral")
    st.info("2. 📁 Certifique-se de que existe um arquivo timesheet_webapp_data.json em:")
    st.info("   - Diretório raiz do projeto")
    st.info("   - src/folhaponto/")
    st.info("   - dashboard/")
    st.stop()

# Sidebar para informações do arquivo
st.sidebar.header("📁 Dados Atuais")
st.sidebar.success("✅ timesheet_webapp_data.json")
if data_file_path:
    st.sidebar.write(f"**Localização:** {Path(data_file_path).name}")
    
    # Get last modified time
    mod_time = datetime.fromtimestamp(os.path.getmtime(data_file_path))
    st.sidebar.write(f"**Última atualização:** {mod_time.strftime('%d/%m/%Y %H:%M')}")

# Extrair informações básicas
employee_info = data.get('employee', {})
company_info = data.get('company', {})
period_info = data.get('period', 'N/A')

# Calcular summary_info a partir dos dados disponíveis
timesheet_data = data.get('timesheet_data', [])
working_days = len([entry for entry in timesheet_data if entry.get('tipo') == 'Trabalho'])
total_days = len(timesheet_data)

# Calcular total de horas trabalhadas
total_hours = 0
total_meal_hours = 0
for entry in timesheet_data:
    if entry.get('jornada_diaria'):
        total_hours += time_to_hours(entry.get('jornada_diaria', '00:00'))
    if entry.get('total_refeicao'):
        total_meal_hours += time_to_hours(entry.get('total_refeicao', '00:00'))

# Pegar problemas de conformidade
compliance_summary = data.get('compliance_summary', {})
issues_count = compliance_summary.get('total_compliance_issues', 0)

summary_info = {
    'total_days': total_days,
    'work_days': working_days,
    'total_hours_worked': total_hours,
    'total_meal_break_hours': total_meal_hours,
    'compliance_issues_count': issues_count
}

# Sidebar - Informações do funcionário
st.sidebar.markdown("---")
st.sidebar.header("👤 Informações do Funcionário")
st.sidebar.write(f"**Nome:** {employee_info.get('name', 'N/A')}")
st.sidebar.write(f"**CPF:** {employee_info.get('cpf', 'N/A')}")
st.sidebar.write(f"**Empresa:** {company_info.get('name', 'N/A')}")
st.sidebar.write(f"**CNPJ:** {company_info.get('cnpj', 'N/A')}")
st.sidebar.write(f"**Período:** {period_info}")

# Botão para visualizar PDF
st.sidebar.markdown("---")
st.sidebar.header("📄 Visualizar PDF")
if st.sidebar.button("📋 Ver Ficha de Ponto (PDF)", use_container_width=True):
    # Caminho para o arquivo PDF
    pdf_path = Path(__file__).parent.parent / "test_sample" / "Ficha_Ponto_Simplificada_André_Luis.pdf"
    
    if pdf_path.exists():
        st.sidebar.success("PDF carregado com sucesso!")
        # Navegar para a página do PDF
        st.session_state.current_page = "pdf_viewer"
        st.session_state.pdf_path = str(pdf_path)
        st.rerun()
    else:
        st.sidebar.error(f"PDF não encontrado: {pdf_path}")

# Verificar se há dados de compliance (agora tudo está no mesmo arquivo)
compliance_data = data  # Todos os dados estão no mesmo arquivo agora

# === NAVEGAÇÃO ENTRE PÁGINAS ===
if st.session_state.current_page == "pdf_viewer":
    # PÁGINA DO PDF
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Voltar ao Dashboard", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    
    with col2:
        st.markdown("### 📄 Ficha de Ponto - André Luis")
    
    with col3:
        st.write("")  # Espaço vazio para equilibrar
    
    # Exibir o PDF em tela cheia
    if 'pdf_path' in st.session_state:
        # Usar toda a largura disponível e altura maior
        display_pdf(st.session_state.pdf_path, width="100%", height="1000px")

else:
    # PÁGINA HOME (DASHBOARD PRINCIPAL)
    
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

    # Análise de risco (adaptado para nova estrutura)
    if compliance_data and 'compliance_summary' in compliance_data:
        st.markdown("---")
        st.header("🎯 Análise de Risco")
        
        compliance_summary = compliance_data['compliance_summary']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Determinar nível de risco baseado na taxa de conformidade
            compliance_rate = compliance_summary.get('compliance_rate', 0)
            total_issues = compliance_summary.get('total_compliance_issues', 0)
            
            if total_issues > 20:
                risk_level = 'CRÍTICO'
                risk_color = '#F44336'
            elif total_issues > 10:
                risk_level = 'ALTO'
                risk_color = '#FF5722'
            elif total_issues > 5:
                risk_level = 'MÉDIO'
                risk_color = '#FF9800'
            else:
                risk_level = 'BAIXO'
                risk_color = '#4CAF50'
                
            st.markdown(f"""
            <div style='text-align: center; padding: 1rem; background: {risk_color}; color: white; border-radius: 10px;'>
                <h3>Nível de Risco</h3>
                <h1>{risk_level}</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric("📈 Taxa de Conformidade", f"{abs(compliance_rate):.1f}%")
        
        with col3:
            violations = compliance_summary.get('total_compliance_issues', 0)
            st.metric("🚨 Total de Violações", violations)

    # Gráficos de análise diária
    if 'timesheet_data' in data:
        st.markdown("---")
        st.header("📈 Análise Diária")
        
        # Processar dados do timesheet para o formato de análise diária
        daily_data = process_timesheet_data_for_charts(data['timesheet_data'])
        
        if daily_data:
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
    if compliance_data and 'metricas_qualidade' in compliance_data:
        st.markdown("---")
        st.header("🎯 Indicadores de Desempenho (KPIs)")
        
        kpis = compliance_data['metricas_qualidade']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            punctuality = kpis.get('pontualidade', 0)
            st.metric("⏰ Pontualidade", f"{punctuality:.1f}%")
            
        with col2:
            consistency = kpis.get('cumprimento_jornada', 0)
            st.metric("📊 Cumprimento Jornada", f"{consistency:.1f}%")
            
        with col3:
            regularity = kpis.get('regularidade_intervalos', 0)
            st.metric("🍽️ Regularidade Intervalos", f"{regularity:.1f}%")

    # Plano de ação baseado nos problemas identificados
    if compliance_data and 'detailed_problems' in compliance_data:
        st.markdown("---")
        st.header("📋 Plano de Ação")
        
        detailed_problems = compliance_data['detailed_problems']
        
        # Resumo do plano de ação
        excessive_hours = len(detailed_problems.get('excessive_daily_hours', []))
        meal_breaks = len(detailed_problems.get('insufficient_meal_breaks', []))
        rest_periods = len(detailed_problems.get('insufficient_rest_periods', []))
        total_issues = excessive_hours + meal_breaks + rest_periods
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            critical_alerts = excessive_hours  # Considerar horas excessivas como críticas
            st.metric("🚨 Alertas Críticos", critical_alerts)
        with col2:
            urgent_alerts = rest_periods  # Considerar descanso insuficiente como urgente
            st.metric("⚠️ Alertas Urgentes", urgent_alerts)
        with col3:
            st.metric("📊 Total de Alertas", total_issues)
        with col4:
            recommendations = min(5, total_issues)  # Limitar a 5 recomendações
            st.metric("💡 Recomendações", recommendations)
        
        # Ações imediatas para horas excessivas
        if excessive_hours > 0:
            st.subheader("🚨 Ações Imediatas - Horas Excessivas")
            st.markdown(f"""
            <div class="alert-critical">
                <strong>Jornadas Excessivas Detectadas</strong><br>
                {excessive_hours} dias com jornada superior ao limite legal foram identificados.<br>
                <em>Ação necessária: Revisar escalas e implementar controle de jornada</em><br>
                <em>Prazo: Imediato</em>
            </div>
            """, unsafe_allow_html=True)
            
            # Visão detalhada dos alertas de horas excessivas
            with st.expander("📊 Ver Detalhes das Jornadas Excessivas", expanded=False):
                st.markdown("### 🕐 JORNADAS DIÁRIAS EXCESSIVAS:")
                
                for i, issue in enumerate(detailed_problems.get('excessive_daily_hours', []), 1):
                    details = issue.get('details', '')
                    # Extrair informações do texto de detalhes
                    if 'Jornada trabalhada' in details and 'excesso:' in details:
                        try:
                            parts = details.split(', ')
                            jornada_part = parts[0].replace('Jornada trabalhada ', '')
                            excesso_part = parts[1].replace('excesso: ', '')
                            
                            # Tentar extrair a data do timesheet_data correspondente
                            timesheet_data = compliance_data.get('timesheet_data', [])
                            data_info = "Data não identificada"
                            
                            # Buscar a entrada correspondente no timesheet
                            for entry in timesheet_data:
                                if entry.get('jornada_diaria') == jornada_part:
                                    data_info = entry.get('data', 'Data não identificada')
                                    break
                            
                            # Layout horizontal compacto para as informações da data
                            st.markdown(f"""
                            <div style='display: inline-flex; gap: 20px; padding: 8px 12px; margin: 2px 0; background-color: #ffebee; border-left: 5px solid #f44336; border-radius: 5px; color: #c62828; font-weight: 500; width: fit-content;'>
                                <span style='min-width: 140px;'><strong>📅 {data_info}</strong></span>
                                <span style='min-width: 150px;'><strong>⏰ Trabalhada:</strong> {jornada_part}</span>
                                <span style='min-width: 130px;'><strong>✅ Normal:</strong> 08:00</span>
                                <span style='min-width: 120px;'><strong>⚠️ Excesso:</strong> {excesso_part}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except (IndexError, ValueError):
                            st.markdown(f"""
                            <div style='padding: 8px 12px; margin: 2px 0; background-color: #ffebee; border-left: 5px solid #f44336; border-radius: 5px; color: #c62828; font-weight: 500;'>
                                <strong>📅 Registro {i}:</strong> {details}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='padding: 8px 12px; margin: 2px 0; background-color: #ffebee; border-left: 5px solid #f44336; border-radius: 5px; color: #c62828; font-weight: 500;'>
                            <strong>📅 Registro {i}:</strong> {details}
                        </div>
                        """, unsafe_allow_html=True)
        
        # Ações urgentes para períodos de descanso
        if rest_periods > 0:
            st.subheader("⚠️ Ações Urgentes - Períodos de Descanso")
            st.markdown(f"""
            <div class="alert-warning">
                <strong>Descanso Insuficiente Entre Jornadas</strong><br>
                {rest_periods} ocorrências de descanso inferior a 11 horas entre jornadas.<br>
                <em>Ação necessária: Ajustar horários para garantir descanso adequado</em><br>
                <em>Prazo: 48 horas</em>
            </div>
            """, unsafe_allow_html=True)
            
            # Visão detalhada dos alertas de descanso insuficiente
            with st.expander("📊 Ver Detalhes dos Períodos de Descanso Insuficientes", expanded=False):
                st.markdown("### 😴 PERÍODOS DE DESCANSO INSUFICIENTES:")
                
                for i, issue in enumerate(detailed_problems.get('insufficient_rest_periods', []), 1):
                    details = issue.get('details', '')
                    # Extrair informações do texto de detalhes
                    if 'Período de descanso:' in details and 'necessário:' in details:
                        try:
                            parts = details.split(', ')
                            descanso_part = parts[0].replace('Período de descanso: ', '')
                            necessario_part = parts[1].replace('necessário: ', '')
                            
                            # Calcular tempo faltante
                            try:
                                descanso_hours = time_to_hours(descanso_part)
                                necessario_hours = time_to_hours(necessario_part)
                                faltante_hours = necessario_hours - descanso_hours
                                faltante_str = hours_to_time(faltante_hours)
                            except:
                                faltante_str = "Cálculo indisponível"
                            
                            # Layout horizontal compacto para as informações do período
                            st.markdown(f"""
                            <div style='display: inline-flex; gap: 20px; padding: 8px 12px; margin: 2px 0; background-color: #fff3e0; border-left: 5px solid #ff9800; border-radius: 5px; color: #e65100; font-weight: 500; width: fit-content;'>
                                <span style='min-width: 140px;'><strong>📅 Período {i}</strong></span>
                                <span style='min-width: 150px;'><strong>😴 Obtido:</strong> {descanso_part}</span>
                                <span style='min-width: 130px;'><strong>✅ Obrigatório:</strong> {necessario_part}</span>
                                <span style='min-width: 120px;'><strong>❌ Faltante:</strong> {faltante_str}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except (IndexError, ValueError):
                            st.markdown(f"""
                            <div style='padding: 8px 12px; margin: 2px 0; background-color: #fff3e0; border-left: 5px solid #ff9800; border-radius: 5px; color: #e65100; font-weight: 500;'>
                                <strong>📅 Período {i}:</strong> {details}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='padding: 8px 12px; margin: 2px 0; background-color: #fff3e0; border-left: 5px solid #ff9800; border-radius: 5px; color: #e65100; font-weight: 500;'>
                            <strong>📅 Período {i}:</strong> {details}
                        </div>
                        """, unsafe_allow_html=True)
            
        # Ações para intervalos de refeição
        if meal_breaks > 0:
            st.subheader("📋 Ações Preventivas - Intervalos de Refeição")
            st.markdown(f"""
            <div class="alert-warning">
                <strong>Intervalos de Refeição Irregulares</strong><br>
                {meal_breaks} ocorrências de intervalos inadequados.<br>
                <em>Ação necessária: Orientar funcionário sobre obrigatoriedade dos intervalos</em><br>
                <em>Prazo: 7 dias</em>
            </div>
            """, unsafe_allow_html=True)
            
            # Visão detalhada dos alertas de intervalos de refeição
            with st.expander("📊 Ver Detalhes dos Intervalos de Refeição Irregulares", expanded=False):
                st.markdown("### 🍽️ INTERVALOS DE REFEIÇÃO INSUFICIENTES:")
                
                for i, issue in enumerate(detailed_problems.get('insufficient_meal_breaks', []), 1):
                    details = issue.get('details', '')
                    # Extrair informações do texto de detalhes
                    if 'Intervalo de refeição:' in details and 'necessário:' in details:
                        try:
                            parts = details.split(', ')
                            intervalo_part = parts[0].replace('Intervalo de refeição: ', '')
                            necessario_part = parts[1].replace('necessário: ', '')
                            
                            # Tentar extrair a data do timesheet_data correspondente
                            timesheet_data = compliance_data.get('timesheet_data', [])
                            data_info = "Data não identificada"
                            
                            # Buscar a entrada correspondente no timesheet (sem intervalo ou com intervalo insuficiente)
                            for entry in timesheet_data:
                                if not entry.get('total_refeicao') or entry.get('total_refeicao') == '':
                                    data_info = entry.get('data', 'Data não identificada')
                                    break
                            
                            # Layout horizontal compacto para as informações da data
                            st.markdown(f"""
                            <div style='display: inline-flex; gap: 20px; padding: 8px 12px; margin: 2px 0; background-color: #fff3e0; border-left: 5px solid #ff9800; border-radius: 5px; color: #e65100; font-weight: 500; width: fit-content;'>
                                <span style='min-width: 140px;'><strong>📅 {data_info}</strong></span>
                                <span style='min-width: 150px;'><strong>🍽️ Registrado:</strong> {intervalo_part}</span>
                                <span style='min-width: 130px;'><strong>✅ Obrigatório:</strong> {necessario_part}</span>
                                <span style='min-width: 120px;'><strong>⚠️ Status:</strong> Não conforme</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except (IndexError, ValueError):
                            st.markdown(f"""
                            <div style='padding: 8px 12px; margin: 2px 0; background-color: #fff3e0; border-left: 5px solid #ff9800; border-radius: 5px; color: #e65100; font-weight: 500;'>
                                <strong>📅 Ocorrência {i}:</strong> {details}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='padding: 8px 12px; margin: 2px 0; background-color: #fff3e0; border-left: 5px solid #ff9800; border-radius: 5px; color: #e65100; font-weight: 500;'>
                            <strong>📅 Ocorrência {i}:</strong> {details}
                        </div>
                        """, unsafe_allow_html=True)

    # Análise de jornada mensal
    if 'period_totals' in data:
        st.markdown("---")
        st.header("📊 Análise de Jornada Mensal")
        
        period_totals = data['period_totals']
        col1, col2 = st.columns(2)
        
        with col1:
            # Métricas de jornada
            total_hours_str = period_totals.get('total_working_hours', '0:00')
            total_minutes = period_totals.get('total_working_minutes', 0)
            horas_trabalhadas = total_minutes / 60
            
            # Calcular horas contratuais (assumindo 8h/dia para dias trabalhados)
            working_days = summary_info.get('work_days', 0)
            horas_contratuais = working_days * 8
            diferenca = horas_trabalhadas - horas_contratuais
            percentual = (horas_trabalhadas / horas_contratuais * 100) if horas_contratuais > 0 else 0
            
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
    if 'timesheet_data' in data:
        st.markdown("---")
        st.header("📋 Dados Detalhados por Dia")
        
        # Processar dados do timesheet para exibição
        daily_data = process_timesheet_data_for_charts(data['timesheet_data'])
        
        if daily_data:
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
                filtered_df = filtered_df[filtered_df['observacoes'].str.contains('irregularidade|Excesso|feriado', na=False)]
            
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
        else:
            st.warning("Não há dados de timesheet válidos para exibir.")

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
