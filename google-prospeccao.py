import requests
import pandas as pd
import os
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')  
BASE_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'

def buscar_empresas_por_razao_social(razao_social, localizacao=None, raio=None, cidade=None, estado=None):
    """
    Busca empresas no Google Maps pela razão social.
    
    :param razao_social: Nome da empresa ou razão social.
    :param localizacao: Coordenadas (lat, lng) para busca localizada. Ex: "-23.5505,-46.6333".
    :param raio: Raio de busca em metros (opcional).
    :param cidade: Nome da cidade para busca (opcional).
    :param estado: Nome do estado para busca (opcional).
    :return: DataFrame com os resultados.
    """
    resultados_textsearch = buscar_textsearch(razao_social, localizacao, raio, cidade, estado)
    resultados_nearbysearch = buscar_nearbysearch(razao_social, localizacao, raio)
    
    # Combina os resultados das duas buscas
    resultados_combinados = pd.concat([resultados_textsearch, resultados_nearbysearch]).drop_duplicates().reset_index(drop=True)
    
    return resultados_combinados

def buscar_textsearch(razao_social, localizacao=None, raio=None, cidade=None, estado=None):
    """
    Realiza uma busca textsearch no Google Maps.
    
    :param razao_social: Nome da empresa ou razão social.
    :param localizacao: Coordenadas (lat, lng) para busca localizada.
    :param raio: Raio de busca em metros (opcional).
    :param cidade: Nome da cidade para busca (opcional).
    :param estado: Nome do estado para busca (opcional).
    :return: DataFrame com os resultados.
    """
    params = {
        'query': razao_social,
        'key': API_KEY
    }
    
    if localizacao:
        params['location'] = localizacao
    if raio:
        params['radius'] = raio
    if cidade:
        params['query'] += f" in {cidade}"
    if estado:
        params['query'] += f", {estado}"
    
    resultados = []
    next_page_token = None
    
    try:
        with tqdm(desc="Prospecção de empresas", unit="empresa", dynamic_ncols=True, bar_format="{desc}: {n_fmt}/∞ [{elapsed}]") as pbar:
            while True:
                if next_page_token:
                    params['pagetoken'] = next_page_token
                
                response = requests.get(BASE_URL, params=params)
                dados = response.json()
                
                if dados['status'] == 'OK':
                    for resultado in dados['results']:
                        nome = resultado.get('name', 'N/A')
                        endereco = resultado.get('formatted_address', 'N/A')
                        place_id = resultado.get('place_id', 'N/A')
                        lat = resultado.get('geometry', {}).get('location', {}).get('lat', 'N/A')
                        lng = resultado.get('geometry', {}).get('location', {}).get('lng', 'N/A')
                        
                        detalhes = obter_detalhes_por_place_id(place_id)
                        if detalhes:
                            telefone = detalhes.get('formatted_phone_number', 'N/A')
                            website = detalhes.get('website', 'N/A')
                            razao_social_detalhada = detalhes.get('name', 'N/A')
                        else:
                            telefone = website = razao_social_detalhada = 'N/A'
                        
                        resultados.append({
                            'Nome': nome,
                            'Endereço': endereco,
                            'Telefone': telefone,
                            'Website': website
                        })
                        pbar.update(1)
                    
                    next_page_token = dados.get('next_page_token')
                    if not next_page_token:
                        break
                else:
                    print(f"Erro na busca: {dados['status']}")
                    break
    
    except Exception as e:
        print(f"Erro ao processar a requisição: {e}")
    
    return pd.DataFrame(resultados)

def buscar_nearbysearch(razao_social, localizacao, raio):
    """
    Realiza uma busca nearbysearch no Google Maps.
    
    :param razao_social: Nome da empresa ou razão social.
    :param localizacao: Coordenadas (lat, lng) para busca localizada.
    :param raio: Raio de busca em metros.
    :return: DataFrame com os resultados.
    """
    nearby_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {
        'keyword': razao_social,
        'location': localizacao,
        'radius': raio,
        'key': API_KEY
    }
    
    resultados = []
    next_page_token = None
    
    try:
        with tqdm(desc="Prospecção de empresas", unit="empresa", dynamic_ncols=True, bar_format="{desc}: {n_fmt}/∞ [{elapsed}]") as pbar:
            while True:
                if next_page_token:
                    params['pagetoken'] = next_page_token
                
                response = requests.get(nearby_url, params=params)
                dados = response.json()
                
                if dados['status'] == 'OK':
                    for resultado in dados['results']:
                        nome = resultado.get('name', 'N/A')
                        endereco = resultado.get('vicinity', 'N/A')
                        place_id = resultado.get('place_id', 'N/A')
                        lat = resultado.get('geometry', {}).get('location', {}).get('lat', 'N/A')
                        lng = resultado.get('geometry', {}).get('location', {}).get('lng', 'N/A')
                        
                        detalhes = obter_detalhes_por_place_id(place_id)
                        if detalhes:
                            telefone = detalhes.get('formatted_phone_number', 'N/A')
                            website = detalhes.get('website', 'N/A')
                            razao_social_detalhada = detalhes.get('name', 'N/A')
                        else:
                            telefone = website = razao_social_detalhada = 'N/A'
                        
                        resultados.append({
                            'Nome': nome,
                            'Endereço': endereco,
                            'Telefone': telefone,
                            'Website': website
                        })
                        pbar.update(1)
                    
                    next_page_token = dados.get('next_page_token')
                    if not next_page_token:
                        break
                else:
                    print(f"Erro na busca: {dados['status']}")
                    break
    
    except Exception as e:
        print(f"Erro ao processar a requisição: {e}")
    
    return pd.DataFrame(resultados)

