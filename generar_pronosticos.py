import json
import urllib.request
import pandas as pd
import re
import io
import math
from datetime import datetime, timezone, timedelta

# =================================================================
# 1. BASE DE DATOS ESTÁTICA DEL APERTURA (14 Fechas)
# Completá los puntos reales con los que terminó cada equipo.
# El sistema los sumará automáticamente al Clausura en vivo.
# =================================================================
apertura_stats = {
    
# --- ZONA A ---
    "Estudiantes":      {"pj": 16, "pg": 9, "pe": 4, "pp": 3, "dg": 12, "pts": 31},
    "Boca Juniors":     {"pj": 16, "pg": 8, "pe": 6, "pp": 2, "dg": 13, "pts": 30},
    "Vélez":            {"pj": 16, "pg": 7, "pe": 7, "pp": 2, "dg": 6, "pts": 28},
    "Talleres":         {"pj": 16, "pg": 7, "pe": 5, "pp": 4, "dg": 4, "pts": 26},
    "Independiente":    {"pj": 16, "pg": 6, "pe": 6, "pp": 4, "dg": 4, "pts": 24},
    "Lanús":            {"pj": 16, "pg": 6, "pe": 6, "pp": 4, "dg": 3, "pts": 24},
    "San Lorenzo":      {"pj": 16, "pg": 5, "pe": 7, "pp": 4, "dg": 0, "pts": 22},
    "Unión":            {"pj": 16, "pg": 5, "pe": 6, "pp": 5, "dg": 4, "pts": 21},
    "Instituto":        {"pj": 16, "pg": 6, "pe": 3, "pp": 7, "dg": 0, "pts": 21},
    "Defensa y Jus.":   {"pj": 16, "pg": 4, "pe": 7, "pp": 5, "dg": -3, "pts": 19},
    "Gimnasia (M)":     {"pj": 16, "pg": 5, "pe": 4, "pp": 7, "dg": -8, "pts": 19},
    "Platense":         {"pj": 16, "pg": 3, "pe": 7, "pp": 6, "dg": -5, "pts": 16},
    "Córdoba SdE":      {"pj": 16, "pg": 4, "pe": 4, "pp": 8, "dg": -10, "pts": 16},
    "Newell's":         {"pj": 16, "pg": 3, "pe": 6, "pp": 7, "dg": -12, "pts": 15},
    "Riestra":          {"pj": 16, "pg": 1, "pe": 8, "pp": 7, "dg": -7, "pts": 11},

    # --- ZONA B ---
    "Independ. (M)":    {"pj": 16, "pg": 10, "pe": 4, "pp": 2, "dg": 14, "pts": 34},
    "River":            {"pj": 16, "pg": 9, "pe": 2, "pp": 5, "dg": 10, "pts": 29},
    "Argentinos":       {"pj": 16, "pg": 8, "pe": 5, "pp": 3, "dg": 4, "pts": 29},
    "Central":          {"pj": 16, "pg": 8, "pe": 4, "pp": 4, "dg": 4, "pts": 28},
    "Belgrano":         {"pj": 16, "pg": 7, "pe": 5, "pp": 4, "dg": 4, "pts": 26},
    "Gimnasia (LP)":    {"pj": 16, "pg": 8, "pe": 2, "pp": 6, "dg": 0, "pts": 26},
    "Huracán":          {"pj": 16, "pg": 5, "pe": 7, "pp": 4, "dg": 4, "pts": 22},
    "Racing":           {"pj": 16, "pg": 5, "pe": 6, "pp": 5, "dg": 2, "pts": 21},
    "Barracas":         {"pj": 16, "pg": 5, "pe": 6, "pp": 5, "dg": 0, "pts": 21},
    "Tigre":            {"pj": 16, "pg": 4, "pe": 8, "pp": 4, "dg": 3, "pts": 20},
    "Sarmiento":        {"pj": 16, "pg": 6, "pe": 1, "pp": 9, "dg": -7, "pts": 19},
    "Banfield":         {"pj": 16, "pg": 5, "pe": 3, "pp": 8, "dg": -2, "pts": 18},
    "Atl. Tucumán":     {"pj": 16, "pg": 3, "pe": 5, "pp": 8, "dg": -5, "pts": 14},
    "Aldosivi":         {"pj": 16, "pg": 0, "pe": 8, "pp": 8, "dg": -13, "pts": 8},
    "Estudiantes RC":   {"pj": 16, "pg": 1, "pe": 2, "pp": 13, "dg": -19, "pts": 5}
}


# =================================================================
# 2. MOTOR MATEMÁTICO DE PROBABILIDADES
# =================================================================
def normal_cdf(x, mu, sigma):
    if sigma == 0: return 1.0 if x <= mu else 0.0
    return (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0)))) / 2.0

