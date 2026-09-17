import json
import urllib.request
import pandas as pd
import re
import io

def simular_prob_anual(pos, total_equipos):
    # Fórmula lineal: a mejor posición, más porcentaje
    champ = round(max(0, 90.0 - (pos - 1) * 15.0), 1) if pos <= 5 else 0.0
    lib = round(max(0, 85.0 - (pos - 1) * 8.0), 1) if pos <= 10 else 0.0
    sud = round(max(0, 80.0 - abs(pos - 7) * 10.0), 1) if pos <= 15 else 0.0
    rel = round(max(0, 95.0 - (total_equipos - pos) * 15.0), 1) if pos >= total_equipos - 4 else 0.0
    return champ, lib, sud, rel

def simular_prob_zona(pos):
    return round(max(0, 98.0 - (pos - 1) * 11.0), 1)

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
        
        # Expresión Regular para separar nombres pegados (Ej: "PlateRiver" -> "Plate")
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
    datos_finales = {"anual": [], "zonaA": [], "zonaB": []}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # 1. Procesar TABLA ANUAL (Acumulada)
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
                c, l, s, r = simular_prob_anual(eq["pos"], total_equipos)
                eq.update({"champ": c, "lib": l, "sud": s, "rel": r})

        # 2. Procesar ZONAS CLAUSURA (Separadas naturalmente)
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
                    eq["playoff"] = simular_prob_zona(eq["pos"])

        print(f"¡Éxito! Anual: {len(datos_finales['anual'])}, Zona A: {len(datos_finales['zonaA'])}, Zona B: {len(datos_finales['zonaB'])}")
        
    except Exception as e:
        print(f"Error detectado: {e}")
        # Salvavidas en caso de falla extrema
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