def obter_detalhes_por_place_id(place_id):
    """
    Obtém detalhes adicionais de um lugar usando o Place ID.
    
    :param place_id: ID do lugar no Google Places.
    :return: Dicionário com detalhes.
    """
    detalhes_url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': place_id,
        'key': API_KEY,
        'fields': 'name,formatted_phone_number,website'
    }
    
    try:
        response = requests.get(detalhes_url, params=params)
        dados = response.json()
        if dados['status'] == 'OK':
            return dados['result']
        else:
            print(f"Erro ao buscar detalhes: {dados['status']} - Place ID: {place_id}")
            if 'error_message' in dados:
                print(f"Mensagem de erro: {dados['error_message']}")
            return {}
    except Exception as e:
        print(f"Erro ao processar detalhes: {e} - Place ID: {place_id}")
        return {}

def obter_coordenadas(cidade, estado):
    """
    Obtém as coordenadas (latitude e longitude) de uma cidade e estado.
    
    :param cidade: Nome da cidade.
    :param estado: Nome do estado.
    :return: String com as coordenadas no formato "lat,lng".
    """
    geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': f"{cidade}, {estado}",
        'key': API_KEY
    }
    
    try:
        response = requests.get(geocode_url, params=params)
        dados = response.json()
        if dados['status'] == 'OK':
            location = dados['results'][0]['geometry']['location']
            return f"{location['lat']},{location['lng']}"
        else:
            print(f"Erro ao obter coordenadas: {dados['status']}")
            return None
    except Exception as e:
        print(f"Erro ao processar coordenadas: {e}")
        return None

def converter_horarios(horarios):
    """
    Converte o formato de horários de atendimento para o formato desejado.
    
    :param horarios: Lista de horários no formato original.
    :return: String com os horários no formato desejado.
    """
    dias_semana = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']
    dias_ingles = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    horarios_convertidos = {}
    
    for horario in horarios:
        dia, _ = horario.split(': ', 1)
        dia_abreviado = dias_semana[dias_ingles.index(dia)]
        
        if dia_abreviado not in horarios_convertidos:
            horarios_convertidos[dia_abreviado] = []
        horarios_convertidos[dia_abreviado].append(dia_abreviado)
    
    horarios_formatados = []
    for dias in horarios_convertidos.values():
        if len(dias) == 7:
            dias_formatados = 'SEG-DOM'
        elif len(dias) == 6 and 'DOM' not in dias:
            dias_formatados = 'SEG-SAB'
        elif len(dias) == 5 and 'SAB' not in dias and 'DOM' not in dias:
            dias_formatados = 'SEG-SEX'
        else:
            dias_formatados = f"{dias[0]}-{dias[-1]}" if len(dias) > 1 else dias[0]
        horarios_formatados.append(dias_formatados)
    
    return ', '.join(horarios_formatados)

def salvar_resultados(resultados, nome_arquivo, cidade):
    """
    Salva os resultados em um arquivo com o formato especificado, sem filtrar pela cidade.
    
    :param resultados: DataFrame com os resultados.
    :param nome_arquivo: Nome do arquivo para salvar os resultados.
    :param cidade: Nome da cidade (não utilizado mais para filtrar).
    """
   
    resultados_filtrados = resultados  

    script_path = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(script_path, nome_arquivo)
    
    resultados_formatados = resultados_filtrados.rename(columns={
        'Endereço': 'REGIAO',
        'Nome': 'NOME DA EMPRESA',
        'Telefone': 'TELEFONE',
        'Website': 'SITE'
    })
    resultados_formatados['NOME DO CONTATO'] = '' 
    resultados_formatados = resultados_formatados[['REGIAO', 'NOME DA EMPRESA', 'NOME DO CONTATO', 'TELEFONE', 'SITE']]
    resultados_formatados.to_excel(caminho_arquivo, index=False)

# Exemplo de uso
if __name__ == "__main__":
    razao_social = "RAZAO SOCIAL"
    cidade = input("Digite o nome da cidade: ")
    estado = input("Digite o nome do estado: ")
    localizacao = obter_coordenadas(cidade, estado)
    raio = 23000  
    
    if localizacao:
        resultados = buscar_empresas_por_razao_social(razao_social, localizacao, raio, cidade, estado)
        
        if not resultados.empty:
            print(resultados)
            salvar_resultados(resultados, 'resultados_busca_formatado.xlsx', cidade)  # Salva no formato especificado
        else:
            print("Nenhum resultado encontrado.")
    else:
        print("Não foi possível obter as coordenadas para a cidade e estado fornecidos.")
