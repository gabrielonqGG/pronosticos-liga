import json
import urllib.request
import pandas as pd
import re
import io
import math
from datetime import datetime, timezone, timedelta

# =================================================================
# 1. BASE DE DATOS ESTÁTICA DEL APERTURA (16 Fechas)
# =================================================================
apertura_stats = {
    # --- ZONA A ---
    "Estudiantes de La Plata":  {"pj": 16, "pg": 9, "pe": 4, "pp": 3, "dg": 12, "pts": 31},
    "Boca Juniors":             {"pj": 16, "pg": 8, "pe": 6, "pp": 2, "dg": 13, "pts": 30},
    "Vélez Sarsfield":          {"pj": 16, "pg": 7, "pe": 7, "pp": 2, "dg": 6, "pts": 28},
    "Talleres de Córdoba":      {"pj": 16, "pg": 7, "pe": 5, "pp": 4, "dg": 4, "pts": 26},
    "Independiente":            {"pj": 16, "pg": 6, "pe": 6, "pp": 4, "dg": 4, "pts": 24},
    "Lanús":                    {"pj": 16, "pg": 6, "pe": 6, "pp": 4, "dg": 3, "pts": 24},
    "San Lorenzo":              {"pj": 16, "pg": 5, "pe": 7, "pp": 4, "dg": 0, "pts": 22},
    "Unión de Santa Fe":        {"pj": 16, "pg": 5, "pe": 6, "pp": 5, "dg": 4, "pts": 21},
    "Instituto":                {"pj": 16, "pg": 6, "pe": 3, "pp": 7, "dg": 0, "pts": 21},
    "Defensa y Justicia":       {"pj": 16, "pg": 4, "pe": 7, "pp": 5, "dg": -3, "pts": 19},
    "Gimnasia Mendoza":         {"pj": 16, "pg": 5, "pe": 4, "pp": 7, "dg": -8, "pts": 19},
    "Platense":                 {"pj": 16, "pg": 3, "pe": 7, "pp": 6, "dg": -5, "pts": 16},
    "Central Córdoba SE":       {"pj": 16, "pg": 4, "pe": 4, "pp": 8, "dg": -10, "pts": 16},
    "Newells Old Boys":         {"pj": 16, "pg": 3, "pe": 6, "pp": 7, "dg": -12, "pts": 15},
    "Deportivo Riestra":        {"pj": 16, "pg": 1, "pe": 8, "pp": 7, "dg": -7, "pts": 11},

    # --- ZONA B ---
    "Independiente Rivadavia":  {"pj": 16, "pg": 10, "pe": 4, "pp": 2, "dg": 14, "pts": 34},
    "River Plate":              {"pj": 16, "pg": 9, "pe": 2, "pp": 5, "dg": 10, "pts": 29},
    "Argentinos Juniors":       {"pj": 16, "pg": 8, "pe": 5, "pp": 3, "dg": 4, "pts": 29},
    "Rosario Central":          {"pj": 16, "pg": 8, "pe": 4, "pp": 4, "dg": 4, "pts": 28},
    "Belgrano":                 {"pj": 16, "pg": 7, "pe": 5, "pp": 4, "dg": 4, "pts": 26},
    "Gimnasia La Plata":        {"pj": 16, "pg": 8, "pe": 2, "pp": 6, "dg": 0, "pts": 26},
    "Huracán":                  {"pj": 16, "pg": 5, "pe": 7, "pp": 4, "dg": 4, "pts": 22},
    "Racing Club":              {"pj": 16, "pg": 5, "pe": 6, "pp": 5, "dg": 2, "pts": 21},
    "Barracas Central":         {"pj": 16, "pg": 5, "pe": 6, "pp": 5, "dg": 0, "pts": 21},
    "Tigre":                    {"pj": 16, "pg": 4, "pe": 8, "pp": 4, "dg": 3, "pts": 20},
    "Sarmiento":                {"pj": 16, "pg": 6, "pe": 1, "pp": 9, "dg": -7, "pts": 19},
    "Banfield":                 {"pj": 16, "pg": 5, "pe": 3, "pp": 8, "dg": -2, "pts": 18},
    "Atlético Tucumán":         {"pj": 16, "pg": 3, "pe": 5, "pp": 8, "dg": -5, "pts": 14},
    "Aldosivi":                 {"pj": 16, "pg": 0, "pe": 8, "pp": 8, "dg": -13, "pts": 8},
    "Estudiantes Río Cuarto":   {"pj": 16, "pg": 1, "pe": 2, "pp": 13, "dg": -19, "pts": 5}
}

