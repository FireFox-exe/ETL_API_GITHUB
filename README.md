# GitHub Language Collector
---
## main.py - Setup inicial

```python

import os
import time
from etl.extractor import RepositoryData
from uploader.uploader import RepositoryUploader
from dotenv import load_dotenv

load_dotenv()

GITHUB_USER = 'FireFox-exe'
REPO_NAME = 'company-repositories-languages'
USERS = ['amzn', 'netflix', 'spotify']

if not os.path.exists('data'):
    os.makedirs('data')
    print("Pasta 'data' criada para salvar arquivos.")

#main.py - Preparar uploader e criar repositório no GitHub
try:
    uploader = RepositoryUploader(GITHUB_USER)
    uploader.create_repository(REPO_NAME)
except Exception as e:
    print(f"Não consegui preparar o uploader: {e}")
    uploader = None
```
Explicação:
Inicializamos o uploader, que será responsável por enviar os arquivos para o GitHub. Também tentamos criar o repositório onde os arquivos serão guardados. Se ocorrer erro, seguimos sem uploader, mas avisamos.


## main.py - Para cada usuário, extrair, salvar e enviar dados
```python

for user in USERS:
    print(f"Processando: {user}")

    try:
        extractor = RepositoryData(user)
        df = extractor.create_languages_df()
    except Exception as e:
        print(f"Erro extraindo dados de {user}: {e}")
        continue

    if df.empty:
        print(f"Nenhum dado para {user}. Pulando upload.")
        continue

    path = f"data/languages_{user}.csv"
    df.to_csv(path, index=False)
    print(f"Dados salvos em {path}.")

    if uploader:
        try:
            uploader.upload_file(REPO_NAME, os.path.basename(path), path)
        except Exception as e:
            print(f"Erro ao enviar arquivo de {user}: {e}")
    else:
        print("Uploader não disponível, arquivo não enviado.")
```
Explicação:
Para cada usuário da lista, criamos um extrator e coletamos os dados em um DataFrame. Se houver dados, salvamos em CSV local. Caso o uploader esteja disponível, enviamos o arquivo para o GitHub. Caso contrário, avisamos que o upload não foi realizado.

## etl/extractor.py - Inicializando classe para pegar dados do GitHub
```python
class RepositoryData:
    def __init__(self, owner):
        self.owner = owner
        self.api_base_url = 'https://api.github.com'
        self.access_token = os.getenv('TOKEN_GITHUB')
        if not self.access_token:
            raise ValueError("TOKEN_GITHUB não configurado.")
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        self._all_repos = None
```
Explicação:
Preparamos a classe com o nome do usuário ou organização. Pegamos o token do .env e configuramos os cabeçalhos para usar a API do GitHub.

## etl/extractor.py - Pegando todos os repositórios (com paginação)
```python
def list_all_repositories(self):
    if self._all_repos:
        return self._all_repos

    repos = []
    page = 1
    while True:
        url = f'{self.api_base_url}/users/{self.owner}/repos'
        res = requests.get(url, headers=self.headers, params={'page': page, 'per_page': 100})
        res.raise_for_status()
        data = res.json()
        if not data:
            break
        repos.extend(data)
        page += 1
        time.sleep(0.5)

    self._all_repos = repos
    return repos
```
Explicação:
Coletamos todos os repositórios do usuário página por página (até 100 por página). Quando não há mais dados, paramos. Guardamos os dados em cache para não buscar novamente.

##etl/extractor.py - Criando DataFrame só com nome do repo e linguagem
```python
def create_languages_df(self):
    repos = self.list_all_repositories()
    names = [repo.get('name') for repo in repos if repo.get('name')]
    langs = [repo.get('language') for repo in repos]
    return pd.DataFrame({'repository_name': names, 'language': langs})
Explicação:
Transformamos a lista de repositórios em um DataFrame contendo apenas o nome do repositório e a linguagem principal. Filtramos nomes que possam estar ausentes.

#uploader/uploader.py - Preparando uploader com autenticação
class RepositoryUploader:
    def __init__(self, username):
        self.username = username
        self.api_base_url = 'https://api.github.com'
        self.access_token = os.getenv('TOKEN_GITHUB')
        if not self.access_token:
            raise ValueError("TOKEN_GITHUB não configurado.")
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
```
Explicação:
Configuramos o uploader com o usuário, token e cabeçalhos necessários para chamar a API do GitHub.

## uploader/uploader.py - Criando o repositório no GitHub
```python
def create_repository(self, repo_name):
    url = f'{self.api_base_url}/user/repos'
    data = {'name': repo_name, 'description': 'Repositório com dados de linguagens.', 'private': False}
    res = requests.post(url, json=data, headers=self.headers)

    if res.status_code == 201:
        print(f"Repositório criado: {res.json().get('html_url')}")
    elif res.status_code == 422 and "name already exists" in res.text:
        print(f"Repositório '{repo_name}' já existe.")
    else:
        print(f"Erro ao criar repositório: {res.status_code}")
        print(res.text)
```
Explicação:
Tenta criar o repositório. Se ele já existe, apenas avisa. Se ocorrer outro erro, mostra o código e a resposta da API.

## uploader/uploader.py - Enviando ou atualizando arquivo no repositório
```python
def upload_file(self, repo_name, file_name, file_path):
    if not os.path.exists(file_path):
        print(f"Arquivo '{file_path}' não encontrado.")
        return False

    with open(file_path, 'rb') as f:
        content = f.read()
    encoded = base64.b64encode(content).decode('utf-8')

    url = f'{self.api_base_url}/repos/{self.username}/{repo_name}/contents/{file_name}'

    sha = None
    res = requests.get(url, headers=self.headers)
    if res.status_code == 200:
        sha = res.json().get('sha')

    data = {'message': f'Upload: {file_name}', 'content': encoded}
    if sha:
        data['sha'] = sha

    res = requests.put(url, json=data, headers=self.headers)

    if res.status_code in [200, 201]:
        print(f"Arquivo '{file_name}' enviado com sucesso.")
        return True
    else:
        print(f"Erro ao enviar arquivo: {res.status_code}")
        print(res.text)
        return False
```
Explicação:
Lê o arquivo local, converte em Base64 (exigido pelo GitHub), verifica se o arquivo já existe para atualizar usando o SHA. Faz o upload e avisa se foi sucesso ou erro.
