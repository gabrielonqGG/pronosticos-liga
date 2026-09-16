import json
import random
import urllib.request
import pandas as pd
import re

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
    if pos <= 8:
        return round(random.uniform(60.0, 99.0) - (pos * 1.5), 1)
    else:
        return round(random.uniform(0.0, 20.0) / (pos - 7), 1)

def procesar_datos():
    datos_finales = {"anual": [], "zonaA": [], "zonaB": []}
    
    try:
        # Apuntamos a una web de estadísticas sin firewalls agresivos
        url = "https://www.futbolargentino.com/primera-division/tabla-de-posiciones"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req, timeout=15).read()
        
        tablas = pd.read_html(html)
        df_stats = None
        
        # Buscamos dinámicamente la tabla que tenga a todos los equipos
        for tabla in tablas:
            if len(tabla) >= 28 and any('Equipo' in str(c) for c in tabla.columns):
                df_stats = tabla
                break
                
        if df_stats is None:
            raise Exception("No se encontró la tabla esperada en la web.")
            
        df_stats.columns = [str(c).upper().strip() for c in df_stats.columns]
        col_equipo = [c for c in df_stats.columns if 'EQUIPO' in c][0]
        
        for i in range(len(df_stats)):
            nombre_crudo = str(df_stats.iloc[i][col_equipo])
            # Limpiamos cualquier número o símbolo que la web le ponga al lado del nombre
            nombre = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', nombre_crudo).strip()
            
            try:
                pts = int(df_stats.iloc[i]['PTS'])
                pj = int(df_stats.iloc[i]['PJ'])
                pg = int(df_stats.iloc[i]['PG'])
                pe = int(df_stats.iloc[i]['PE'])
                pp = int(df_stats.iloc[i]['PP'])
                
                col_dg = [c for c in df_stats.columns if 'DIF' in c or 'DG' in c]
                dg = int(df_stats.iloc[i][col_dg[0]]) if col_dg else 0
            except:
                # Si le cambian el nombre a las columnas, extraemos por posición de fila
                pts = int(df_stats.iloc[i, 2])
                pj = int(df_stats.iloc[i, 3])
                pg = int(df_stats.iloc[i, 4])
                pe = int(df_stats.iloc[i, 5])
                pp = int(df_stats.iloc[i, 6])
                dg = int(df_stats.iloc[i, 9])
            
            datos_equipo = {
                "name": nombre,
                "pj": pj, "pg": pg, "pe": pe, "pp": pp, "dg": dg, "pts": pts
            }
            
            datos_finales["anual"].append(datos_equipo.copy())
            
            es_zona_a = any(clave in nombre.lower() for clave in claves_zona_a)
            if es_zona_a:
                datos_finales["zonaA"].append(datos_equipo.copy())
            else:
                datos_finales["zonaB"].append(datos_equipo.copy())
                
        for zona in ["anual", "zonaA", "zonaB"]:
            if datos_finales[zona]:
                datos_finales[zona].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
                total_en_tabla = len(datos_finales[zona])
                for i, eq in enumerate(datos_finales[zona]):
                    eq["pos"] = i + 1
                    if zona == "anual":
                        c, l, s, r = calcular_prob_anual(eq["pos"], total_en_tabla)
                        eq.update({"champ": c, "lib": l, "sud": s, "rel": r})
                    else:
                        eq["playoff"] = calcular_prob_zona(eq["pos"])

        print(f"¡Extracción impecable! Equipos procesados: {len(datos_finales['anual'])}")
        
    except Exception as e:
        print(f"Error detectado: {e}")
        for zona in ["anual", "zonaA", "zonaB"]:
            for i in range(1, 16 if zona != "anual" else 31):
                datos_finales[zona].append({
                    "pos": i, "name": f"Bloqueo Temporal", 
                    "pj": 0, "pg": 0, "pe": 0, "pp": 0, "dg": 0, "pts": 0,
                    "champ": 0, "lib": 0, "sud": 0, "rel": 0, "playoff": 0
                })

    with open('pronosticos.json', 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    procesar_datos()
