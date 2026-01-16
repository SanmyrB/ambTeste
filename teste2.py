# ============================================================
# SIMULAÇÃO SAZONAL DE USINA SUCROENERGÉTICA – 240 INTERAÇÕES
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# 1. FUNÇÃO PARA GERAÇÃO SAZONAL
# ------------------------------------------------------------
def gerar_serie_sazonal(minimo, media, maximo, n=240, n_baixo=30):
    """
    Gera uma série sazonal:
    - Primeiras n_baixo iterações: abaixo da média
    - Miolo: média a acima da média
    - Últimas n_baixo iterações: abaixo da média
    """
    serie = np.zeros(n)

    serie[:n_baixo] = np.random.uniform(minimo, media, n_baixo)
    serie[n_baixo:n-n_baixo] = np.random.uniform(media, maximo, n - 2*n_baixo)
    serie[n-n_baixo:] = np.random.uniform(minimo, media, n_baixo)

    return serie


# ------------------------------------------------------------
# 2. GERAÇÃO DAS ENTRADAS DA USINA
# ------------------------------------------------------------
n_iter = 240

entradas = {
    "toneladaCana": 9507,
    "Umidade Bagaço (%)": gerar_serie_sazonal(50, 52.5, 55, n_iter),
    "Disponibilidade Industrial (%)": 100,
    "Disponibilidade Agrícola (%)": 100,
    "Disponibilidade Climática (%)": gerar_serie_sazonal(85, 97, 100, n_iter),
    "brix Caldo Primário (º)": gerar_serie_sazonal(14.25, 17.125, 20, n_iter),
    "pol Caldo Primário": gerar_serie_sazonal(11.25, 14.125, 17, n_iter),
    "Temperatura do Caldo Primário (ºC)": 27,
    "Vazão de Caldo Primário p/ Fábrica (m³/h)": 211,
    "Pureza do Caldo Decantado (%)": gerar_serie_sazonal(80.5, 82.75, 85, n_iter),
    "brix Lodo (º)": gerar_serie_sazonal(7.25,8.875,10.5, n_iter),
    "pol Filtrado": gerar_serie_sazonal(2.5,5.5,9.5, n_iter),
    "Pressão de Vapor na Fábrica (kgf/cm²)": 1.5,
    "Pol do Xarope": gerar_serie_sazonal(40.5, 48, 55.5, n_iter),
    "Área do Evaporador (m²)": 1000,
    "Brix do Mel Final (º)": gerar_serie_sazonal(65, 73, 81, n_iter),
    "Pureza do Mel Final (%)": gerar_serie_sazonal(53, 58.75, 64.5, n_iter),
    "Vazão de Bagaço para Caldeira 3 (ton/h)": gerar_serie_sazonal(30, 37.5, 45, n_iter),
    "Vazão de Bagaço para Caldeira 4 (ton/h)": gerar_serie_sazonal(30, 37.5, 45, n_iter)
}

df = pd.DataFrame(entradas)
df.index.name = "Iteracao"


# ------------------------------------------------------------
# 3. MODELO SIMPLIFICADO DA USINA
# ------------------------------------------------------------
def simular_usina(toneladaCana, Umidade_Bagaco, Disponibilidade_Industrial,
                  Disponibilidade_Agricola, Disponibilidade_Climatica,
                  brix_Caldo_Primario, pol_Caldo_Primario,
                  Temperatura_Caldo_Primario, Vazao_Caldo_Primario_fabrica
                  , Pureza_Caldo_Decantado, brix_Lodo, pol_Filtrado,
                  Pressao_Vapor_fabrica, Pol_do_Xarope, Area_do_Evaporador,
                  Brix_do_Mel_Final, Pureza_do_Mel_Final,
                  Vazao_Bagaco_Caldeira_3, Vazao_Bagaco_Caldeira_4):
    
    # Cálculo da Extração
    
    

    return acucar, etanol, energia


# ------------------------------------------------------------
# 4. EXECUÇÃO DA SIMULAÇÃO
# ------------------------------------------------------------
acucar, etanol, energia = [], [], []

# for _, linha in df.iterrows():
#    a, e, en = simular_usina(linha)
#    acucar.append(a)
#    etanol.append(e)
#    energia.append(en)

# df["acucar_t_h"] = acucar
# df["etanol_m3_h"] = etanol
# df["energia_MW"] = energia


# ------------------------------------------------------------
# 5. RESULTADOS ANUAIS ACUMULADOS
# ------------------------------------------------------------
# resumo_anual = {
#    "Açúcar total (t)": df["acucar_t_h"].sum(),
#    "Etanol total (m³)": df["etanol_m3_h"].sum(),
#    "Energia total (MWh)": df["energia_MW"].sum()
#}

# print("RESUMO ANUAL DA PRODUÇÃO")
#for k, v in resumo_anual.items():
#    print(f"{k}: {v:,.2f}")

print(entradas["Disponibilidade Climática (%)"])

plt.plot(entradas["Disponibilidade Climática (%)"])
plt.show()