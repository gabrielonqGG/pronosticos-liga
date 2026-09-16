import json
import random
import urllib.request
import pandas as pd

claves_zona_a = [
    "argentinos", "tucum", "banfield", "barracas",
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

def procesar_scraping():
    datos_finales = {"anual": [], "zonaA": [], "zonaB": []}
    
    try:
        url = "https://www.espn.com.ar/futbol/posiciones/_/liga/arg.1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read()
        
        # pandas extrae mágicamente las tablas HTML
        tablas = pd.read_html(html)
        
        # ESPN separa los nombres (tabla 0) de las estadísticas (tabla 1)
        df_nombres = tablas[0]
        df_stats = tablas[1]
        
        total_equipos = len(df_nombres)
        
        for i in range(total_equipos):
            pos = i + 1
            # Limpiamos el nombre para quitar el número de ranking
            nombre_crudo = str(df_nombres.iloc[i, 0])
            nombre = ''.join([letra for letra in nombre_crudo if not letra.isdigit()]).strip()
            
            champ, lib, sud, rel = calcular_probabilidades(pos, total_equipos)
            
            datos_equipo = {
                "pos": pos,
                "name": nombre,
                "pj": int(df_stats.iloc[i]['J']),
                "pg": int(df_stats.iloc[i]['G']),
                "pe": int(df_stats.iloc[i]['E']),
                "pp": int(df_stats.iloc[i]['P']),
                "dg": int(df_stats.iloc[i]['DIF']),
                "pts": int(df_stats.iloc[i]['PTS']),
                "champ": champ,
                "lib": lib,
                "sud": sud,
                "rel": rel
            }
            
            datos_finales["anual"].append(datos_equipo)
            
            # Filtramos Zonas
            es_zona_a = any(clave in nombre.lower() for clave in claves_zona_a)
            if es_zona_a:
                datos_finales["zonaA"].append(datos_equipo)
            else:
                datos_finales["zonaB"].append(datos_equipo)
                
        # Recalculamos las posiciones de las Zonas
        if datos_finales["zonaA"]:
            datos_finales["zonaA"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
            for i, eq in enumerate(datos_finales["zonaA"]): eq["pos"] = i + 1
        if datos_finales["zonaB"]:
            datos_finales["zonaB"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
            for i, eq in enumerate(datos_finales["zonaB"]): eq["pos"] = i + 1

        print("¡Scraping de ESPN exitoso y datos procesados!")
        
    except Exception as e:
        print(f"Error en el scraping: {e}")

    with open('pronosticos.json', 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    procesar_scraping()