def aplicar_probabilidades(datos, tipo="anual"):
    total = len(datos)
    if total == 0: return

    pj_total = 41 if tipo == "anual" else 14
    pts_1 = datos[0]['pts'] if total > 0 else 0
    pts_3 = datos[2]['pts'] if total > 2 else 0
    pts_8 = datos[7]['pts'] if total > 7 else 0
    pts_9 = datos[8]['pts'] if total > 8 else 0
    
    if total > 1:
        pts_max_descenso = datos[-2]['pts'] + (max(0, pj_total - datos[-2]['pj']) * 3)
    else:
        pts_max_descenso = 0

    for pos, eq in enumerate(datos, start=1):
        pts = eq['pts']
        pj = eq['pj']
        
        pj_restantes = max(0, pj_total - pj)
        pts_en_juego = pj_restantes * 3
        pts_maximos = pts + pts_en_juego

        if tipo == "anual":
            puede_champ = pts_maximos >= pts_1
            puede_lib = pts_maximos >= pts_3
            puede_sud = pts_maximos >= pts_9
            salvado_matematicamente = pts > pts_max_descenso
            
            def calc_pct(puede_llegar, pts_objetivo, pos_actual, target_pos):
                if not puede_llegar: return 0.0
                if pts >= pts_objetivo and pj_restantes == 0: return 100.0
                
                distancia = pts_objetivo - pts
                if distancia <= 0:
                    ventaja = abs(distancia)
                    return min(99.99, 80.0 + (ventaja * 2.5) + (15.0 / max(1, pj_restantes)))
                
                ratio = distancia / pts_en_juego if pts_en_juego > 0 else 1
                prob = (1.0 - ratio) * 100.0
                penalizacion = max(0, (pos_actual - target_pos) * 2.5)
                return max(0.01, prob - penalizacion)
            
            champ = calc_pct(puede_champ, pts_1, pos, 1)
            lib = calc_pct(puede_lib, pts_3, pos, 3)
            sud = calc_pct(puede_sud, pts_9, pos, 9)
            
            if salvado_matematicamente:
                rel = 0.0
            else:
                pts_salvacion = datos[-3]['pts'] if total > 2 else 0
                distancia_a_salvacion = pts_salvacion - pts
                if distancia_a_salvacion <= 0:
                    rel = max(0.01, 15.0 - abs(distancia_a_salvacion) * 3)
                else:
                    ratio = distancia_a_salvacion / pts_en_juego if pts_en_juego > 0 else 1
                    rel = min(99.99, 50.0 + (ratio * 50.0))

            if pos == 1: champ = max(champ, 90.0)
            lib = max(0.0, lib - champ)
            sud = max(0.0, sud - lib - champ)

            eq.update({"champ": round(champ, 2), "lib": round(lib, 2), "sud": round(sud, 2), "rel": round(rel, 2)})

        elif tipo == "zona":
            puede_playoff = pts_maximos >= pts_8
            
            if not puede_playoff:
                prob = 0.0
            elif pts >= pts_8 and pj_restantes == 0:
                prob = 100.0
            else:
                distancia = pts_8 - pts
                if distancia <= 0:
                    ventaja = abs(distancia)
                    prob = min(99.99, 85.0 + (ventaja * 2.0))
                else:
                    ratio = distancia / pts_en_juego if pts_en_juego > 0 else 1
                    prob = (1.0 - ratio) * 100.0
                    penalizacion = max(0, (pos - 8) * 3.0)
                    prob = max(0.01, prob - penalizacion)
                    
            eq["playoff"] = round(prob, 2)

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
    
    for i in range(len(df)):
        nombre_crudo = str(df.iloc[i][col_equipo])
        nombre_letras = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', nombre_crudo).strip()
        nombre_limpio = re.sub(r'([a-zñáéíóú])([A-ZÑÁÉÍÓÚ])', r'\1|\2', nombre_letras).split('|')[0].strip()
        
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
        # SOLO hacemos una petición web a la tabla del Clausura que está perfectamente actualizada
        url_zonas = "https://www.futbolargentino.com/primera-division/tabla-de-posiciones"
        req_zonas = urllib.request.Request(url_zonas, headers=headers)
        html_zonas = urllib.request.urlopen(req_zonas, timeout=15).read().decode('utf-8')
        
        tablas_zonas = extraer_tablas_validas(html_zonas)
        if len(tablas_zonas) >= 2:
            datos_finales["zonaA"] = procesar_dataframe(tablas_zonas[0])
            datos_finales["zonaB"] = procesar_dataframe(tablas_zonas[1])
            
            # Calculamos las probabilidades para las zonas en base a los puntos de hoy
            for zona in ["zonaA", "zonaB"]:
                datos_finales[zona].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
                for i, eq in enumerate(datos_finales[zona]): eq["pos"] = i + 1
                aplicar_probabilidades(datos_finales[zona], "zona")

            # Construimos la Tabla Anual sumando el Apertura + el Clausura en vivo
            todos_los_equipos = datos_finales["zonaA"] + datos_finales["zonaB"]
            for eq in todos_los_equipos:
                nombre = eq["name"]
                # Buscamos los puntos históricos (Si no completaste alguno, por defecto suma 0)
                historial = apertura_stats.get(nombre, {"pj": 14, "pg": 0, "pe": 0, "pp": 0, "dg": 0, "pts": 0})
                
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

            # Ordenamos y calculamos las probabilidades Anuales reales
            datos_finales["anual"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
            for i, eq in enumerate(datos_finales["anual"]): eq["pos"] = i + 1
            aplicar_probabilidades(datos_finales["anual"], "anual")

        print(f"¡Éxito! Tabla Anual construida localmente. Actualizado el {fecha_actual}")
        
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
