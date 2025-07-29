# google-maps-prospeccao

#  Prospecção com Google Maps API

Script para buscar empresas por razão social usando a Google Places API. Exporta os dados para um Excel com nome, endereço, telefone e site da empresa.

##  Funcionalidades

- Busca por nome/razão social
- Suporte a filtros por cidade, estado e raio
- Exportação em Excel formatado
- Barra de progresso com `tqdm`
- Detalhamento com place_id

##  Tecnologias

- Python 3
- requests
- pandas
- tqdm
- Google Places API

##  Instalação

```bash
pip install -r requirements.txt
