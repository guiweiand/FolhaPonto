# Dashboard - Cronoanálise da Jornada de Trabalho

## 📊 Visão Geral

Este dashboard web interativo foi desenvolvido para análise detalhada da cronoanálise da jornada de trabalho, fornecendo insights sobre conformidade trabalhista, identificação de irregularidades e geração de relatórios executivos.

## 🎯 Funcionalidades

### 📈 Análise de Dados
- **Visão Geral**: Métricas principais como total de dias, horas trabalhadas e problemas de conformidade
- **Análise de Risco**: Avaliação do nível de risco trabalhista com indicadores visuais
- **KPIs de Desempenho**: Indicadores de pontualidade, consistência e frequência de horas extras
- **Análise Diária**: Gráficos interativos de horas trabalhadas e intervalos de refeição

### ⚖️ Conformidade Trabalhista
- **Verificação de Jornadas**: Identificação de jornadas excessivas (>8h e >10h)
- **Intervalos de Refeição**: Análise de adequação dos intervalos de almoço
- **Períodos de Descanso**: Verificação dos intervalos entre jornadas
- **Plano de Ação**: Alertas categorizados por criticidade com prazos definidos

### 📋 Relatórios
- **Dados Detalhados**: Tabela completa com filtros personalizáveis
- **Análise Mensal**: Comparação entre horas trabalhadas e contratuais
- **Exportação**: Funcionalidades para gerar relatórios (em desenvolvimento)

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8 ou superior (recomendado: UV Python Package Manager)
- Arquivos de dados JSON gerados pelo sistema de análise

### Opção 1: Usando UV (Recomendado)
```bash
# Executar com UV (método preferido)
uv run streamlit run app.py

# OU use os scripts automáticos:
# Windows Batch
run_dashboard_uv.bat

# Windows PowerShell  
powershell -ExecutionPolicy Bypass -File run_dashboard_uv.ps1

# Linux/Mac
./run_dashboard_uv.sh
```

### Opção 2: Script Automático (Pip tradicional)
```bash
# Execute o script batch
run_dashboard.bat

# OU execute o script PowerShell
powershell -ExecutionPolicy Bypass -File run_dashboard.ps1
```

### Opção 3: Instalação Manual (Pip tradicional)
```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar o dashboard
streamlit run app.py
```

## 📁 Estrutura de Arquivos

```
dashboard/
├── app.py                    # Aplicação principal do Streamlit
├── requirements.txt          # Dependências Python
├── run_dashboard.bat        # Script de execução (Windows Batch - Pip)
├── run_dashboard.ps1        # Script de execução (PowerShell - Pip)
├── run_dashboard_uv.bat     # Script de execução (Windows Batch - UV)
├── run_dashboard_uv.ps1     # Script de execução (PowerShell - UV)
├── run_dashboard_uv.sh      # Script de execução (Linux/Mac - UV)
└── README.md                # Documentação

Dados necessários (pasta pai):
├── timesheet_clean_final.json          # Dados limpos do timesheet
├── dashboard_data_complete.json        # Dados completos do dashboard
└── src/folhaponto/compliance_dashboard.json  # Relatório de conformidade
```

## 📊 Dados Suportados

O dashboard automaticamente detecta e carrega os seguintes arquivos de dados:

1. **timesheet_clean_final.json**: Dados principais da análise de jornada
2. **compliance_dashboard.json**: Relatório de conformidade trabalhista
3. **dashboard_data_complete.json**: Dados consolidados completos

## 🎨 Interface

### Componentes Principais:
- **Sidebar**: Informações do funcionário e seleção de dados
- **Métricas**: Cards com indicadores principais
- **Gráficos Interativos**: Visualizações usando Plotly
- **Tabelas Filtráveis**: Dados detalhados com opções de filtro
- **Alertas Visuais**: Sinalizações por cores baseadas no nível de risco

### Cores do Sistema:
- 🟢 **Verde**: Conformidade adequada
- 🟡 **Amarelo**: Atenção necessária
- 🟠 **Laranja**: Situação de risco
- 🔴 **Vermelho**: Crítico - ação imediata necessária

## 🔧 Configuração

### Variáveis de Ambiente (Opcionais)
```bash
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### Personalização
O dashboard pode ser personalizado editando o arquivo `app.py`:
- Cores e temas no CSS customizado
- Métricas e KPIs exibidos
- Filtros e visualizações
- Layout e componentes

## 📱 Responsividade

O dashboard é totalmente responsivo e funciona em:
- 💻 Desktops
- 📱 Tablets
- 📲 Smartphones

## 🛠️ Solução de Problemas

### Problemas Comuns:

1. **Erro "Arquivo não encontrado"**
   - Verifique se os arquivos JSON estão na localização correta
   - Confirme se os dados foram gerados pelo notebook de análise

2. **Erro de dependências**
   ```bash
   pip install --upgrade streamlit pandas plotly
   ```

3. **Porta 8501 em uso**
   ```bash
   streamlit run app.py --server.port 8502
   ```

4. **Erro de encoding**
   - Verifique se os arquivos JSON estão em UTF-8

## 📈 Performance

### Otimizações Implementadas:
- Cache de dados com `@st.cache_data`
- Carregamento lazy de arquivos grandes
- Componentes otimizados do Plotly

## 🔐 Segurança

- Dados processados localmente
- Nenhuma informação enviada para servidores externos
- Execução em ambiente isolado

## 📞 Suporte

Para suporte e melhorias:
1. Verifique a documentação
2. Consulte os logs de erro no terminal
3. Reporte problemas com detalhes do erro

## 📄 Licença

Desenvolvido para análise de conformidade trabalhista.
Uso interno da organização.