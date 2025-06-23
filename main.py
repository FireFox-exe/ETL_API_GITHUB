import os
import time
from etl.extractor import RepositoryData  # Importa o extrator de dados do GitHub
from upload.loader import RepositoryUploader  # Importa o uploader para o GitHub
from dotenv import load_dotenv

load_dotenv()  # Ativa as variáveis de ambiente


GITHUB_USER = 'FireFox-exe' 
REPO_NAME = 'company-repositories-languages'
USERS = ['amzn', 'netflix', 'spotify']  # Empresas para extrair dados

print("\n INICIANDO PIPELINE AUTOMATIZADO DO GITHUB ")

# Cria a pasta 'data' se ainda não existir
if not os.path.exists('data'):
    os.makedirs('data')
    print("Criada pasta 'data' para salvar arquivos.")

# Tenta preparar o uploader e criar o repositório
try:
    uploader = RepositoryUploader(GITHUB_USER)
    uploader.create_repository(REPO_NAME)
except Exception as e:
    print(f"Aviso: não consegui preparar o uploader/repositório: {e}")
    uploader = None  # Continua sem uploader

print("Repositório pronto.\n")

# Para cada empresa, executa extração e upload
for user in USERS:
    print(f"Processando dados para: {user}")

    # Tenta extrair dados do GitHub
    try:
        extractor = RepositoryData(user)
        df = extractor.create_languages_df()
    except Exception as e:
        print(f"Erro ao extrair dados de '{user}': {e}")
        continue  # Se der erro, vai para o próximo user

    # Se não tiver dados, não faz upload
    if df.empty:
        print(f"Nenhum dado para '{user}', pulando upload.")
        continue

    # Salva os dados localmente em um CSV
    path = f"data/languages_{user}.csv"
    df.to_csv(path, index=False)
    print(f"Dados salvos em '{path}'.")

    # Se o uploader estiver pronto, tenta subir o arquivo
    if uploader:
        try:
            uploader.upload_file(REPO_NAME, os.path.basename(path), path)
        except Exception as e:
            print(f"Erro ao subir arquivo de '{user}': {e}")
    else:
        print("Uploader não disponível, arquivo não será enviado.")

print("\n PIPELINE FINALIZADO \n")
