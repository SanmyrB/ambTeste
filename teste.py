import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

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

def fermentacao(vazMosto, brixMosto, purzMosto, convert = 0.9):

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

def Coluna_MN(nome, vaz_in, fracEt_in, fracEt_Topo, fracEt_Liq, fracEt_Fundo, disponiagric, disponiClima, disponiIndust):

    # Balanço de Massa
    # S1 + S2 + S3 = S_in (1)
    # S1*X1 + S2*X2 + S3*X3 = S_in*X_in (2)

    #Isolando o S3 da equação A
    # S3 = S_in - S1 - S2 (3)

    # Substituindo (3) em (2)
    # S1*X1 + S2*X2 + (S_in - S1 - S2)*X3 = S_in*X_in (4)

    # Isolando S2 em (4)
    # S2 = (S_in*X_in - S_in*X3 - S1*(X1 - X3)) / (X2 - X3) (5)

    # Substituindo (5) em (3)
    # S3 = S_in - S1 - (S_in*X_in - S_in*X3 - S1*(X1 - X3)) / (X2 - X3) (6)

    # ============ Prâmetros Conhecidos ============

    # S_in = vaz_in
    # X_in = fracEt_in
    # X1 = fracEt_Topo
    # X2 = fracEt_Liq
    # X3 = fracEt_Fundo

    # Média
    def med (a):
        return sum(a)/len(a)
    
    # Disponibilidade
    disponibilidade = min(disponiagric/100, disponiClima/100, disponiIndust/100) * 24
    
    # Fração de Etanol nas Correntes
    fracTotal = fracEt_Topo + fracEt_Liq + fracEt_Fundo
    fracVapCalc = fracEt_Topo / fracTotal
    fracLiqCalc = fracEt_Liq / fracTotal
    fracFundoCalc = fracEt_Fundo / fracTotal

    if fracEt_Topo > 0 and fracEt_Liq > 0 and fracEt_Fundo > 0:
        # Parâmetros da primeira Equação 
        p1 = (vaz_in * fracEt_in - (vaz_in * fracFundoCalc))/(fracLiqCalc - fracFundoCalc)
        p2 = (fracVapCalc - fracFundoCalc)/(fracLiqCalc - fracFundoCalc)
    else:
        return "Erro: Fração de Etanol inválida."

    S1, S2, S3 = None, None, None

    S1_list, S2_list, S3_list = [], [], []

    p3 = p2 - 1
    p4 = vaz_in - p1

    for i in range(1, int(vaz_in)):
        S1 = i
        S2 = p1 - p2 * S1
        S3 = p3 * S1 + p4

        if S2 > 0 and S3 > 0:
            
            S1_list.append(S1)
            S2_list.append(S2)
            S3_list.append(S3)

            i += 0.5
        else:
            i += 0.5
            continue

    return {nome:
                {
                    "S1": round(med(S1_list), 2),
                    "S2": round(med(S2_list), 2),
                    "S3": round(med(S3_list), 2),
                    "Retorno de etanol total (m³/h)": round(med(S1_list)*fracEt_Topo + med(S2_list)*fracEt_Liq,2) if nome=="Coluna AA1" else round(med(S1_list)*fracEt_Topo,2),
                    "Etanol perdido (m³/h)": round(med(S3_list) * fracEt_Fundo,2) if nome=="Coluna AA1" else round(med(S2_list) * fracEt_Liq + med(S3_list) * fracEt_Fundo,2),
                    "Balanço verificado (m³/h)": round(med(S1_list) + med(S2_list) + med(S3_list),2) - vaz_in,
                    "Total Produzido (m³/h)": round(med(S1_list)*fracEt_Topo,2) * disponibilidade if nome=="Coluna B" else None
                }
            }

colunaAA1 = Coluna_MN("Coluna AA1", vazVinho_m3, concentEt,
                          fracEt_Topo=0.94, fracEt_Liq=0.05, fracEt_Fundo=0.01,
                          disponiagric=100, disponiClima=100, disponiIndust=100)

vazS1 = colunaAA1["Coluna AA1"]["S1"]
vazS2 = colunaAA1["Coluna AA1"]["S2"]
vazTotal_colB = vazS1 + vazS2
fracEt_in_colB = (vazS1 * 0.94 + vazS2 * 0.05) / (vazTotal_colB)

colunaB = Coluna_MN("Coluna B", vazTotal_colB, fracEt_in_colB,
                         fracEt_Topo=0.95, fracEt_Liq=0.04, fracEt_Fundo=0.01,
                         disponiagric=100, disponiClima=100, disponiIndust=100)

print(MistResult)
print(ferment)
print(colunaAA1)
print(colunaB)
print(colunaB["Coluna B"]["Total Produzido (m³/h)"])