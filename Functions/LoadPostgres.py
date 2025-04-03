from sqlalchemy import create_engine, text

def Iterative_Load_Postgres(usuario, senha, host, porta, nome_banco, ListaDFs):
    engine = create_engine(f'postgresql://{usuario}:{senha}@{host}:{porta}/{nome_banco}', isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        for nome_tabela in ListaDFs.keys():
            conn.execute(text(f"TRUNCATE TABLE {nome_tabela} CASCADE;"))
            print(f"Tabela '{nome_tabela}' limpa antes da nova inserção.")

    for nome_tabela, df in ListaDFs.items():
        df.to_sql(nome_tabela, con=engine, if_exists='append', index=False)
        print(f"Novos dados de '{nome_tabela}' salvo com sucesso")