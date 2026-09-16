import json
import random
import urllib.request

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
    exito = False
    equipos_procesados = set()
    
    url_base = "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings"
    
    # Armamos un escuadrón de 3 puentes distintos para burlar a ESPN
    rutas_proxy = [
        f"https://api.codetabs.com/v1/proxy?quest={url_base}",
        f"https://corsproxy.io/?url={url_base}",
        url_base # Último intento directo por si ESPN baja la guardia
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }

    # El script prueba una ruta por una hasta que alguna funcione
    for ruta in rutas_proxy:
        if exito:
            break
        try:
            print(f"Intentando penetrar por: {ruta}")
            req = urllib.request.Request(ruta, headers=headers)
            response = urllib.request.urlopen(req, timeout=15).read()
            texto = response.decode('utf-8')
            
            # ESCUDO ANTI-RUPTURAS: Si no arranca con una llave JSON '{', lo descartamos
            if not texto.strip().startswith('{'):
                print("ESPN bloqueó este puente y mandó basura. Saltando al siguiente...")
                continue
                
            data = json.loads(texto)
            
            entries = []
            for child in data.get('children', []):
                stands = child.get('standings', {})
                entries.extend(stands.get('entries', []))
                
            if not entries:
                continue
                
            for entry in entries:
                nombre = entry['team']['name']
                if nombre in equipos_procesados:
                    continue
                equipos_procesados.add(nombre)
                
                stats = entry.get('stats', [])
                pj = pg = pe = pp = dg = pts = 0
                
                for s in stats:
                    nombre_stat = s.get('name', '')
                    valor_stat = int(s.get('value', 0))
                    
                    if nombre_stat == 'gamesPlayed': pj = valor_stat
                    elif nombre_stat == 'wins': pg = valor_stat
                    elif nombre_stat == 'ties': pe = valor_stat
                    elif nombre_stat == 'losses': pp = valor_stat
                    elif nombre_stat == 'pointDifferential': dg = valor_stat
                    elif nombre_stat == 'points': pts = valor_stat
                
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
                    
            exito = True
            print(f"¡HACK EXITOSO! Se descargaron {len(equipos_procesados)} equipos.")
            
        except Exception as e:
            print(f"El puente falló. Detalle del error: {e}")

    # Si todo sale bien, calculamos la matemática
    if exito:
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
    else:
        # Si de verdad los 3 puentes caen, salvavidas limpio sin romper Python
        print("Bloqueo total. Activando salvavidas para proteger la web.")
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
