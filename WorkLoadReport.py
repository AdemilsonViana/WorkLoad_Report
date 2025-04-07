# %% ------------------------------------------------------------------------------------------
# imports
#streamlit run WorkLoadReport.py
from Functions.APIs.notion import api_notion_iterativa
from Functions.Utils.data_processing import format_time
import streamlit as st
import pandas as pd
import plotly.express as px

# %% ------------------------------------------------------------------------------------------
# streamlit setup
st.set_page_config(page_title="Workload Report", layout="wide")
st.title('Workload Report')

# Adicionar botão de atualização
if st.button('🔄 Atualizar Dados'):
    st.cache_data.clear()
    st.rerun()

# %% ------------------------------------------------------------------------------------------
# Configuração das URLs do Notion
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
# Extração de dados do Notion
# O decorador @st.cache_data armazena os resultados da função por 5 minutos (300 segundos)
# Isso evita chamadas desnecessárias à API do Notion e melhora a performance
@st.cache_data(ttl=300)
def load_notion_data():
    # Esta função encapsula a chamada à API do Notion
    # O parâmetro 'urls' contém as configurações necessárias para cada calendário
    return api_notion_iterativa(urls)

# Carregar os dados usando a função cacheada
dados = load_notion_data()
if dados is None:
    st.stop()

# %% ------------------------------------------------------------------------------------------
# Processamento inicial dos dados
# Processar cada dataframe
dfs = {}
for tipo, df in dados.items():
    # Extrair e normalizar os dados
    df = df[['properties']]
    df = pd.json_normalize(df['properties'])
    df = df[['Date.date.start', 'Date.date.end']]
    df.rename(columns={'Date.date.start': 'dt_start', 'Date.date.end': 'dt_end'}, inplace=True)
    
    # Converter para datetime e calcular duração
    df['dt_start'] = pd.to_datetime(df['dt_start'])
    df['dt_end'] = pd.to_datetime(df['dt_end'])
    df['duration'] = (df['dt_end'] - df['dt_start']).dt.total_seconds() / 3600
    
    # Adicionar colunas de tempo
    df['type'] = tipo
    df['date'] = df['dt_start'].dt.strftime('%d/%m/%Y')
    df['year'] = df['dt_start'].dt.year
    df['month'] = df['dt_start'].dt.month
    df['week'] = df['dt_start'].dt.isocalendar().week
    df['weekday'] = df['dt_start'].dt.dayofweek + 1
    
    dfs[tipo] = df

df_workload = pd.concat(dfs.values())

# %% ------------------------------------------------------------------------------------------
# Criação das tabelas pivot
# Tabela pivot semanal
weekday_names = {
    1: 'Segunda', 2: 'Terça', 3: 'Quarta', 4: 'Quinta',
    5: 'Sexta', 6: 'Sábado', 7: 'Domingo'
}

weekday_pivot = pd.pivot_table(
    df_workload,
    values='duration',
    index=['year', 'week'],
    columns='weekday',
    aggfunc='sum',
    fill_value=0
)

# Adicionar métricas à tabela pivot semanal
# Primeiro, garantir que estamos usando apenas as colunas que existem
available_numbers = [num for num in range(1, 8) if num in weekday_pivot.columns]
weekday_pivot['Média'] = weekday_pivot[available_numbers].mean(axis=1)

# Calcular média ponderada diretamente usando os números dos dias
weekday_pivot['Média Ponderada'] = (
    weekday_pivot[available_numbers].multiply(available_numbers).sum(axis=1) / 
    weekday_pivot[available_numbers].sum(axis=1)
).round(2)

weekday_pivot['Min - Max'] = (
    weekday_pivot[available_numbers].max(axis=1) - 
    weekday_pivot[available_numbers].min(axis=1)
)

# Renomear as colunas dos dias para os nomes em português
weekday_pivot = weekday_pivot.rename(columns=weekday_names)

# Tabela pivot detalhada
pivot_table = pd.pivot_table(
    df_workload,
    values='duration',
    index=['year', 'month', 'week', 'date'],
    columns='type',
    aggfunc='sum',
    fill_value=0
)

# Adicionar a coluna Grand Total sem criar a linha
pivot_table['Grand Total'] = pivot_table.sum(axis=1)

# Converter para timedelta
for col in pivot_table.columns:
    pivot_table[col] = pd.to_timedelta(pivot_table[col], unit='h')

