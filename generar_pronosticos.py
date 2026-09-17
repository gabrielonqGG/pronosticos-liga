import json
import urllib.request
import pandas as pd
import re
import io
import math
from datetime import datetime, timezone, timedelta

# Nombres estrictos para evitar cualquier bug de lectura HTML y cruce de diccionarios
EQUIPOS_OFICIALES = [
    "Argentinos Juniors", "Independiente Rivadavia", "Vélez Sarsfield", "Boca Juniors",
    "Gimnasia La Plata", "Rosario Central", "River Plate", "Estudiantes de La Plata",
    "Belgrano", "Independiente", "Instituto", "Defensa y Justicia", "Gimnasia Mendoza",
    "Unión de Santa Fe", "Lanús", "Sarmiento", "Tigre", "Huracán", "Barracas Central",
    "San Lorenzo", "Talleres de Córdoba", "Newells Old Boys", "Atlético Tucumán",
    "Racing Club", "Banfield", "Platense", "Central Córdoba SE", "Aldosivi",
    "Estudiantes Río Cuarto", "Deportivo Riestra"
]

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

# =================================================================
# 2. MOTOR MATEMÁTICO DE DATA SCIENCE (Campana de Gauss)
# =================================================================
def normal_cdf(x, mu, sigma):
    if sigma == 0: return 1.0 if x <= mu else 0.0
    return (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0)))) / 2.0

def aplicar_probabilidades(datos, tipo="anual"):
    total = len(datos)
    if total == 0: return

    # Configurado a 32 fechas Anuales y 16 fechas de Zona
    pj_total = 32 if tipo == "anual" else 16
    
    def get_rival(idx):
        idx = max(0, min(idx, total - 1))
        eq = datos[idx]
        pj = eq['pj']
        ppg = eq['pts'] / pj if pj > 0 else 1.3
        return eq['pts'], max(0, pj_total - pj), ppg

    for pos, eq in enumerate(datos, start=1):
        pts = eq['pts']
        pj = eq['pj']
        ppg = pts / pj if pj > 0 else 1.3
        pj_restantes = max(0, pj_total - pj)

        def prob_superar(pts_B, pj_res_B, ppg_B):
            if pts + (pj_restantes * 3) < pts_B: return 0.0
            if pj_restantes == 0 and pj_res_B == 0: return 100.0 if pts >= pts_B else 0.0

            mu_A = pts + (pj_restantes * ppg)
            sigma_A = math.sqrt(pj_restantes) * 1.35
            mu_B = pts_B + (pj_res_B * ppg_B)
            sigma_B = math.sqrt(pj_res_B) * 1.35

            mu_D = mu_A - mu_B
            sigma_D = math.sqrt(sigma_A**2 + sigma_B**2)

            if sigma_D == 0: return 100.0 if mu_D >= 0 else 0.0
            p = 1.0 - normal_cdf(0, mu_D, sigma_D)
            return max(0.01, p * 100.0)

        def prob_caer(pts_B, pj_res_B, ppg_B):
            if pts_B + (pj_res_B * 3) < pts: return 0.0
            if pj_restantes == 0 and pj_res_B == 0: return 100.0 if pts <= pts_B else 0.0

            mu_A = pts + (pj_restantes * ppg)
            sigma_A = math.sqrt(pj_restantes) * 1.35
            mu_B = pts_B + (pj_res_B * ppg_B)
            sigma_B = math.sqrt(pj_res_B) * 1.35

            mu_D = mu_A - mu_B
            sigma_D = math.sqrt(sigma_A**2 + sigma_B**2)

            if sigma_D == 0: return 100.0 if mu_D <= 0 else 0.0
            p = normal_cdf(0, mu_D, sigma_D)
            return max(0.01, p * 100.0)

        if tipo == "anual":
            rival_champ = get_rival(1 if pos == 1 else 0)
            champ = prob_superar(*rival_champ)
            
            rival_lib = get_rival(3 if pos <= 3 else 2)
            lib = prob_superar(*rival_lib)

            rival_sud = get_rival(9 if pos <= 9 else 8)
            sud = prob_superar(*rival_sud)

            rival_desc = get_rival(total-3 if pos > total-2 else total-2)
            rel = prob_caer(*rival_desc)

            lib = max(0.0, lib - champ)
            sud = max(0.0, sud - lib - champ)

            eq.update({"champ": round(champ, 2), "lib": round(lib, 2), "sud": round(sud, 2), "rel": round(rel, 2)})

        elif tipo == "zona":
            rival_playoff = get_rival(8 if pos <= 8 else 7)
            playoff = prob_superar(*rival_playoff)
            eq["playoff"] = round(playoff, 2)

# =================================================================
# 3. EXTRACCIÓN Y PROCESAMIENTO
# =================================================================
def extraer_tablas_validas(html_str):
    tablas = pd.read_html(io.StringIO(html_str))
    return [t for t in tablas if any('Equipo' in str(c) for c in t.columns)]

def procesar_dataframe(df):
    equipos = []
    df.columns = [str(c).upper().strip() for c in df.columns]
    col_equipo = [c for c in df.columns if 'EQUIPO' in c][0]
    
    nombres_ordenados = sorted(EQUIPOS_OFICIALES, key=len, reverse=True)
    
    for i in range(len(df)):
        nombre_crudo = str(df.iloc[i][col_equipo])
        
        # Limpieza estricta: Si el nombre escrapeado contiene el nombre oficial, lo asigna
        nombre_limpio = nombre_crudo
        for eq in nombres_ordenados:
            if eq.replace(" ", "").lower() in nombre_crudo.replace(" ", "").lower():
                nombre_limpio = eq
                break
        
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
                # Fallback actualizado: Si por algún error de tipeo no cruza, al menos suma los 16 PJ
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