# Limpiador estricto para que los nombres de la web siempre crucen con el diccionario
def limpiar_nombre(crudo):
    c = crudo.lower().replace(" ", "").replace("'", "").replace(".", "").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
    if 'newell' in c: return "Newells Old Boys"
    if 'rivadavia' in c: return "Independiente Rivadavia"
    if 'independiente' in c: return "Independiente"
    if 'boca' in c: return "Boca Juniors"
    if 'river' in c: return "River Plate"
    if 'velez' in c: return "Vélez Sarsfield"
    if 'sanlorenzo' in c: return "San Lorenzo"
    if 'racing' in c: return "Racing Club"
    if 'rosario' in c: return "Rosario Central"
    if 'argentinos' in c: return "Argentinos Juniors"
    if 'defensa' in c: return "Defensa y Justicia"
    if 'talleres' in c: return "Talleres de Córdoba"
    if 'tucuman' in c: return "Atlético Tucumán"
    if 'union' in c: return "Unión de Santa Fe"
    if 'cordoba' in c and 'central' in c: return "Central Córdoba SE"
    if 'gimnasia' in c and ('mendoza' in c or 'm' in c.replace('gimnasiam', 'm')): return "Gimnasia Mendoza"
    if 'gimnasia' in c: return "Gimnasia La Plata"
    if 'riestra' in c: return "Deportivo Riestra"
    if 'estudiantes' in c and ('rio' in c or 'rc' in c or 'cuarto' in c): return "Estudiantes Río Cuarto"
    if 'estudiantes' in c: return "Estudiantes de La Plata"
    if 'barracas' in c: return "Barracas Central"
    if 'lanus' in c: return "Lanús"
    if 'sarmiento' in c: return "Sarmiento"
    if 'tigre' in c: return "Tigre"
    if 'huracan' in c: return "Huracán"
    if 'instituto' in c: return "Instituto"
    if 'belgrano' in c: return "Belgrano"
    if 'banfield' in c: return "Banfield"
    if 'platense' in c: return "Platense"
    if 'aldosivi' in c: return "Aldosivi"
    return "Desconocido"

# =================================================================
# 2. MOTOR MATEMÁTICO DE DATA SCIENCE (Softmax Distribuido)
# =================================================================
def redistribuir_porcentajes(probs, slots):
    # Asegura que si un equipo supera el 100%, ese excedente se reparta a los de abajo
    for _ in range(10):
        exceso = sum(p - 100.0 for p in probs if p > 100.0)
        if exceso <= 0.01: break
        
        probs = [min(100.0, p) for p in probs]
        receptores = [i for i, p in enumerate(probs) if p < 100.0 and p > 0.0]
        
        if not receptores: break
        espacio_libre = sum(probs[i] for i in receptores)
        
        for i in receptores:
            if espacio_libre > 0:
                probs[i] += exceso * (probs[i] / espacio_libre)
            else:
                probs[i] += exceso / len(receptores)
    return [min(100.0, p) for p in probs]

