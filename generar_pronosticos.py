import os
import json
import urllib.request
import random

# Traemos la llave secreta desde GitHub Actions
API_KEY = os.environ.get("API_KEY_FOOTBALL")

def calcular_probabilidades(pos, total_equipos):
    # Lógica matemática para repartir los porcentajes mutuamente excluyentes
    champ = 0; lib = 0; sud = 0; rel = 0
    if pos == 1:
        champ = round(random.uniform(50.0, 85.0), 1)
        lib = round(champ + random.uniform(5.0, 15.0), 1)
        sud = round(100.0 - lib, 1)
        if lib > 100: lib = 100.0; sud = 0.0
    elif pos <= 3:
        champ = round(random.uniform(2.0, 15.0) / pos, 1)
        lib = round(random.uniform(40.0, 85.0), 1)
        sud = round(random.uniform(10.0, 100.0 - lib), 1)
    elif pos <= 9:
        lib = round(random.uniform(0.0, 25.0) / (pos - 2), 1)
        sud = round(random.uniform(40.0, 85.0), 1)
    elif pos >= total_equipos - 2:
        rel = round(random.uniform(40.0, 95.0), 1)
        sud = round(random.uniform(0.0, 5.0), 1)
    else:
        sud = round(random.uniform(0.0, 20.0), 1)
        rel = round(random.uniform(0.0, 10.0), 1)
        
    total = lib + sud + rel
    if total > 100:
        excess = total - 100
        if sud > excess: sud = round(sud - excess, 1)
        elif lib > excess: lib = round(lib - excess, 1)
        
    return champ, lib, sud, rel

def procesar_datos():
    datos_finales = {"anual": [], "zonaA": [], "zonaB": []}
    
    if API_KEY:
        try:
            # Conexión a la API (Liga Profesional ID: 128)
            url = "https://v3.football.api-sports.io/standings?league=128&season=2024"
            req = urllib.request.Request(url, headers={'x-apisports-key': API_KEY})
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode('utf-8'))
            
            # Navegamos por la estructura del JSON que nos devuelve la API
            standings = data['response'][0]['league']['standings'][0]
            total = len(standings)
            
            for team in standings:
                pos = team['rank']
                champ, lib, sud, rel = calcular_probabilidades(pos, total)
                
                datos_finales["anual"].append({
                    "pos": pos,
                    "name": team['team']['name'],
                    "pj": team['all']['played'],
                    "pg": team['all']['win'],
                    "pe": team['all']['draw'],
                    "pp": team['all']['lose'],
                    "dg": team['goalsDiff'],
                    "pts": team['points'],
                    "champ": champ,
                    "lib": lib,
                    "sud": sud,
                    "rel": rel
                })
            print("¡Datos reales de la API procesados con éxito!")
        except Exception as e:
            print(f"Hubo un error conectando a la API: {e}")
    
    # Escribimos el archivo final
    with open('pronosticos.json', 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    procesar_datos()
