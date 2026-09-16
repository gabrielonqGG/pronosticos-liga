import pandas as pd
import math
import json

# Distribución de Poisson para predecir goles (0 a 5 goles)
def prob_goles(lmbda):
    return [(lmbda**k * math.exp(-lmbda)) / math.factorial(k) for k in range(6)]

# Aquí podrías cargar tu CSV: df = pd.read_csv("datos_liga.csv")
# Usaremos un DataFrame de ejemplo para que funcione directamente:
datos_partidos = {
    "fecha": ["20 Sep", "20 Sep", "21 Sep"],
    "local": ["Talleres", "Boca Juniors", "Belgrano"],
    "visitante": ["Instituto", "River Plate", "Racing Club"],
    "goles_esperados_local": [1.6, 1.2, 1.1], # Calculado de promedios históricos
    "goles_esperados_visitante": [0.8, 1.3, 1.1]
}

df = pd.DataFrame(datos_partidos)
pronosticos = []

for _, row in df.iterrows():
    p_goles_L = prob_goles(row['goles_esperados_local'])
    p_goles_V = prob_goles(row['goles_esperados_visitante'])
    
    # Calcular probabilidades de matriz de resultados
    victoria_local = sum(p_goles_L[i] * sum(p_goles_V[:i]) for i in range(1, 6))
    empate = sum(p_goles_L[i] * p_goles_V[i] for i in range(6))
    victoria_visita = sum(p_goles_V[i] * sum(p_goles_L[:i]) for i in range(1, 6))
    
    total = victoria_local + empate + victoria_visita
    
    pronosticos.append({
        "date": row['fecha'],
        "home": row['local'],
        "away": row['visitante'],
        "p1": round((victoria_local / total) * 100),
        "pX": round((empate / total) * 100),
        "p2": round((victoria_visita / total) * 100)
    })

# Exportar a JSON
with open('pronosticos.json', 'w', encoding='utf-8') as f:
    json.dump(pronosticos, f, ensure_ascii=False, indent=4)

print("pronosticos.json generado con éxito.")