def aplicar_probabilidades(datos, tipo="anual"):
    total = len(datos)
    if total == 0: return

    pj_total = 32 if tipo == "anual" else 16

    # 1. Calculamos la esperanza matemática de cada equipo
    for eq in datos:
        pts = eq['pts']
        pj = eq['pj']
        pj_restantes = max(0, pj_total - pj)
        ppg = pts / pj if pj > 0 else 1.3
        
        eq['mu'] = pts + (pj_restantes * ppg)
        eq['pmax'] = pts + (pj_restantes * 3)
        eq['pmin'] = pts
        eq['pj_res'] = pj_restantes

    pts_1 = datos[0]['pts'] if total > 0 else 0
    pts_3 = datos[2]['pts'] if total > 2 else 0
    pts_8 = datos[7]['pts'] if total > 7 else 0
    pts_9 = datos[8]['pts'] if total > 8 else 0
    pts_max_descenso = datos[-2]['pmax'] if total > 1 else 0

    # 2. Motor Softmax: Reparte el 100% exacto entre competidores
    def calcular_softmax(slots, pts_corte, es_descenso=False):
        pesos = []
        max_mu = max([eq['mu'] for eq in datos])
        
        for eq in datos:
            # Temperatura dinámica: Faltando pocas fechas la eliminación es más certera
            alpha = 3.0 / max(1, eq['pj_res'])
            
            if not es_descenso:
                if eq['pmax'] < pts_corte:
                    pesos.append(0.0) # Matemáticamente eliminado
                elif eq['pj_res'] == 0 and eq['pts'] >= pts_corte:
                    pesos.append(float('inf')) # Clasificado asegurado
                else:
                    pesos.append(math.exp(alpha * (eq['mu'] - max_mu)))
            else:
                if eq['pmin'] > pts_max_descenso:
                    pesos.append(0.0) # Salvado del descenso
                elif eq['pj_res'] == 0 and eq['pts'] <= pts_max_descenso:
                    pesos.append(float('inf')) # Descendido
                else:
                    pesos.append(math.exp(-alpha * (eq['mu'] - max_mu)))
        
        inf_count = sum(1 for w in pesos if w == float('inf'))
        if inf_count > 0:
            probs = [(slots / inf_count * 100.0 if w == float('inf') else 0.0) for w in pesos]
            return [min(100.0, p) for p in probs]

        suma_pesos = sum(pesos)
        if suma_pesos == 0: return [0.0] * total
        
        probs_crudas = [(w / suma_pesos) * slots * 100.0 for w in pesos]
        return redistribuir_porcentajes(probs_crudas, slots)

    if tipo == "anual":
        p_top1 = calcular_softmax(1, pts_1)
        p_top3 = calcular_softmax(3, pts_3)
        p_top9 = calcular_softmax(9, pts_9)
        p_bot2 = calcular_softmax(2, 0, True)

        for i, eq in enumerate(datos):
            c1 = p_top1[i]
            c3 = max(c1, p_top3[i])
            c9 = max(c3, p_top9[i])
            
            champ = c1
            lib = c3 - c1
            sud = c9 - c3
            rel = p_bot2[i]

            # Mínimos de fe si las matemáticas todavía le dan vida
            if eq['pmax'] >= pts_1 and champ < 0.01: champ = 0.01
            if eq['pmax'] >= pts_3 and lib < 0.01 and champ == 0: lib = 0.01
            if eq['pmax'] >= pts_9 and sud < 0.01 and lib == 0 and champ == 0: sud = 0.01
            if eq['pmin'] <= pts_max_descenso and rel < 0.01: rel = 0.01

            eq.update({
                "champ": round(champ, 2),
                "lib": round(lib, 2),
                "sud": round(sud, 2),
                "rel": round(rel, 2)
            })

    elif tipo == "zona":
        p_top8 = calcular_softmax(8, pts_8)
        for i, eq in enumerate(datos):
            playoff = p_top8[i]
            if eq['pmax'] >= pts_8 and playoff < 0.01: playoff = 0.01
            eq["playoff"] = round(playoff, 2)

# =================================================================
# 3. EXTRACCIÓN Y PROCESAMIENTO INTOCABLE
# =================================================================
def extraer_tablas_validas(html_str):
    tablas = pd.read_html(io.StringIO(html_str))
    return [t for t in tablas if any('Equipo' in str(c) for c in t.columns)]

