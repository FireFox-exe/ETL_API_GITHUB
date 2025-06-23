import os
import requests
import pandas as pd
import time
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env (como o token do GitHub)
load_dotenv()

class RepositoryData:
    def __init__(self, owner):
        # Define o nome do dono do repositório (pode ser uma empresa ou pessoa)
        self.owner = owner
        self.api_base_url = 'https://api.github.com'
        
        # Busca o token no arquivo .env para conseguir acessar a API
        self.access_token = os.getenv('TOKEN_GITHUB')
        if not self.access_token:
            raise ValueError("TOKEN_GITHUB não encontrado no .env. Configure antes de rodar.")

        # Define os cabeçalhos usados nas requisições para o GitHub
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }

        # Cria uma variável para armazenar os dados dos repositórios (cache simples)
        self._all_repos = None

        print(f"Coletando dados do GitHub para: {self.owner}")

    def list_all_repositories(self):
        # Se os dados já foram buscados antes, usa o cache
        if self._all_repos:
            print("Usando cache dos repositórios.")
            return self._all_repos

        repos = []
        page = 1  # Começa na página 1 (a API divide os resultados em páginas)

        while True:
            # Monta a URL com os parâmetros de paginação
            url = f'{self.api_base_url}/users/{self.owner}/repos'
            params = {'page': page, 'per_page': 100}
            print(f"Baixando página {page}...")

            try:
                # Faz a requisição e transforma a resposta em JSON
                res = requests.get(url, headers=self.headers, params=params)
                res.raise_for_status()
                data = res.json()

                # Se não tiver mais dados, encerra o loop
                if not data:
                    break

                # Adiciona os repositórios da página na lista principal
                repos.extend(data)
                page += 1
                time.sleep(0.5)  # Pausa para não sobrecarregar a API
            except Exception as e:
                print(f"Erro ao buscar página {page}: {e}")
                break

        # Salva no cache e retorna a lista final
        self._all_repos = repos
        return repos

    def extract_repo_names(self, repos):
        # Cria uma lista com os nomes dos repositórios
        names = []
        for repo in repos:
            name = repo.get('name')  # Usa .get() para evitar erro caso falte a chave
            if name:
                names.append(name)
            else:
                print("Aviso: repositório sem nome encontrado e ignorado.")
        return names

    def extract_languages(self, repos):
        # Cria uma lista com as linguagens principais de cada repositório
        langs = []
        for repo in repos:
            lang = repo.get('language')
            if lang is None:
                print(f"Aviso: repositório '{repo.get('name', 'N/A')}' sem linguagem principal.")
            langs.append(lang)
        return langs

    def create_languages_df(self):
        # Junta tudo: busca repositórios, extrai dados e transforma em DataFrame
        repos = self.list_all_repositories()
        if not repos:
            print("Nenhum repositório encontrado.")
            return pd.DataFrame(columns=['repository_name', 'language'])

        names = self.extract_repo_names(repos)
        langs = self.extract_languages(repos)

        # Cria um DataFrame com os nomes e linguagens
        df = pd.DataFrame({'repository_name': names, 'language': langs})
        print(f"DataFrame criado com {len(df)} registros.")
        return df
