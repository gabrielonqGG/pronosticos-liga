import os
import json
import urllib.request
import random

API_KEY = os.environ.get("API_KEY_FOOTBALL")

# Usamos palabras clave en minúscula para que coincida sin importar cómo lo escriba la API
claves_zona_a = [
    "argentinos", "tucuman", "banfield", "barracas",
    "riestra", "gimnasia", "huracan", "independiente",
    "instituto", "river", "rosario", "talleres",
    "velez", "rivadavia"
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
    api_exitosa = False
    
    if API_KEY:
        try:
            url = "https://v3.football.api-sports.io/standings?league=128&season=2026"
            req = urllib.request.Request(url, headers={'x-apisports-key': API_KEY})
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode('utf-8'))
            
            # Verificamos si la API devolvió errores (ej: límite de consultas)
            if 'errors' in data and data['errors']:
                raise Exception(f"La API devolvió un error: {data['errors']}")
            
            if not data.get('response'):
                raise Exception("La API no devolvió datos para la Liga 128 en el año 2026.")
            
            listas_tablas = data['response'][0]['league']['standings']
            
            for tabla in listas_tablas:
                total_equipos_tabla = len(tabla)
                for team in tabla:
                    nombre = team['team']['name']
                    pos = team['rank']
                    champ, lib, sud, rel = calcular_probabilidades(pos, total_equipos_tabla)
                    
                    datos_equipo = {
                        "pos": pos,
                        "name": nombre,
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
                    
                    datos_finales["anual"].append(datos_equipo)
                    
                    # Asignación segura a Zonas
                    es_zona_a = any(clave in nombre.lower() for clave in claves_zona_a)
                    if es_zona_a:
                        datos_finales["zonaA"].append(datos_equipo)
                    else:
                        datos_finales["zonaB"].append(datos_equipo)
            
            # Recalcular posiciones
            if datos_finales["zonaA"]:
                datos_finales["zonaA"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
                for i, eq in enumerate(datos_finales["zonaA"]): eq["pos"] = i + 1
            if datos_finales["zonaB"]:
                datos_finales["zonaB"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
                for i, eq in enumerate(datos_finales["zonaB"]): eq["pos"] = i + 1
                
            api_exitosa = True
            print("¡Datos reales procesados y divididos con éxito!")
            
        except Exception as e:
            print(f"\n--- ERROR CRÍTICO DETECTADO ---")
            print(f"Detalle: {e}")
            print(f"-------------------------------\n")
    
    # Si la API falla, generamos datos de simulación temporales para que la web no se rompa
    if not api_exitosa:
        print("Activando salvavidas: Cargando datos de simulación temporales.")
        equipos_simulados = ["Velez", "River", "Boca", "Talleres", "Racing", "Huracan"]
        for i, eq in enumerate(equipos_simulados):
            c, l, s, r = calcular_probabilidades(i+1, 6)
            fake_data = {"pos": i+1, "name": eq + " (Datos Simulados por Error de API)", "pj": 10, "pg": 5, "pe": 3, "pp": 2, "dg": 5, "pts": 20 - i, "champ": c, "lib": l, "sud": s, "rel": r}
            datos_finales["anual"].append(fake_data)
            datos_finales["zonaA"].append(fake_data)
            datos_finales["zonaB"].append(fake_data)

    with open('pronosticos.json', 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    procesar_datos()
