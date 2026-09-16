import json
import random
import urllib.request
import pandas as pd

claves_zona_a = [
    "argentinos", "tucum", "banfield", "barracas",
    "riestra", "gimnasia", "huracan", "independiente",
    "instituto", "river", "rosario", "talleres",
    "velez", "rivadavia", "belgrano"
]

def calcular_prob_anual(pos, total_equipos):
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

def calcular_prob_zona(pos):
    # Lógica para los 8 clasificados a Playoffs Interzonales
    if pos <= 8:
        return round(random.uniform(60.0, 99.0) - (pos * 1.5), 1)
    else:
        return round(random.uniform(0.0, 20.0) / (pos - 7), 1)

def procesar_scraping():
    datos_finales = {"anual": [], "zonaA": [], "zonaB": []}
    
    try:
        url = "https://www.espn.com.ar/futbol/posiciones/_/liga/arg.1"
        # Le ponemos un camuflaje para que ESPN no nos bloquee
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=15).read()
        
        tablas = pd.read_html(html)
        df_nombres = tablas[0]
        df_stats = tablas[1]
        
        total_equipos = len(df_nombres)
        
        for i in range(total_equipos):
            nombre_crudo = str(df_nombres.iloc[i, 0])
            nombre = ''.join([letra for letra in nombre_crudo if not letra.isdigit()]).strip()
            
            datos_equipo = {
                "name": nombre,
                "pj": int(df_stats.iloc[i]['J']),
                "pg": int(df_stats.iloc[i]['G']),
                "pe": int(df_stats.iloc[i]['E']),
                "pp": int(df_stats.iloc[i]['P']),
                "dg": int(df_stats.iloc[i]['DIF']),
                "pts": int(df_stats.iloc[i]['PTS'])
            }
            
            datos_finales["anual"].append(datos_equipo.copy())
            
            es_zona_a = any(clave in nombre.lower() for clave in claves_zona_a)
            if es_zona_a:
                datos_finales["zonaA"].append(datos_equipo.copy())
            else:
                datos_finales["zonaB"].append(datos_equipo.copy())
                
        # Procesar posiciones y probabilidades
        datos_finales["anual"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
        for i, eq in enumerate(datos_finales["anual"]):
            eq["pos"] = i + 1
            c, l, s, r = calcular_prob_anual(eq["pos"], total_equipos)
            eq.update({"champ": c, "lib": l, "sud": s, "rel": r})

        for zona in ["zonaA", "zonaB"]:
            if datos_finales[zona]:
                datos_finales[zona].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
                for i, eq in enumerate(datos_finales[zona]):
                    eq["pos"] = i + 1
                    eq["playoff"] = calcular_prob_zona(eq["pos"])

        print(f"¡Scraping de ESPN exitoso! Se procesaron {total_equipos} equipos.")
        
    except Exception as e:
        print(f"Error en el scraping: {e}")
        print("Activando salvavidas para no romper la web...")
        # Generamos datos de emergencia para que la web nunca quede en blanco
        for zona in ["anual", "zonaA", "zonaB"]:
            for i in range(1, 16 if zona != "anual" else 31):
                datos_finales[zona].append({
                    "pos": i, "name": f"Equipo {i} (Error ESPN)", 
                    "pj": 0, "pg": 0, "pe": 0, "pp": 0, "dg": 0, "pts": 0,
                    "champ": 0, "lib": 0, "sud": 0, "rel": 0, "playoff": 0
                })

    with open('pronosticos.json', 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    procesar_scraping()