def procesar_dataframe(df):
    equipos = []
    df.columns = [str(c).upper().strip() for c in df.columns]
    col_equipo = [c for c in df.columns if 'EQUIPO' in c][0]
    
    for i in range(len(df)):
        nombre_crudo = str(df.iloc[i][col_equipo])
        nombre_limpio = limpiar_nombre(nombre_crudo)
        
        try:
            pts = int(df.iloc[i]['PTS'])
            pj = int(df.iloc[i]['PJ'])
            pg = int(df.iloc[i]['PG'])
            pe = int(df.iloc[i]['PE'])
            pp = int(df.iloc[i]['PP'])
            col_dg = [c for c in df.columns if 'DIF' in c or 'DG' in c]
            dg = int(df.iloc[i][col_dg[0]]) if col_dg else 0
        except:
            pts = int(df.iloc[i, 3])
            pj = int(df.iloc[i, 4])
            pg = int(df.iloc[i, 5])
            pe = int(df.iloc[i, 6])
            pp = int(df.iloc[i, 7])
            dg = int(df.iloc[i, 10])
        
        equipos.append({
            "name": nombre_limpio,
            "pj": pj, "pg": pg, "pe": pe, "pp": pp, "dg": dg, "pts": pts
        })
    return equipos

def procesar_datos():
    arg_tz = timezone(timedelta(hours=-3))
    fecha_actual = datetime.now(arg_tz).strftime("%d/%m/%Y a las %H:%M hs")
    
    datos_finales = {"anual": [], "zonaA": [], "zonaB": [], "ultima_actualizacion": fecha_actual}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        url_zonas = "https://www.futbolargentino.com/primera-division/tabla-de-posiciones"
        req_zonas = urllib.request.Request(url_zonas, headers=headers)
        html_zonas = urllib.request.urlopen(req_zonas, timeout=15).read().decode('utf-8')
        
        tablas_zonas = extraer_tablas_validas(html_zonas)
        if len(tablas_zonas) >= 2:
            datos_finales["zonaA"] = procesar_dataframe(tablas_zonas[0])
            datos_finales["zonaB"] = procesar_dataframe(tablas_zonas[1])
            
            for zona in ["zonaA", "zonaB"]:
                datos_finales[zona].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
                for i, eq in enumerate(datos_finales[zona]): eq["pos"] = i + 1
                aplicar_probabilidades(datos_finales[zona], "zona")

            todos_los_equipos = datos_finales["zonaA"] + datos_finales["zonaB"]
            for eq in todos_los_equipos:
                nombre = eq["name"]
                historial = apertura_stats.get(nombre, {"pj": 16, "pg": 0, "pe": 0, "pp": 0, "dg": 0, "pts": 0})
                
                eq_anual = {
                    "name": nombre,
                    "pj": eq["pj"] + historial["pj"],
                    "pg": eq["pg"] + historial["pg"],
                    "pe": eq["pe"] + historial["pe"],
                    "pp": eq["pp"] + historial["pp"],
                    "dg": eq["dg"] + historial["dg"],
                    "pts": eq["pts"] + historial["pts"]
                }
                datos_finales["anual"].append(eq_anual)

            datos_finales["anual"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
            for i, eq in enumerate(datos_finales["anual"]): eq["pos"] = i + 1
            aplicar_probabilidades(datos_finales["anual"], "anual")

        print(f"¡Éxito! Tabla Anual construida localmente y proyecciones calculadas. Actualizado el {fecha_actual}")
        
    except Exception as e:
        print(f"Error detectado: {e}")
        for zona in ["anual", "zonaA", "zonaB"]:
            for i in range(1, 16 if zona != "anual" else 31):
                datos_finales[zona].append({
                    "pos": i, "name": f"Sin datos", "pj": 0, "pg": 0, "pe": 0, "pp": 0, "dg": 0, "pts": 0,
                    "champ": 0, "lib": 0, "sud": 0, "rel": 0, "playoff": 0
                })

    with open('pronosticos.json', 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    procesar_datos()
