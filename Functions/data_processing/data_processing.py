# Expandir colunas de dicionários aninhados
import pandas as pd
def expand_column_nested_dicts(df, column):
    """
    Colunas que representam multiplas colunas
    {campo: {campo: valor, campo: valor}}
    Entra com o dataframe e a determinada coluna
    Retorna o dataframe com a coluna expandida
    """
    df_2 = pd.json_normalize(df[column])
    df = df.reset_index(drop=True)
    df = pd.concat([df.drop(column, axis=1), df_2], axis=1)
    return df

# Expandir colunas de lista de dicionários aninhados
import pandas as pd
def expand_column_list_of_nested_dicts(df, column):
    """
    Colunas que representam multiplas colunas e até registros
    [{campo: {campo: valor, campo: valor}}, {campo: {campo: valor, campo: valor}}]
    Entra com o dataframe e a determinada coluna
    Retorna o dataframe com a coluna expandida
    """
    df = df.explode(column) # Expandindo as listas (abrindo os registros)
    df_2 = pd.json_normalize(df[column]) # Expandindo os dicionários (abrindos os dicionários) em um novo dataframe
    df = df.reset_index(drop=True) # Resetanto o indíce
    df = pd.concat([df.drop(column, axis=1), df_2], axis=1) # Juntando os dois dataframes
    return df

# formatar duração de tempo em valor decimal
import pandas as pd
def format_time(td):
    if isinstance(td, pd.Timedelta):
        total_hours = td.total_seconds() / 3600
    else:
        total_hours = td
    hours = int(total_hours)
    minutes = int((total_hours - hours) * 60)
    return f"{hours}h {minutes}min"

# remover acentos
import unicodedata
def remover_acentos(texto):
    if isinstance(texto, str):
        return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto
