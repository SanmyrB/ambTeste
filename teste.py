import numpy as np
from scipy.optimize import minimize

Bcaldo = 17.08
PolCaldo = 14.21
Bmel = 67.92
Melpurez = 58.92
mCaldo = 211.62 # m³/h
mMel = 22.24 # ton/h
mFiltrado = 30.06 # ton/h
Bfiltrado = 9.07
Polfiltrado = 6.2

def tanqMistura (PolCaldo, Bcaldo, Bmel, Melpurez, mCaldo, mMel, mFiltrado, Bfiltrado, polFiltrado):
    
    # Cálculos preliminares
    purzCaldo = PolCaldo / Bcaldo * 100
    MEcaldo = 0.000028 * Bcaldo**2 + 0.002951 * Bcaldo + 1.01037
    mCaldo_ton = mCaldo * MEcaldo
    
    # Cálculo do Brix do Mosto 
    vazTotal = mCaldo_ton + mMel + mFiltrado
    BMosto = ((mCaldo_ton * Bcaldo) + (mMel * Bmel) + (mFiltrado * Bfiltrado))/vazTotal
    
    # Avalia a necessidade de diluição
    if BMosto > 22:
        vazTotal = (vazTotal * BMosto) / 22
        agua = vazTotal - (mCaldo_ton + mMel)
        BMosto = 22
    else:
        agua = 0

    # Determinação da Pureza
    purzMosto = ((mCaldo_ton * Bcaldo * purzCaldo) + (mMel * Bmel * Melpurez) + (mFiltrado * Bfiltrado * (polFiltrado/Bfiltrado*100)))/(vazTotal*BMosto)

    return {"Tanque de Mistura": {
                "Pureza Caldo Primário": round(purzCaldo, 2),
                "Vazão do Mosto (ton/h)": round(vazTotal, 2),
                "Brix do Mosto (º)": round(BMosto, 2),
                "Pureza do Mosto (%)": round(purzMosto, 2),
                "Água para Diluição": round(agua, 2)
            }
        }

MistResult = tanqMistura(PolCaldo, Bcaldo,Bmel, Melpurez, mCaldo, 
                         mMel, mFiltrado, Bfiltrado, Polfiltrado)

vazMosto = MistResult["Tanque de Mistura"]["Vazão do Mosto (ton/h)"]
brixMosto = MistResult["Tanque de Mistura"]["Pureza do Mosto (%)"]
purzMosto = MistResult["Tanque de Mistura"]["Pureza do Mosto (%)"]

def fermentacao(vazMosto, brixMosto, purzMosto, convert = 0.8):

    # Vazão de Sacarose Disponível (kg/h)
    vazSac_kg = (vazMosto * brixMosto / 100 * purzMosto / 100) * 1000

    # C6H15O6 -> 2C2H5OH + 2CO2
    # Constantes esquiométricas
    mmSac = 0.180 # kg/mol
    mmEt = 0.04607 # kg/mol
    mmCO2 = 0.044 # kg/mol

    # Massa específica do Etanol
    meEt = 789 # kg/m³
    meH2O = 997 # kg/m³

    # Rendimento Teórico
    redmT = (2 * mmEt) / mmSac

    # Vazão de Sacarose (mol/h)
    vazSac_mol = vazSac_kg/mmSac
    
    # Vazão de Etanol (mol/h)
    vazEt_mol = vazSac_mol * redmT * convert

    # Vazão de Etanol (m³/h)
    vazEt_kg = vazEt_mol * mmEt
    vazEt_m3 = vazEt_kg / meEt

    # Vazão de CO2
    vazCO2_mol = vazSac_mol * ((2 * mmCO2)/mmSac) * convert
    vazCO2_kg = vazCO2_mol * mmCO2

    # Cálculo da Massa que permanece no líquido
    vazLiquid_kg = vazMosto * 1000 - vazCO2_kg
    vazNF_kg = vazLiquid_kg - vazEt_kg # NF: Não Fermentáveis = água + não fermentáveis
    vazNF_m3 = vazNF_kg / meH2O

    # Vazão de Saída da Dorna
    vazVinho_m3 = vazEt_m3 + vazNF_m3

    # Cálculo do ºGL e concentração de etanol
    GL = vazEt_m3 / vazNF_m3 * 100
    conctEt = vazEt_m3 / vazVinho_m3

    return {"Fermentação": {
                "Vazão de do Vinho Fermentado (m³/h)": round(vazVinho_m3, 2),
                "Vazão de Etanol Disponível (m³/h)": round(vazEt_m3, 2),
                "GL": round(GL, 2),
                "Concentração de Etanol": round(conctEt, 4)
            }
        }

