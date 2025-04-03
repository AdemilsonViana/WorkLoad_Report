import requests
import pandas as pd

def API_Notion(dataset_id, token):
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