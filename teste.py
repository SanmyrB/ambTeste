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
    vazDorna_m3 = vazEt_m3 + vazNF_m3

    # Cálculo do ºGL e concentração de etanol
    GL = vazEt_m3 / vazNF_m3 * 100
    conctEt = vazEt_m3 / vazDorna_m3 * 100

    return {"Fermentação": {
                "Vazão de Saída da Dorna (m³/h)": round(vazDorna_m3, 2),
                "Vazão de Etanol Disponível (m³/h)": round(vazEt_m3, 2),
                "GL": round(GL, 2),
                "Concentração de Etanol": round(conctEt, 2)
            }
        }

ferment = fermentacao(vazMosto, brixMosto, purzMosto)

vazDorna_m3 = ferment["Fermentação"]["Vazão de Saída da Dorna (m³/h)"]
vazEt_m3 = ferment["Fermentação"]["Vazão de Etanol Disponível (m³/h)"]
concentEt = ferment["Fermentação"]["Concentração de Etanol"]

def coluna_destilacao(
    nome,
    vazao_in,
    frac_in,
    frac_fundo,
    frac_vap=None,
    frac_liq=None
):
    """
    Balanço simplificado de uma coluna de destilação de etanol.
    """

    etanol_in = vazao_in * frac_in
    saidas = {}

    # Trata valores None
    frac_vap_calc = frac_vap if frac_vap is not None else 0.0
    frac_liq_calc = frac_liq if frac_liq is not None else 0.0

    total_frac_sum = frac_vap_calc + frac_liq_calc + frac_fundo
    if total_frac_sum == 0:
        return {"coluna": nome, "saidas": {}}

    # --- Saída Vapor ---
    if frac_vap is not None:
        etanol_vap = etanol_in * (frac_vap_calc / total_frac_sum)
        vapor_out = etanol_vap / frac_vap if frac_vap > 0 else 0.0

        saidas["Vapor_Out"] = vapor_out
        saidas["Etanol_Vapor"] = vapor_out * frac_vap
        saidas["Frac_Et_Vapor"] = (
            saidas["Etanol_Vapor"] / vapor_out if vapor_out > 0 else 0.0
        )

    # --- Saída Líquida ---
    if frac_liq is not None:
        etanol_liq_topo = etanol_in * (frac_liq_calc / total_frac_sum)
        liquido_out = etanol_liq_topo / frac_liq if frac_liq > 0 else 0.0

        saidas["Liquido_Out"] = liquido_out
        saidas["Etanol_Liquido"] = liquido_out * frac_liq
        saidas["Frac_Et_Liquido"] = (
            saidas["Etanol_Liquido"] / liquido_out if liquido_out > 0 else 0.0
        )

    # --- Saída Fundo ---
    etanol_fundo = etanol_in * (frac_fundo / total_frac_sum)
    fundo_out = etanol_fundo / frac_fundo if frac_fundo > 0 else 0.0

    saidas["Fundo_Out"] = fundo_out
    saidas["Etanol_Fundo"] = fundo_out * frac_fundo
    saidas["Frac_Et_Fundo"] = (
        saidas["Etanol_Fundo"] / fundo_out if fundo_out > 0 else 0.0
    )

    return {
        "coluna": nome,
        "saidas": saidas
    }

def sistema_destilacao_etanol_fundo(
    vazao_vinho,
    frac_vinho,
    frac_topo_aa1_vap,
    frac_topo_aa1_liq,
    frac_fundo_d,
    disponi_agric,
    disponi_clim,
    disponi_indust
):
    """
    Sistema de destilação com colunas AA1, D e B,
    considerando etanol no fundo da coluna D.
    """

    # Disponibilidade operacional
    disponi = min(disponi_clim, disponi_indust, disponi_agric) / 100
    disponi_h = disponi * 24

    # --- Coluna AA1 ---
    col_aa1 = coluna_destilacao(
        nome="AA1",
        vazao_in=vazao_vinho,
        frac_in=frac_vinho,
        frac_fundo=0.01,
        frac_vap=frac_topo_aa1_vap,
        frac_liq=frac_topo_aa1_liq
    )

    # --- Coluna D ---
    feed_d = col_aa1["saidas"].get("Liquido_Out", 0.0)
    frac_in_d = (
        col_aa1["saidas"]["Etanol_Liquido"] / feed_d if feed_d > 0 else 0.0
    )

    col_d = coluna_destilacao(
        nome="D",
        vazao_in=feed_d,
        frac_in=frac_in_d,
        frac_fundo=frac_fundo_d,
        frac_vap=None,
        frac_liq=0.05
    )

    # --- Coluna B ---
    feed_b = (
        col_aa1["saidas"].get("Vapor_Out", 0.0) +
        col_d["saidas"].get("Fundo_Out", 0.0)
    )

    etanol_feed_b = (
        col_aa1["saidas"].get("Etanol_Vapor", 0.0) +
        col_d["saidas"].get("Etanol_Fundo", 0.0)
    )

    frac_in_b = etanol_feed_b / feed_b if feed_b > 0 else 0.0

    col_b = coluna_destilacao(
        nome="B",
        vazao_in=feed_b,
        frac_in=frac_in_b,
        frac_fundo=0.01,
        frac_vap=None,
        frac_liq=0.95
    )

    # --- Resultados principais ---
    residuos_totais = (
        col_aa1["saidas"]["Fundo_Out"] +
        col_d["saidas"]["Fundo_Out"] +
        col_b["saidas"]["Fundo_Out"]
    )

    frac_et_residuos = (
        (
            col_aa1["saidas"]["Etanol_Fundo"] +
            col_d["saidas"]["Etanol_Fundo"] +
            col_b["saidas"]["Etanol_Fundo"]
        ) / residuos_totais
        if residuos_totais > 0 else 0.0
    )

    return {
        "Destilacao": {
            "Produto Final (ETANOL-2 Fundo D)": round(col_d["saidas"]["Etanol_Fundo"], 2),
            "Produto Final (ETHID B)": round(col_b["saidas"]["Etanol_Liquido"], 2),
            "Produto Final (ETHID B) diário":
                round(col_b["saidas"]["Etanol_Liquido"] * disponi_h, 2),
            "Resíduos Totais": round(residuos_totais, 2),
            "Frac Etanol Resíduos": round(frac_et_residuos, 4),
        }
    }

colunas = sistema_destilacao_etanol_fundo(vazDorna_m3, concentEt ,0.94, 0.05, 0.02, 100, 100, 100)

print(MistResult)
print(ferment)
print(colunas)
