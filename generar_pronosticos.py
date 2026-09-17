import math

def simular_prob_anual(pos, pts, pj, total_equipos):
    pj_total = 41 # 14 Copa de la Liga + 27 Liga Profesional
    pj_restantes = max(0, pj_total - pj)
    pts_en_juego = pj_restantes * 3

    # Umbrales teóricos dinámicos (cuántos puntos suele tener el equipo en esa posición en la fecha actual)
    pts_ideal_champ = (pj * 2.1)
    pts_ideal_lib = (pj * 1.75)
    pts_ideal_sud = (pj * 1.45)
    pts_ideal_desc = (pj * 1.05)

    def sigmoide(x):
        # Evita desbordamientos matemáticos
        if x > 20: return 99.9
        if x < -20: return 0.1
        return 100 / (1 + math.exp(-x))

    # Factor de volatilidad: cuantas más fechas faltan, más incierto es todo (la curva se aplana)
    volatilidad = max(1.0, pj_restantes * 0.35)

    # Probabilidades base
    champ = sigmoide((pts - pts_ideal_champ) / volatilidad)
    lib_bruto = sigmoide((pts - pts_ideal_lib) / volatilidad)
    sud_bruto = sigmoide((pts - pts_ideal_sud) / volatilidad)
    rel = sigmoide((pts_ideal_desc - pts) / volatilidad) # Invertido para el descenso

    # Ajustes por posición real para alinear el modelo con la tabla
    if pos == 1: champ += 15
    if pos <= 3: lib_bruto += 15
    if pos <= 9: sud_bruto += 10
    if pos >= total_equipos - 2: rel += 20

    # Lógica de exclusión mutua
    lib = max(0.0, lib_bruto)
    sud = max(0.0, sud_bruto - lib)

    # Recortes estrictos: Si matemáticamente no llega, es 0%
    if pts + pts_en_juego < pts_ideal_champ - 3: champ = 0.0
    if pts + pts_en_juego < pts_ideal_lib - 3: lib = 0.0
    if pts + pts_en_juego < pts_ideal_sud - 3: sud = 0.0

    return min(99.9, max(0.0, champ)), min(99.9, max(0.0, lib)), min(99.9, max(0.0, sud)), min(99.9, max(0.0, rel))

def simular_prob_zona(pos, pts, pj):
    pj_total = 14
    pj_restantes = max(0, pj_total - pj)
    pts_en_juego = pj_restantes * 3

    # Umbral histórico de clasificación (aprox 1.4 pts por partido)
    pts_ideal_clasif = (pj * 1.4)
    volatilidad = max(1.0, pj_restantes * 0.4)

    # Evitar overflow
    x = (pts - pts_ideal_clasif) / volatilidad
    prob = 99.9 if x > 20 else (0.1 if x < -20 else 100 / (1 + math.exp(-x)))

    if pos <= 8: prob += 15
    else: prob -= 15

    # Lógica matemática dura
    if pts + pts_en_juego < pts_ideal_clasif - 3: prob = 0.0
    
    return min(99.9, max(0.0, prob))
