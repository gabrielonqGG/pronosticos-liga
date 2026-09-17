import math

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
        # Probabilidad de que los puntos restantes sean >= a los necesarios
        p = 1.0 - normal_cdf(pts_necesarios, mu_restante, sigma_restante)
        return p * 100.0

    def calcular_probabilidad_caer(umbral):
        if pts + pts_en_juego < umbral: return 100.0
        if pts >= umbral and pj_restantes == 0: return 0.0
        pts_necesarios = umbral - pts
        p = normal_cdf(pts_necesarios, mu_restante, sigma_restante)
        return p * 100.0

    # Probabilidades puras basadas en rendimiento proyectado
    champ_bruto = calcular_probabilidad_llegar(umbral_champ)
    lib_bruto = calcular_probabilidad_llegar(umbral_lib)
    sud_bruto = calcular_probabilidad_llegar(umbral_sud)
    rel_bruto = calcular_probabilidad_caer(umbral_desc)

    # Factor de corrección de la tabla (ajusta según la posición actual frente a competidores)
    factor_lideres = max(0.01, 1.0 - ((pos - 1) / total_equipos))
    factor_colistas = max(0.01, 1.0 - ((total_equipos - pos) / total_equipos))

    champ = champ_bruto * math.pow(factor_lideres, 1.5)
    lib = lib_bruto * factor_lideres
    sud = sud_bruto * math.sqrt(factor_lideres)
    rel = rel_bruto * math.pow(factor_colistas, 1.5)

    # Exclusión mutua: El que clasifica a Libertadores no va a Sudamericana
    sud = max(0.0, sud - lib)

    # Retornamos con 2 decimales exactos para que el Frontend los procese
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

    umbral_playoff = 19 # Puntos históricos para clasificar 8vo en zonas de 14/15 equipos

    if pts >= umbral_playoff: return 99.99
    if pts + pts_en_juego < umbral_playoff: return 0.0 # Eliminado matemáticamente

    pts_necesarios = umbral_playoff - pts
    p = 1.0 - normal_cdf(pts_necesarios, mu_restante, sigma_restante)
    
    # Ajuste por posición en la zona
    factor_pos = max(0.01, 1.0 - ((pos - 1) / 15.0))
    prob = (p * 100.0) * factor_pos

    return round(min(99.99, max(0.0, prob)), 2)
