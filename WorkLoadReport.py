# %% ------------------------------------------------------------------------------------------
# imports
#streamlit run WorkLoadReport.py
from Functions.API_Notion import API_Notion
import streamlit as st
import pandas as pd
import plotly.express as px

# %% ------------------------------------------------------------------------------------------
# streamlit setup
st.set_page_config(page_title="Work Load Report", layout="wide")
st.title('Work Load Report')

# Adicionar botão de atualização
if st.button('🔄 Atualizar Dados'):
    st.cache_data.clear()
    st.rerun()

#%% ------------------------------------------------------------------------------------------
# lista de urls
urls = {
    'studying_calendar': {
        'dataset_id': st.secrets["notion"]["studying_calendar_dataset_id"],
        'token': st.secrets["notion"]["studying_calendar_token"]
    },
    'working_calendar': {
        'dataset_id': st.secrets["notion"]["working_calendar_dataset_id"],
        'token': st.secrets["notion"]["working_calendar_token"]
    },
    'workout_calendar': {
        'dataset_id': st.secrets["notion"]["workout_calendar_dataset_id"],
        'token': st.secrets["notion"]["workout_calendar_token"]
    }
}

# %% ------------------------------------------------------------------------------------------
# função para extrair dados do Notion
@st.cache_data(ttl=300)  # Cache por 5 minutos
def api_notion_iterativa():
    try:
        dados = {}
        for calendar_type, config in urls.items():
            # Extrair dados do Notion
            df_temp = API_Notion(config['dataset_id'], config['token'])
            dados[calendar_type] = df_temp
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar dados do Notion: {str(e)}")
        return None

# Carregar dados
dados = api_notion_iterativa()

if dados is None:
    st.stop()

df_studying = dados['studying_calendar']
df_working = dados['working_calendar']
df_workout = dados['workout_calendar']

# %% ------------------------------------------------------------------------------------------
# handeling
dfs = {
    'studying': df_studying,
    'working': df_working,
    'workout': df_workout
}

for tipo, df in dfs.items():
    dfs[tipo] = df[['properties']]
    dfs[tipo] = pd.json_normalize(dfs[tipo]['properties'])
    dfs[tipo] = dfs[tipo][['Date.date.start', 'Date.date.end']]
    dfs[tipo].rename(columns={'Date.date.start': 'dt_start', 'Date.date.end': 'dt_end'}, inplace=True)
    dfs[tipo]['dt_start'] = pd.to_datetime(dfs[tipo]['dt_start'])
    dfs[tipo]['dt_end'] = pd.to_datetime(dfs[tipo]['dt_end'])

    dfs[tipo]['duration'] = dfs[tipo]['dt_end'] - dfs[tipo]['dt_start']
    dfs[tipo]['duration'] = dfs[tipo]['duration'].dt.total_seconds() / 3600  # converte para horas
    dfs[tipo]['type'] = tipo

    dfs[tipo]['date'] = dfs[tipo]['dt_start'].dt.strftime('%d/%m/%Y')
    dfs[tipo]['year'] = dfs[tipo]['dt_start'].dt.year
    dfs[tipo]['month'] = dfs[tipo]['dt_start'].dt.month
    dfs[tipo]['week'] = dfs[tipo]['dt_start'].dt.isocalendar().week

# Atualizar as variáveis originais
df_studying = dfs['studying']
df_working = dfs['working']
df_workout = dfs['workout']

# %% ------------------------------------------------------------------------------------------
# handeling 2
# juntar os dados
df_workload = pd.concat([df_studying, df_working, df_workout])

# Criar a tabela dinâmica
pivot_table = pd.pivot_table(
    df_workload,
    values='duration',
    index=['year', 'month', 'week', 'date'],
    columns='type',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='Grand Total'
)

# Converter as colunas para timedelta
for col in pivot_table.columns:
    pivot_table[col] = pd.to_timedelta(pivot_table[col], unit='h')

# Converter os índices para string para evitar problemas de tipo
pivot_table.index = pivot_table.index.set_levels([
    pivot_table.index.levels[0].astype(str),  # year
    pivot_table.index.levels[1].astype(str),  # month
    pivot_table.index.levels[2].astype(str),  # week
    pivot_table.index.levels[3].astype(str)   # date
])

# Função para formatar o tempo
def format_time(td):
    total_hours = td.total_seconds() / 3600
    hours = int(total_hours)
    minutes = int((total_hours - hours) * 60)
    return f"{hours}h {minutes}min"

# %% ------------------------------------------------------------------------------------------
# streamlit interface
# Adicionar filtros no sidebar
st.sidebar.header('Filtros')

# Adicionar seletor de período
time_period = st.sidebar.selectbox(
    'Agrupar por',
    ['date', 'week', 'month', 'year']
)

# Obter valores únicos para os filtros
years = sorted(pivot_table.index.get_level_values('year').unique())
months = sorted(pivot_table.index.get_level_values('month').unique())
weeks = sorted(pivot_table.index.get_level_values('week').unique())

# Criar os filtros
selected_year = st.sidebar.selectbox('Ano', ['Todos'] + list(years))
selected_month = st.sidebar.selectbox('Mês', ['Todos'] + list(months))
selected_week = st.sidebar.selectbox('Semana', ['Todos'] + list(weeks))

# Aplicar filtros
filtered_table = pivot_table.copy()

if selected_year != 'Todos':
    filtered_table = filtered_table[filtered_table.index.get_level_values('year') == selected_year]
if selected_month != 'Todos':
    filtered_table = filtered_table[filtered_table.index.get_level_values('month') == selected_month]
if selected_week != 'Todos':
    filtered_table = filtered_table[filtered_table.index.get_level_values('week') == selected_week]

# Remover a última linha (total) antes de mostrar
filtered_table_display = filtered_table.iloc[:-1] if len(filtered_table) > 1 else filtered_table

# níveis do índice em função do período selecionado
if time_period == 'year':
    filtered_table_display = filtered_table_display.groupby(level='year').sum()
elif time_period == 'month':
    filtered_table_display = filtered_table_display.groupby(level=['month']).sum()
elif time_period == 'week':
    filtered_table_display = filtered_table_display.groupby(level=['week']).sum()

# Mostrar totais dos dados filtrados
if len(filtered_table) > 0:
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcular os totais somando todas as linhas exceto a última (que já é um total)
    data_for_totals = filtered_table.iloc[:-1] if len(filtered_table) > 1 else filtered_table
    
    with col1:
        study_total = data_for_totals['studying'].sum()
        st.metric("Total Studying", format_time(study_total))
    with col2:
        work_total = data_for_totals['working'].sum()
        st.metric("Total Working", format_time(work_total))
    with col3:
        workout_total = data_for_totals['workout'].sum()
        st.metric("Total Workout", format_time(workout_total))
    with col4:
        total_workload = study_total + work_total + workout_total
        st.metric("Total Workload", format_time(total_workload))

# Formatar a tabela para exibição
formatted_table = filtered_table_display.copy()
for col in formatted_table.columns:
    formatted_table[col] = formatted_table[col].apply(format_time)

# Mostrar a tabela filtrada
st.subheader('Tabela Detalhada')
st.dataframe(
    formatted_table,
    use_container_width=True,
    hide_index=False
)
# %%