ferment = fermentacao(vazMosto, brixMosto, purzMosto)

vazVinho_m3 = ferment["Fermentação"]["Vazão de do Vinho Fermentado (m³/h)"]
vazEt_m3 = ferment["Fermentação"]["Vazão de Etanol Disponível (m³/h)"]
concentEt = ferment["Fermentação"]["Concentração de Etanol"]

def Coluna_PNL (nome, vazVinho_m3, fracEt_in, fracEt_Topo, fracEt_Liq, fracEt_Fundo):

    x = np.array([fracEt_Topo, fracEt_Liq, fracEt_Fundo])

    def objetivo(Fs):
        F1, F2, F3 = Fs
        return x[1]*F2 + x[2]*F3 + 1e-4*(F1**2 + F2**2 + F3**2)

    # -----------------------------
    # Restrições de igualdade
    # -----------------------------
    def balanco_total(Fs):
        return Fs.sum() - vazVinho_m3

    def balanco_etanol(Fs):
        return np.dot(x, Fs) - vazVinho_m3 * fracEt_in

    constraints = [
        {"type": "eq", "fun": balanco_total},
        {"type": "eq", "fun": balanco_etanol}
    ]

    # -----------------------------
    # Limites
    # -----------------------------
    bounds = [(0, None)] * 3

    # -----------------------------
    # Chute inicial
    # -----------------------------
    x0 = np.array([10, 100, 157])

    # -----------------------------
    # Resolução
    # -----------------------------
    res = minimize(
        objetivo,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints
    )

    res.x = [float(x) for x in res.x]

    return {"nome": nome,
            "Vazão do Topo (m³/h)": round(res.x[0], 2),
            "Concentração do Topo": fracEt_Topo,
            "Vazão do Líquido Intermediário (m³/h)": round(res.x[1], 2),
            "Concentração do Líquido Intermediário": fracEt_Liq,
            "Vazão do Fundo (m³/h)": round(res.x[2], 2),
            "Concentração do Fundo": fracEt_Fundo,
            "Etanol perdido (m³/h)": round(float(objetivo(res.x)),2)
            }

colunaAA1 = Coluna_PNL("Coluna AA1", vazVinho_m3, concentEt,
                          fracEt_Topo=0.94, fracEt_Liq=0.05, fracEt_Fundo=0.01)

vazTopo_m3 = colunaAA1["Vazão do Topo (m³/h)"]
vazLiq_m3 = colunaAA1["Vazão do Líquido Intermediário (m³/h)"]

vazTotal = vazTopo_m3 + vazLiq_m3
concentTotal = (vazTopo_m3 * colunaAA1["Concentração do Topo"] + vazLiq_m3 * colunaAA1["Concentração do Líquido Intermediário"]) / vazTotal

colunaB = Coluna_PNL("Coluna B", vazTotal, concentTotal, fracEt_Topo=0.95, fracEt_Liq=0.04, fracEt_Fundo=0.01)

print(MistResult)
print(ferment)
print(colunaAA1)
print(colunaB)
print(colunaB["Vazão do Topo (m³/h)"] * 24)