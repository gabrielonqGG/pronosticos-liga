import json
import urllib.request
import pandas as pd
import re
import io
import math
from datetime import datetime, timezone, timedelta

# Función de Distribución Acumulada (Distribución Normal)
def normal_cdf(x, mu, sigma):
    if sigma == 0: return 1.0 if x <= mu else 0.0
    return (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0)))) / 2.0

def simular_prob_anual(pos, pts, pj, total_equipos):
    pj_total = 41 # 14 Copa + 27 Liga
    pj_restantes = max(0, pj_total - pj)
    pts_en_juego = pj_restantes * 3

    # Si el torneo terminó
    if pj_restantes == 0:
        return (100.0 if pos == 1 else 0.0,
                100.0 if 1 <= pos <= 3 else 0.0,
                100.0 if 4 <= pos <= 9 else 0.0,
                100.0 if pos >= total_equipos - 1 else 0.0)

    # Proyección estadística del equipo
    ppg_actual = pts / pj if pj > 0 else 1.3
    mu_restante = pj_restantes * ppg_actual
    sigma_restante = math.sqrt(pj_restantes) * 1.35 # Desviación estándar de fútbol

    # Umbrales históricos de clasificación para 41 fechas
    umbral_champ = 84
    umbral_lib = 71
    umbral_sud = 58
    umbral_desc = 42

    def calcular_probabilidad_llegar(umbral):
        if pts >= umbral: return 100.0
        if pts + pts_en_juego < umbral: return 0.0 # Eliminación matemática estricta
        pts_necesarios = umbral - pts
        p = 1.0 - normal_cdf(pts_necesarios, mu_restante, sigma_restante)
        return p * 100.0

    def calcular_probabilidad_caer(umbral):
        if pts + pts_en_juego < umbral: return 100.0
        if pts >= umbral and pj_restantes == 0: return 0.0
        pts_necesarios = umbral - pts
        p = normal_cdf(pts_necesarios, mu_restante, sigma_restante)
        return p * 100.0

    # Probabilidades puras
    champ_bruto = calcular_probabilidad_llegar(umbral_champ)
    lib_bruto = calcular_probabilidad_llegar(umbral_lib)
    sud_bruto = calcular_probabilidad_llegar(umbral_sud)
    rel_bruto = calcular_probabilidad_caer(umbral_desc)

    # Factor de corrección por la posición actual en la tabla
    factor_lideres = max(0.01, 1.0 - ((pos - 1) / total_equipos))
    factor_colistas = max(0.01, 1.0 - ((total_equipos - pos) / total_equipos))

    champ = champ_bruto * math.pow(factor_lideres, 1.5)
    lib = lib_bruto * factor_lideres
    sud = sud_bruto * math.sqrt(factor_lideres)
    rel = rel_bruto * math.pow(factor_colistas, 1.5)

    # Exclusión mutua
    sud = max(0.0, sud - lib)

    return round(min(99.99, max(0.0, champ)), 2), \
           round(min(99.99, max(0.0, lib)), 2), \
           round(min(99.99, max(0.0, sud)), 2), \
           round(min(99.99, max(0.0, rel)), 2)

def simular_prob_zona(pos, pts, pj):
    pj_total = 14
    pj_restantes = max(0, pj_total - pj)
    pts_en_juego = pj_restantes * 3

    if pj_restantes == 0:
        return 100.0 if pos <= 8 else 0.0

    ppg_actual = pts / pj if pj > 0 else 1.3
    mu_restante = pj_restantes * ppg_actual
    sigma_restante = math.sqrt(pj_restantes) * 1.35

    umbral_playoff = 19 # Puntos históricos para clasificar 8vo

    if pts >= umbral_playoff: return 99.99
    if pts + pts_en_juego < umbral_playoff: return 0.0

    pts_necesarios = umbral_playoff - pts
    p = 1.0 - normal_cdf(pts_necesarios, mu_restante, sigma_restante)
    
    factor_pos = max(0.01, 1.0 - ((pos - 1) / 15.0))
    prob = (p * 100.0) * factor_pos

    return round(min(99.99, max(0.0, prob)), 2)

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
    # Calculamos la hora exacta en Argentina (UTC-3)
    arg_tz = timezone(timedelta(hours=-3))
    fecha_actual = datetime.now(arg_tz).strftime("%d/%m/%Y a las %H:%M hs")
    
    datos_finales = {"anual": [], "zonaA": [], "zonaB": [], "ultima_actualizacion": fecha_actual}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        url_anual = "https://www.futbolargentino.com/primera-division/tabla-general/tabla-de-posiciones"
        req_anual = urllib.request.Request(url_anual, headers=headers)
        html_anual = urllib.request.urlopen(req_anual, timeout=15).read().decode('utf-8')
        
        tablas_anual = extraer_tablas_validas(html_anual)
        if tablas_anual:
            datos_finales["anual"] = procesar_dataframe(tablas_anual[0])
            datos_finales["anual"].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
            
            total_equipos = len(datos_finales["anual"])
            for i, eq in enumerate(datos_finales["anual"]):
                eq["pos"] = i + 1
                c, l, s, r = simular_prob_anual(eq["pos"], eq["pts"], eq["pj"], total_equipos)
                eq.update({"champ": c, "lib": l, "sud": s, "rel": r})

        url_zonas = "https://www.futbolargentino.com/primera-division/tabla-de-posiciones"
        req_zonas = urllib.request.Request(url_zonas, headers=headers)
        html_zonas = urllib.request.urlopen(req_zonas, timeout=15).read().decode('utf-8')
        
        tablas_zonas = extraer_tablas_validas(html_zonas)
        if len(tablas_zonas) >= 2:
            datos_finales["zonaA"] = procesar_dataframe(tablas_zonas[0])
            datos_finales["zonaB"] = procesar_dataframe(tablas_zonas[1])
            
            for zona in ["zonaA", "zonaB"]:
                datos_finales[zona].sort(key=lambda x: (x['pts'], x['dg']), reverse=True)
                for i, eq in enumerate(datos_finales[zona]):
                    eq["pos"] = i + 1
                    eq["playoff"] = simular_prob_zona(eq["pos"], eq["pts"], eq["pj"])

        print(f"¡Éxito! Actualizado el {fecha_actual}")
        
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
