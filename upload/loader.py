import os
import requests
import base64
from dotenv import load_dotenv

# Carrega as variáveis do .env (como o token do GitHub)
load_dotenv()

class RepositoryUploader:
    def __init__(self, username):
        self.username = username
        self.api_base_url = 'https://api.github.com'
        self.access_token = os.getenv('TOKEN_GITHUB')

        if not self.access_token:
            raise Exception("TOKEN_GITHUB não encontrado no .env.")

        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }

        print(f"Iniciando uploader para o usuário: {self.username}")

    def create_repository(self, repo_name):
        # Cria um repositório novo no GitHub. Se já existir, só avisa.
        print(f"-> Criando repositório: {repo_name}")
        url = f'{self.api_base_url}/user/repos'
        data = {
            'name': repo_name,
            'description': 'Criado automaticamente com Python',
            'private': False
        }
        
        #response
        res = requests.post(url, json=data, headers=self.headers) 

        if res.status_code == 201:
            print("Repositório criado com sucesso!")
            print(f"Link: {res.json().get('html_url')}")
        elif res.status_code == 422:
            print(f"O repositório '{repo_name}' já existe ou tem algum problema no nome.")
            print("Vamos continuar usando ele assim mesmo.")
        else:
            print(f"Não foi possível criar o repositório. Código de erro: {res.status_code}")
            print("Resposta da API:")
            print(res.text)


    def upload_file(self, repo_name, file_name, file_path):
        #Envia um arquivo para o repositório no GitHub.
        print(f"\n Enviando arquivo: {file_name}")

        if not os.path.exists(file_path):
            print("Arquivo não encontrado. Abortando.")
            return

        # Lê e codifica o conteúdo do arquivo
        with open(file_path, "rb") as f:
            content = f.read()
        encoded_content = base64.b64encode(content).decode("utf-8")

        url = f'{self.api_base_url}/repos/{self.username}/{repo_name}/contents/{file_name}'

        # Verifica se o arquivo já existe
        sha = None
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            sha = res.json().get('sha')
            print("Arquivo já existe. Será atualizado.")
        elif res.status_code == 404:
            print("Arquivo não existe. Será criado.")
        else:
            print("Não foi possível verificar o arquivo. Continuando assim mesmo...")

        data = {
            'message': f'Upload automático de {file_name}',
            'content': encoded_content
        }
        if sha:
            data['sha'] = sha

        res = requests.put(url, json=data, headers=self.headers)

        if res.status_code in [200, 201]:
            print(f"Arquivo enviado com sucesso!")
        else:
            print(f"Erro ao enviar arquivo. Código: {res.status_code}")
            print(res.text)
