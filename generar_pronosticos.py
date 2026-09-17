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

def aplicar_probabilidades(datos, tipo="anual"):
    total = len(datos)
    if total == 0: return

    # Partidos totales en el año (14 Copa + 27 Liga) o en la Zona (14)
    pj_total = 41 if tipo == "anual" else 14
    
    # Identificamos los puntos REALES de los rivales a vencer en este instante
    pts_1 = datos[0]['pts'] if total > 0 else 0
    pts_3 = datos[2]['pts'] if total > 2 else 0
    pts_8 = datos[7]['pts'] if total > 7 else 0
    pts_9 = datos[8]['pts'] if total > 8 else 0
    
    # El puntaje MÁXIMO que puede llegar a alcanzar el equipo que hoy está descendiendo (anteúltimo)
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
            # 1. Eliminaciones matemáticas estrictas (Corte a 0.0%)
            puede_champ = pts_maximos >= pts_1
            puede_lib = pts_maximos >= pts_3
            puede_sud = pts_maximos >= pts_9
            salvado_matematicamente = pts > pts_max_descenso
            
            def calc_pct(puede_llegar, pts_objetivo, pos_actual, target_pos):
                if not puede_llegar: return 0.0
                if pts >= pts_objetivo and pj_restantes == 0: return 100.0
                
                distancia = pts_objetivo - pts
                # Si ya está adentro de los puestos de clasificación:
                if distancia <= 0:
                    ventaja = abs(distancia)
                    # Mayor ventaja = porcentaje más cercano a 100
                    return min(99.99, 80.0 + (ventaja * 2.5) + (15.0 / max(1, pj_restantes)))
                
                # Si está afuera, depende de cuántos puntos necesita ganar de los que quedan
                ratio = distancia / pts_en_juego if pts_en_juego > 0 else 1
                prob = (1.0 - ratio) * 100.0
                
                # Penalización por cantidad de equipos que tiene que superar
                penalizacion = max(0, (pos_actual - target_pos) * 2.5)
                return max(0.01, prob - penalizacion) # Mínimo 0.01% si matemáticamente tiene chance
            
            champ = calc_pct(puede_champ, pts_1, pos, 1)
            lib = calc_pct(puede_lib, pts_3, pos, 3)
            sud = calc_pct(puede_sud, pts_9, pos, 9)
            
            # Lógica inversa para el descenso
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

            # Ajuste visual de exclusión (quien va a Libertadores, no suma % en Sudamericana)
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
