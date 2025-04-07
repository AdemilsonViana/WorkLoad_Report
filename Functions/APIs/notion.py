import requests
import pandas as pd

def API_Notion(dataset_id, token):
    '''
    Função para extrair dados do Notion.
    Recebe o ID do dataset e o token de autenticação.
    '''
    NOTION_VERSION = "2022-06-28"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    
    url = f"https://api.notion.com/v1/databases/{dataset_id}/query"
    all_results = []
    payload = {}

    while True:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        # Acumula os registros da página atual
        all_results.extend(data.get("results", []))
        
        # Verifica se há mais registros (paginação)
        if data.get("has_more", False):
            payload = {"start_cursor": data.get("next_cursor")}
        else:
            break

    return pd.DataFrame(all_results)

def api_notion_iterativa(urls):
    '''
    Função para extrair dados do Notion de forma iterativa.
    Recebe um dicionário de URLs e retorna um dicionário de DataFrames.
    o dicionário de URLs deve conter o ID do dataset e o token de autenticação.
    Exemplo:
    urls = {
        'studying_calendar': {
            'dataset_id': st.secrets["notion"]["studying_calendar_dataset_id"],
            'token': st.secrets["notion"]["studying_calendar_token"]
    '''
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