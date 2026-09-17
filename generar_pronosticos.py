import json
import urllib.request
import pandas as pd
import re
import io
import math
from datetime import datetime, timezone, timedelta

def simular_prob_anual(pos, pts, pj, total_equipos):
    pj_total = 41
    pj_restantes = max(0, pj_total - pj)
    pts_en_juego = pj_restantes * 3

    pts_ideal_champ = (pj * 2.1)
    pts_ideal_lib = (pj * 1.75)
    pts_ideal_sud = (pj * 1.45)
    pts_ideal_desc = (pj * 1.05)

    def sigmoide(x):
        if x > 20: return 99.9
        if x < -20: return 0.1
        return 100 / (1 + math.exp(-x))

    volatilidad = max(1.0, pj_restantes * 0.35)

    champ = sigmoide((pts - pts_ideal_champ) / volatilidad)
    lib_bruto = sigmoide((pts - pts_ideal_lib) / volatilidad)
    sud_bruto = sigmoide((pts - pts_ideal_sud) / volatilidad)
    rel = sigmoide((pts_ideal_desc - pts) / volatilidad) 

    if pos == 1: champ += 15
    if pos <= 3: lib_bruto += 15
    if pos <= 9: sud_bruto += 10
    if pos >= total_equipos - 2: rel += 20

    lib = max(0.0, lib_bruto)
    sud = max(0.0, sud_bruto - lib)

    if pts + pts_en_juego < pts_ideal_champ - 3: champ = 0.0
    if pts + pts_en_juego < pts_ideal_lib - 3: lib = 0.0
    if pts + pts_en_juego < pts_ideal_sud - 3: sud = 0.0

    return min(99.9, max(0.0, champ)), min(99.9, max(0.0, lib)), min(99.9, max(0.0, sud)), min(99.9, max(0.0, rel))

def simular_prob_zona(pos, pts, pj):
    pj_total = 14
    pj_restantes = max(0, pj_total - pj)
    pts_en_juego = pj_restantes * 3
    pts_ideal_clasif = (pj * 1.4)
    volatilidad = max(1.0, pj_restantes * 0.4)

    x = (pts - pts_ideal_clasif) / volatilidad
    prob = 99.9 if x > 20 else (0.1 if x < -20 else 100 / (1 + math.exp(-x)))

    if pos <= 8: prob += 15
    else: prob -= 15

    if pts + pts_en_juego < pts_ideal_clasif - 3: prob = 0.0
    
    return min(99.9, max(0.0, prob))

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
