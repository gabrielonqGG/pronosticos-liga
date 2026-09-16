import os
import json
import urllib.request
import random

API_KEY = os.environ.get("API_KEY_FOOTBALL")

# Equipos de la Zona A del Clausura
equipos_zona_a = [
    "Argentinos Jrs", "Atletico Tucuman", "Banfield", "Barracas Central",
    "Deportivo Riestra", "Gimnasia L.P.", "Huracan", "Independiente",
    "Instituto Cordoba", "River Plate", "Rosario Central", "Talleres Cordoba",
    "Velez Sarsfield", "Independ. Rivadavia"
]

def calcular_probabilidades(pos, total_equipos):
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
            url = "https://v3.football.api-sports.io/standings?league=128&season=2026"
            req = urllib.request.Request(url, headers={'x-apisports-key': API_KEY})
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode('utf-8'))
            
            listas_tablas = data['response'][0]['league']['standings']
            
            # Recorremos la(s) tabla(s) que mande la API
            for tabla in listas_tablas:
                total_equipos_tabla = len(tabla)
                
                for team in tabla:
                    nombre_equipo = team['team']['name']
                    pos = team['rank']
                    champ, lib, sud, rel = calcular_probabilidades(pos, total_equipos_tabla)
                    
                    datos_equipo = {
                        "pos": pos,
                        "name": nombre_equipo,
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
                    }
                    
                    # 1. Lo agregamos siempre a la Tabla Anual
                    datos_finales["anual"].append(datos_equipo)
                    
                    # 2. Lo filtramos a su Zona correspondiente manualmente
                    if nombre_equipo in equipos_zona_a:
                        datos_finales["zonaA"].append(datos_equipo)
                    else:
                        datos_finales["zonaB"].append(datos_equipo)
            
            # Recalculamos las posiciones de la Zona A
            datos_finales["zonaA"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
            for i, equipo in enumerate(datos_finales["zonaA"]):
                equipo["pos"] = i + 1
                
            # Recalculamos las posiciones de la Zona B
            datos_finales["zonaB"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
            for i, equipo in enumerate(datos_finales["zonaB"]):
                equipo["pos"] = i + 1

            print("¡Datos procesados y zonas divididas con éxito!")
            
        except Exception as e:
            print(f"Hubo un error conectando a la API: {e}")
    
    with open('pronosticos.json', 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    procesar_datos()