# Converter índices para string
pivot_table.index = pivot_table.index.set_levels([
    pivot_table.index.levels[0].astype(str),
    pivot_table.index.levels[1].astype(str),
    pivot_table.index.levels[2].astype(str),
    pivot_table.index.levels[3].astype(str)
])

# %% ------------------------------------------------------------------------------------------
# Interface Streamlit - Filtros
st.sidebar.header('Filters')

years = sorted(pivot_table.index.get_level_values('year').unique())
months = sorted(pivot_table.index.get_level_values('month').unique())
weeks = sorted(pivot_table.index.get_level_values('week').unique())

selected_year = st.sidebar.selectbox('Year', ['All'] + list(years))
selected_month = st.sidebar.selectbox('Month', ['All'] + list(months))
selected_weeks = st.sidebar.multiselect('Weeks', weeks, default=None)

# Aplicação dos filtros
# Filtrar tabela semanal
filtered_weekday_pivot = weekday_pivot.copy()
if selected_year != 'All':
    filtered_weekday_pivot = filtered_weekday_pivot[
        filtered_weekday_pivot.index.get_level_values('year').astype(str) == selected_year
    ]
if selected_weeks:
    filtered_weekday_pivot = filtered_weekday_pivot[
        filtered_weekday_pivot.index.get_level_values('week').astype(str).isin(selected_weeks)
    ]

# Filtrar tabela detalhada
filtered_table = pivot_table.copy()
if selected_year != 'All':
    filtered_table = filtered_table[filtered_table.index.get_level_values('year') == selected_year]
if selected_month != 'All':
    filtered_table = filtered_table[
        filtered_table.index.get_level_values('month').astype(str) == str(selected_month)
    ]
if selected_weeks:
    filtered_table = filtered_table[filtered_table.index.get_level_values('week').astype(str).isin(selected_weeks)]

# Após aplicar todos os filtros, ordenar por data
filtered_table = filtered_table.sort_index(ascending=False)

# %% ------------------------------------------------------------------------------------------
# Layout
# Detailed table com seletor entre os cartões e a tabela
st.subheader('Workload distribution')
# Métricas totais
if len(filtered_table) > 0:
    col1, col2, col3, col4 = st.columns(4)
    data_for_totals = filtered_table
    
    with col1:
        study_total = data_for_totals['studying_calendar'].sum()
        st.metric("Total Studying", format_time(study_total))
    with col2:
        work_total = data_for_totals['working_calendar'].sum()
        st.metric("Total Working", format_time(work_total))
    with col3:
        workout_total = data_for_totals['workout_calendar'].sum()
        st.metric("Total Workout", format_time(workout_total))
    with col4:
        total_workload = study_total + work_total + workout_total
        st.metric("Total Workload", format_time(total_workload))

# Mover o seletor para aqui, antes do processamento da tabela
time_period = st.selectbox('Agrupar por', ['date', 'week', 'month', 'year'])

# Preparar tabela detalhada
filtered_table_display = filtered_table

# Agrupar por período selecionado
if time_period == 'year':
    filtered_table_display = filtered_table_display.groupby(level='year').sum().sort_index(ascending=False)
elif time_period == 'month':
    filtered_table_display = filtered_table_display.groupby(level=['year', 'month']).sum().sort_index(ascending=False)
elif time_period == 'week':
    filtered_table_display = filtered_table_display.groupby(level=['year', 'week']).sum().sort_index(ascending=False)
# Se for 'date', já está ordenado pelo sort_index anterior

# Formatar tabela detalhada
formatted_table = filtered_table_display.copy()
for col in formatted_table.columns:
    formatted_table[col] = formatted_table[col].apply(format_time)

# Mostrar a tabela detalhada
st.dataframe(formatted_table, use_container_width=True, hide_index=False)

# Workload weekly distribution por último
st.subheader('Workload weekly distribution')
st.dataframe(filtered_weekday_pivot, use_container_width=True, hide_index=False)
# legenda
st.markdown('''
**Mesures**
* **Média**: Principal métrica de comparação entre as semanas
* **Média ponderada**: Métrica de alálise de distribuição, quando mais perto de 4 mais bem equilibrada está a distribuição.
    * A média ponderada buscada é entre **3.5** e **4**, considerando o descanço aos fins de semana.
* **Min - Max**: Também undica a distribuição, quando menor melhor foi a distribuição.
''')

