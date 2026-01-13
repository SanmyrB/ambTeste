import numpy as np
import math as m
import pandas as pd
import csv
import os
from datetime import datetime
import streamlit as st
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import subprocess
import plotly.express as px
import ast
import plotly.graph_objects as go
import plotly.io as pio
from typing import List, Dict, Any
# Configuração global do Kaleido (sem warnings)

pio.defaults.default_format = "png"
pio.defaults.default_width = 1000
pio.defaults.default_height = 600
pio.defaults.default_scale = 2

def garantir_lista(val):
    """Converte valores vindos das simulações em lista de floats"""
    if isinstance(val, (list, tuple)):
        return [float(x) for x in val]

    if isinstance(val, str):
        try:
            return ast.literal_eval(val)  # tenta converter direto
        except:
            val = val.replace("[", "").replace("]", "").replace(",", " ")
            tokens = val.split()
            lista = []
            for t in tokens:
                t = re.sub(r"[^0-9eE\+\-\.]", "", t)  # remove lixo
                if t:
                    try:
                        lista.append(float(t))
                    except:
                        pass
            return lista

    return [float(val)]

def salvar_figura(fig, nome):
    """Tenta salvar como PNG, senão fallback para HTML"""
    try:
        caminho = f"{nome}.png"
        fig.write_image(caminho)
        return caminho
    except Exception as e:
        print("⚠️ Erro exportando PNG com kaleido, salvando como HTML:", e)
        caminho = f"{nome}.html"
        fig.write_html(caminho)
        return caminho

def gerar_slide_fabrica(dados_file, simulacao):

    dados = carregar_simulacao(dados_file, simulacao)
    frames = ""

    # === 1. Aquecedor ===
    y_temp = garantir_lista(dados['Aquecedor']['Lista de Temperaturas (ºC)'])
    x_temp = ['Inicial'] + [f'Aq {i}' for i in range(1, len(y_temp))]
    fig_temp_aq = go.Figure([go.Scatter(x=x_temp, y=y_temp, mode="lines+markers")])
    fig_temp_aq.update_layout(title="Temperatura dos Aquecedores (ºC)")
    graf_temp_aq = salvar_figura(fig_temp_aq, "grafico_temp_aq")

    y_perda = garantir_lista(dados['Aquecedor']['Lista de Perdas (kgf/cm²)'])
    x_perda = ['Inicial'] + [f'Aq {i}' for i in range(1, len(y_perda))]
    fig_perda_aq = go.Figure([go.Bar(x=x_perda, y=y_perda)])
    fig_perda_aq.update_layout(title="Perda de Carga dos Aquecedores (kgf/cm²)")
    graf_perda_aq = salvar_figura(fig_perda_aq, "grafico_perda_aq")

    frames += r"""
    \begin{frame}{Aquecedor}
    \begin{itemize}
        \item Velocidade: %.2f m/s
        \item Temperatura final: %.2f ºC
        \item Perda de carga final: %.2f kgf/cm²
        \item Calor trocado: %.2f kcal
    \end{itemize}
    \centering
    \includegraphics[width=0.45\textwidth]{%s}
    \includegraphics[width=0.45\textwidth]{%s}
    \end{frame}
    """ % (
        dados['Aquecedor']['Velocidade (m/s)'],
        y_temp[-1],
        y_perda[-1],
        dados['Aquecedor']['Calor trocado (kcal)'],
        graf_temp_aq,
        graf_perda_aq
    )

    # === 2. Trocador de Calor ===
    y_temp = garantir_lista(dados['Trocador de Calor']['Lista de Temperaturas (ºC)'])
    x_temp = ['Inicial'] + [f'Tr {i}' for i in range(1, len(y_temp))]
    fig_temp_tr = go.Figure([go.Scatter(x=x_temp, y=y_temp, mode="lines+markers")])
    fig_temp_tr.update_layout(title="Temperatura no Trocador de Calor (ºC)")
    graf_temp_tr = salvar_figura(fig_temp_tr, "grafico_temp_trocador")

    y_perda = garantir_lista(dados['Trocador de Calor']['Lista de Perdas (kgf/cm²)'])
    x_perda = ['Inicial'] + [f'Tr {i}' for i in range(1, len(y_perda))]
    fig_perda_tr = go.Figure([go.Bar(x=x_perda, y=y_perda)])
    fig_perda_tr.update_layout(title="Perda de Carga no Trocador de Calor (kgf/cm²)")
    graf_perda_tr = salvar_figura(fig_perda_tr, "grafico_perda_trocador")

    frames += r"""
    \begin{frame}{Trocador de Calor}
    \begin{itemize}
        \item Temperatura final: %.2f ºC
        \item Perda final: %.2f kgf/cm²
        \item Velocidade: %.2f m/s
        \item Calor trocado: %.2f kcal
    \end{itemize}
    \centering
    \includegraphics[width=0.45\textwidth]{%s}
    \includegraphics[width=0.45\textwidth]{%s}
    \end{frame}
    """ % (
        y_temp[-1],
        y_perda[-1],
        dados['Trocador de Calor']['Velocidade (m/s)'],
        dados['Trocador de Calor']['Calor trocado (kcal)'],
        graf_temp_tr,
        graf_perda_tr
    )

    # === 3. Decantador ===
    frames += r"""
    \begin{frame}{Decantador}
    \begin{itemize}
        \item Vazão de Lodo: %.2f ton/h
        \item Vazão de Caldo na Saída: %.2f ton/h
        \item Brix do Caldo: %.2f º
        \item Pureza do Caldo: %.2f %%
    \end{itemize}
    \end{frame}
    """ % (
        dados['Decantador']['Vazão de Lodo (ton/h)'],
        dados['Decantador']['Vazão de Caldo na Saída do Decantador (ton/h)'],
        dados['Decantador']['Brix do Caldo na Saída do Decantador (º)'],
        dados['Decantador']['Pureza do Caldo na Saída do Decantador (%)']
    )

    # === 4. Evaporadores ===
    y_brix = garantir_lista(dados['Evaporadores']['Lista dos Brix do Caldo (º)'])
    x_brix = [f'Ev {i}' for i in range(1, len(y_brix) + 1)]
    fig_brix_ev = go.Figure([go.Scatter(x=x_brix, y=y_brix, mode="lines+markers")])
    fig_brix_ev.update_layout(title="Brix nos Evaporadores (º)")
    graf_brix_ev = salvar_figura(fig_brix_ev, "grafico_brix_evaporadores")

    frames += r"""
    \begin{frame}{Evaporadores}
    \begin{itemize}
        \item Brix final: %.2f º
        \item Vazão final de Caldo: %.2f m³/h
        \item Queda de Pressão Total: %.2f kgf/cm²
    \end{itemize}
    \centering
    \includegraphics[width=0.6\textwidth]{%s}
    \end{frame}
    """ % (
        y_brix[-1],
        dados['Evaporadores']['Vazão final de Caldo (m³/h)'],
        dados['Evaporadores']['Queda de Pressão Total (kgf/cm²)'],
        graf_brix_ev
    )

    # === 5. Filtro Prensa ===
    frames += r"""
    \begin{frame}{Filtro Prensa}
    \begin{itemize}
        \item Vazão de Filtrado: %.2f m³/h
        \item Brix do Filtrado: %.2f º
        \item Massa da Torta: %.2f ton/h
    \end{itemize}
    \end{frame}
    """ % (
        dados['Filtro Prensa']['Vazão de Filtrado (m³/h)'],
        dados['Filtro Prensa']['Brix do Filtrado (º)'],
        dados['Filtro Prensa']['Massa da Torta (ton/h)']
    )

    # === 6. Peneira Rotativa ===
    frames += r"""
    \begin{frame}{Peneira Rotativa}
    \begin{itemize}
        \item Vazão de Caldo: %.2f ton/h
        \item Vazão de Caldo (m³/h): %.2f m³/h
        \item Brix de Saída: %.2f º
    \end{itemize}
    \end{frame}
    """ % (
        dados['Peneira Rotativa']['Vazão de Caldo na Saída da Peneira Rotativa (ton/h)'],
        dados['Peneira Rotativa']['Vazão de Caldo na Saída da Peneira Rotativa (m³/h)'],
        dados['Peneira Rotativa']['Brix de Saída da Peneira Rotativa (º)']
    )

    # === Montagem do LaTeX ===
    with open("slide_padrao.tex", "r", encoding="utf-8") as f:
        tex = f.read()

    tex = tex.replace("%%TITULO%%", f"Simulação - Fábrica")
    tex = tex.replace("%%CONTEUDO%%", frames)

    tex_file = "apresentacao_fabrica.tex"
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(tex)

    subprocess.run(["pdflatex", tex_file], check=True)

    return "apresentacao_fabrica.pdf"

def gerar_pdf(csv_path, area, simulacao):

    output_file = f"Relatorio_Simulacao_{area}_{simulacao}.pdf"

    df = pd.read_csv(csv_path)
    df_filtrado = df[(df["Área"] == area) & (df["Simulação"] == simulacao)]
    if df_filtrado.empty:
        return None

    doc = SimpleDocTemplate(output_file, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Criar estilo menor para tabela
    small_style = ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=10
    )

    # Título e cabeçalho
    title = Paragraph(f"Relatório da Simulação: {simulacao}", styles['Title'])
    elements.append(title)
    data_sim = df_filtrado['Data'].iloc[0]
    header_info = Paragraph(f"Área: {area} &nbsp;&nbsp;&nbsp; Data: {data_sim}", styles['Normal'])
    elements.append(header_info)
    elements.append(Spacer(1, 8))

    # Estrutura da tabela
    table_data = [["Variável", "Valor"]]
    ultimo_dic = None

    for _, row in df_filtrado.iterrows():
        valor = row['Valor']
        # Quebrar listas em várias linhas
        if isinstance(valor, str) and valor.startswith("[") and valor.endswith("]"):
            lista = [v.strip() for v in valor.strip("[]").replace("\n", "").split(",")]
            valor = Paragraph("<br/>".join(lista), small_style)
        else:
            valor = Paragraph(str(valor), small_style)

        # Se mudou o dicionário, insere subtítulo
        if row['Dicionário'] != ultimo_dic:
            table_data.append([Paragraph(f"<b>{row['Dicionário']}</b>", styles['Normal']), ""])
            ultimo_dic = row['Dicionário']

        # Linha normal (sem repetir o dicionário)
        table_data.append([Paragraph(row['Variável'], small_style), valor])

    # Ajustar larguras
    page_width = A4[0]
    col_widths = [0.45 * page_width, 0.45 * page_width]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Estilo
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#d9d9d9")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.black),
        ('ALIGN',(0,0),(-1,0),'CENTER'),
        ('ALIGN',(0,1),(-1,-1),'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ])

    # Linhas alternadas (listras)
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0,i), (-1,i), colors.whitesmoke)

    table.setStyle(table_style)
    elements.append(table)

    doc.build(elements)
    return output_file

def alinhar_listas(labels, lista1, lista2):
    """
    Ajusta labels, lista1 e lista2 para terem o mesmo tamanho.
    Sempre corta para o menor comprimento encontrado.
    """
    min_len = min(len(labels), len(lista1), len(lista2))
    return labels[:min_len], lista1[:min_len], lista2[:min_len]

def str_to_float_list(s):
    # Remove colchetes
    s = s.strip().replace('[', '').replace(']', '')
    # Substitui múltiplos espaços por um único espaço
    s = re.sub(r'\s+', ' ', s)
    # Substitui ponto entre números decimais (ex: 32.06) por único separador de float
    # Encontrar padrões de números com ponto decimal
    numbers = re.findall(r'\d+\.\d+', s)
    return [float(num) for num in numbers]

def converter_json_listas(d):
    """
    Converte recursivamente listas e dicionários,
    garantindo que strings numéricas sejam floats.
    """
    if isinstance(d, dict):
        return {k: converter_json_listas(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [converter_json_listas(v) for v in d]
    elif isinstance(d, str):
        try:
            return float(d)
        except ValueError:
            return d
    else:
        return d


def carregar_simulacao(arquivo_csv, nome_simulacao):
    """
    Carrega dados de simulação CSV e retorna dicionário estruturado por etapa e variável.
    Converte strings de listas no formato Python em listas de floats.
    """
    df = pd.read_csv(arquivo_csv)

    # Filtra simulação
    df_filtrado = df[df["simulacao"] == nome_simulacao]
    resultado = {}

    for _, row in df_filtrado.iterrows():
        etapa, variavel, valor_raw = row["dicionario"], row["variavel"], str(row["valor"]).strip()

        # Detecta listas no formato Python "[...]" e converte
        if valor_raw.startswith('[') and valor_raw.endswith(']'):
            lista = valor_raw[1:-1].split(',')
            valor = [float(v.strip()) for v in lista]
        else:
            try:
                valor = float(valor_raw)
            except ValueError:
                valor = valor_raw

        resultado.setdefault(etapa, {})[variavel] = valor

    return resultado

def salvar_dados_csv(arquivo_csv, lista_dicionarios, nome_simulacao, nivel):
    """
    Salva uma lista de dicionários em CSV.
    Valores numéricos e listas são convertidos para formato Python padrão.
    """
    linhas = []
    data_atual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    for dicionario in lista_dicionarios:
        for equipamento, variaveis in dicionario.items():
            for variavel, valor in variaveis.items():
                # Se for lista, converte para string no formato Python com vírgulas
                if isinstance(valor, list):
                    valor_str = '[' + ', '.join([str(float(v)) for v in valor]) + ']'
                # Se for número isolado
                elif isinstance(valor, (int, float)):
                    valor_str = str(float(valor))
                # Se for string
                else:
                    valor_str = str(valor)

                linhas.append({
                    'area': nivel,
                    'simulacao': nome_simulacao,
                    'data': data_atual,
                    'dicionario': equipamento,
                    'variavel': variavel,
                    'valor': valor_str
                })

    df = pd.DataFrame(linhas)

    # Salva CSV
    if os.path.exists(arquivo_csv):
        df.to_csv(arquivo_csv, mode='a', header=False, index=False)
    else:
        df.to_csv(arquivo_csv, mode='w', header=True, index=False)

def comparar_simulacoes(dados1, dados2, nome1, nome2):
    def flatten(dados):
        flat = {}
        for etapa, variaveis in dados.items():
            for var, val in variaveis.items():
                flat[f"{etapa} - {var}"] = val
        return flat

    df1 = pd.DataFrame.from_dict(flatten(dados1), orient="index", columns=[nome1])
    df2 = pd.DataFrame.from_dict(flatten(dados2), orient="index", columns=[nome2])
    df = pd.concat([df1, df2], axis=1)

    # Apenas para valores numéricos, calcula diferença %
    df["Diferença (%)"] = None
    for i in df.index:
        try:
            v1, v2 = float(df.loc[i, nome1]), float(df.loc[i, nome2])
            df.loc[i, "Diferença (%)"] = ((v2 - v1) / v1) * 100
        except:
            pass
    return df

def Filtra_area(file_path, area):
    try:
        df = pd.read_csv(file_path)
        df.columns = ["Área", "Simulacao", "Data", "Etapa", "Variavel", "Valor"]

        df_filtrado = df[df["Área"] == area]

        return df_filtrado
    except Exception as e:
        st.warning(f'Erro ao filtrar o arquivo: {e}')

def Lista_Simulacao(df_filtrado, coluna= 1):
    """
    Lê um arquivo CSV e retorna os valores únicos da primeira coluna.

    Args:
        file_path (str): O caminho para o arquivo CSV.

    Returns:
        pandas.Series: Uma série do pandas contendo os valores únicos da primeira coluna.
                      Retorna None se o arquivo não for encontrado ou estiver vazio.
    """
    if df_filtrado is None or df_filtrado.empty:
        print("⚠️ Aviso: DataFrame vazio.")
        return pd.Series([], dtype="object")

    if coluna >= len(df_filtrado.columns):
        print(f"⚠️ Aviso: O DataFrame não tem a coluna de índice {coluna}.")
        return pd.Series([], dtype="object")

    col_name = df_filtrado.columns[coluna]
    unique_values = df_filtrado[col_name].dropna().unique()

    return pd.Series(unique_values)

def exporta_equipamentos_para_excel(caminho_csv, caminho_excel):
    df = pd.read_csv(caminho_csv)
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

    # Use o nome correto da coluna do CSV: 'Dicionário'
    grupos = list(df.groupby('Dicionário'))
    if not grupos:
        raise ValueError('Nenhum dado encontrado para exportar. Verifique o arquivo CSV.')

    with pd.ExcelWriter(caminho_excel, engine='openpyxl') as writer:
        for equipamento, grupo in grupos:
            grupo.to_excel(writer, sheet_name=str(equipamento)[:31], index=False)

def dividir_lista_por_mil(lista_original): #Transforma todas as vazões em ton/h
                            
    if not isinstance(lista_original, list):
        raise TypeError('A entrada deve ser uma lista.')

    lista_dividida_e_formatada = [round(item / 1000, 2) for item in lista_original]
    
    return lista_dividida_e_formatada

def arredonda_lista(lista_original):
    '''
    Arredonda os valores de uma lista para duas casas decimais.

    Args:
        lista_original (list): Uma lista de números.

    Returns:
        list: Uma nova lista com os valores arredondados.
    '''
    if not isinstance(lista_original, list):
        raise TypeError('A entrada deve ser uma lista.')
    lista_dividida_e_formatada = [round(item, 2) for item in lista_original]
    return lista_dividida_e_formatada

def m_c_a_para_kgf(lista_original):
    '''
    Converte metros de coluna de água (m.c.a) para kgf/cm².

    Args:
        lista_original (list): Uma lista de valores em m.c.a.

    Returns:
        list: Uma nova lista com os valores convertidos para kgf/cm².
    '''
    if not isinstance(lista_original, list):
        raise TypeError('A entrada deve ser uma lista.')
    lista_kgf = [item * 0.01 for item in lista_original]
    return lista_kgf

def bar_para_kgf(lista_original):
    '''
    Converte bar para kgf/cm².

    Args:
        lista_original (list): Uma lista de valores em bar.

    Returns:
        list: Uma nova lista com os valores convertidos para kgf/cm².
    '''
    if not isinstance(lista_original, list):
        raise TypeError('A entrada deve ser uma lista.')
    lista_kgf = [item * 1.01972 for item in lista_original]
    return lista_kgf

def calcular_moenda(ton_cana_dia, disponi_agric, disponi_clim, disponi_indust, extra_terno,
                    embebi_fibra, umid_bag, brix_prim, pol_prim, fibra_cana):
    '''
    Calcula as vazões e purezas dos caldos na seção de moenda.

    Args:
        ton_cana_dia (float): Tonelada de Cana no dia.
        disponi_agric (float): Disponibilidade Agrícola (%).
        disponi_clim (float): Disponibilidade Climática (%).
        disponi_indust (float): Disponibilidade da Indústria (%).
        extra_terno (float): Extração do Primeiro Terno (%).
        embebi_fibra (float): Embebição (% da Fibra).
        umid_bag (float): Umidade do Bagaço (%).
        brix_1 (float): Brix do Caldo Primário (º).
        pol_1 (float): Pol do Caldo Primário (º).
        fibra_cana (float): Fibra da Cana (%).
        brix_sec (float): Brix do Caldo Secundário (º).
        pol_sec (float): Pol do Caldo Secundário (º).
        vaz_fab (float): Vazão de Caldo para a Fábrica (m³/h).
        vaz_dest (float): Vazão de Caldo para a Destilaria (m³/h)

    Returns:
        dict: Um dicionário com todos os resultados calculados, incluindo vazões e purezas.
    '''
    disponi_list = [disponi_clim, disponi_indust, disponi_agric]
    disponi = min(disponi_list)
    disponi_h = disponi * 24
    tch = ton_cana_dia / (24 * disponi)
    
    vaz_fibra = tch * fibra_cana
    vaz_embeb = vaz_fibra * embebi_fibra
    vaz_bagac = vaz_fibra / umid_bag

    # Cálculos Caldo 1º Terno
    vaz_caldo_1 = tch * extra_terno

    # Cálculos Caldo 2-6º Terno
    vaz_caldo_26 = tch + vaz_embeb - vaz_caldo_1 - vaz_bagac

    # Cálculos Caldo Primário
    vaz_caldo_prim = vaz_caldo_1 + vaz_caldo_26
    purez_prim = (pol_prim / brix_prim) * 100
    dens_prim = ((0.000028 * brix_prim ** 2) + (0.002951 * brix_prim + 1.01037))
    vaz_caldo_prim_m = vaz_caldo_prim * dens_prim

    resultados = {
        'Extração': {
            'Tonelada de Cana por hora': round(tch,2),
            'Disponibilidade Geral (h)': round(disponi_h,2),
            'Vazão de Bagaço (ton/h)': round(vaz_bagac,2),
            'Vazão de Caldo Primário (ton/h)': round(vaz_caldo_prim,2),
            'Vazão de Caldo Primário (m³/h)': round(vaz_caldo_prim_m,2),
            'Pureza do Caldo Primário (%)': round(purez_prim,2),
            'Densidade do Caldo Primário': round(dens_prim,2),
            'Vazão de Embebição (m³/h)': round(vaz_embeb,2)
        }
    }

    return resultados

def calcular_aquecimento(nome, num_equip, temp_entrada, temp_aque, dint, quant_passe, tubos, comp_tubo, brix, vaz_entrada):
    '''
    Calcula as temperaturas e perdas de carga em aquecedores ou trocadores de calor.

    Args:
        nome (str): Nome do equipamento ('Aquecedor' ou 'Trocador de Calor').
        num_equip (int): Número de equipamentos.
        temp_entrada (float): Temperatura de entrada do fluido (ºC).
        temp_aque (float): Temperatura do fluido de aquecimento (ºC).
        dint (float): Diâmetro interno do tubo (m).
        quant_passe (int): Quantidade inicial de passes.
        tubos (int): Número de tubos.
        comp_tubo (float): Comprimento do tubo (m).
        brix (float): Brix do caldo (º).
        vaz_entrada (float): Vazão de caldo (ton/h).

    Returns:
        tuple: Uma tupla contendo as listas de temperaturas, perdas de carga, velocidade e a vazão de aquecimento total.
    '''
    valor_pi = m.pi
    cp = 1 - 0.006 * brix
    dens = ((0.000028 * brix ** 2) + (0.002951 * brix) + 1.01037) * 1000

    area = (valor_pi * (dint ** 2) / 4) * tubos
    vaz_entrada_kg = vaz_entrada * 1000
    vaz_entrada_m3_s = (vaz_entrada_kg / 3600) / dens

    sai = valor_pi * dint * tubos * quant_passe * comp_tubo
    temperaturas = [temp_entrada]
    perdas = [0]
    vel = vaz_entrada_m3_s / area

    quant_passes_equip = quant_passe
    for _ in range(num_equip):
        coef = temp_aque * (5 + vel)
        expoente = (-coef * sai) / (vaz_entrada_kg * cp)
        temp_said = temp_aque - (temp_aque - temperaturas[-1]) * m.pow(2.81, expoente)
        temperaturas.append(temp_said)

        perda = (0.0025 * (vel ** 2) * quant_passes_equip * (comp_tubo + 1)) / dint
        perdas.append(perda)
        quant_passes_equip += 2 if nome == 'Aquecedor' else 6
    
    denominador_q = ((607 - 0.7 * temp_aque) / 0.95)
    q = (vaz_entrada_kg * cp * (temperaturas[-1] - temp_entrada) / denominador_q) / 1000

    temperaturas = arredonda_lista(temperaturas)
    perdas = m_c_a_para_kgf(arredonda_lista(perdas))
    
    resultados = {
        f'{nome}': {
            'Lista de Temperaturas (ºC)': temperaturas,
            'Lista de Perdas (kgf/cm²)': perdas,
            'Velocidade (m/s)': vel,
            'Calor trocado (kcal)': q
        }
    }

    return resultados

def calcular_sulfitacao(vaz_entrada, s_tonc=225, mm_s=32.065, mm_oxig=32):
    '''
    Calcula a demanda de Enxofre e Oxigênio para a Sulfitação.

    Args:
        vaz_entrada (float): Vazão para a fábrica em ton/h.
        s_tonc (float): Gramas de Enxofre por tonelada de cana.
        mm_s (float): Massa molar do Enxofre (g/mol).
        mm_oxig (float): Massa molar do Oxigênio (g/mol).
        vaz_s_kg = Vazão de Enxofre necessário (kg/h)
        vaz_oxig_kg = Vazão de Oxigênio necessário (kg/h)

    Returns:
        tuple: Vazão de Enxofre e Vazão de Oxigênio em kg/h.
    '''
    vaz_s_g = vaz_entrada * s_tonc # g/h
    vaz_s_mol = vaz_s_g / mm_s
    vaz_oxig_mol = vaz_s_mol
    vaz_oxig_g = vaz_oxig_mol * mm_oxig
    
    vaz_s_kg = vaz_s_g / 1000
    vaz_oxig_kg = vaz_oxig_g / 1000

    resultados = {
        'Sulfitação': {
            'Vazão de Enxofre (kg/h)': vaz_s_kg,
            'Vazão de Oxigênio': vaz_oxig_kg
        }
    }
    
    return resultados

def calcular_caleacao(vaz_entrada, cal_tonc=650, mm_ca=100, mm_h2o=18):
    '''
    Calcula a demanda de Cal e Água para a Caleação.

    Args:
        vaz_entrada (float): Vazão para a fábrica em ton/h.
        cal_tonc (float): Gramas de Cal por tonelada de cana.
        mm_ca (float): Massa molar do Cal (g/mol).
        mm_h2o (float): Massa molar da Água (g/mol).
        vaz_cal_kg = Vazão de Enxofre necessário (kg/h)
        vaz_h2o_kg = Vazão de Oxigênio necessário (kg/h)

    Returns:
        tuple: Vazão de Cal e Vazão de Água em kg/h.
    '''
    vaz_cal_g = vaz_entrada * cal_tonc
    vaz_cal_mol = vaz_cal_g / mm_ca
    vaz_h2o_mol = vaz_cal_mol / 4
    vaz_h2o_g = vaz_h2o_mol * mm_h2o
    
    vaz_cal_kg = vaz_cal_g / 1000
    vaz_h2o_kg = vaz_h2o_g / 1000

    resultados = {
        'Caleação': {
            'Vazão de Cal (kg/h)': vaz_cal_kg,
            'Vazão de Água (kg/h)': vaz_h2o_kg
        }
    }
    
    return resultados

def calcular_balao_flash(vaz_entrada, brix_misto, temp_tc, temp_said_balao_flash):
    '''
    Calcula a quantidade de água perdida no Flasheamento, vazão e brix de saída do equipamento.

    Args:
        vaz_entrada (float): Vazão de caldo na entrada do balão flash (ton/h).
        brix_misto (float): Brix do caldo misto na entrada do balão flash (º).
        temp_tc (float): Temperatura do caldo misto na entrada do balão flash (ºC).
        temp_said_balao_flash (float): Temperatura de saída do caldo do balão flash (ºC).

    Returns:
        tuple: Uma tupla contendo a vazão de caldo na saída (ton/h), o Brix do caldo de saída (º) e a vazão volumétrica de saída (m³/h).
    '''

    Cp = 1 - 0.006 * brix_misto
    denom_agua_evap = (607 - (0.7 * (temp_tc - temp_said_balao_flash)))
    agua_evap_bflash = vaz_entrada * Cp *(((temp_tc - temp_said_balao_flash) / denom_agua_evap))
    vaz_saida = vaz_entrada - agua_evap_bflash
    brix_flash = (brix_misto * vaz_entrada) / vaz_saida
    dens_flash = ((0.000028 * brix_flash ** 2) + (0.002951 * brix_flash) + 1.01037)
    vaz_saida_m = vaz_saida / dens_flash

    resultados ={
        'Balão Flash': {
            'Vazão de Saída do Balão Flash (ton/h)': vaz_saida,
            'Vazão de Saída do Balão Flash (m³/h)': vaz_saida_m,
            'Brix de Saída do Balão Flash (º)': brix_flash
        }
    }

    return resultados

def calcular_filtro_rotativo(vaz_entrada, brix_entrada):
    '''
    Calcula a nova vazão e brix após passar pelo filtro rotativo.

    Args:
        vaz_entrada (float): Vazão de caldo na entrada do filtro rotativo (ton/h).
        brix_flash (float): Brix do caldo na entrada do filtro rotativo (º).
        reten_fr (float): Retenção do filtro rotativo (%).

    Returns:
        tuple: Uma tupla contendo a vazão de caldo de saída (ton/h), o Brix do caldo de saída (º) e a vazão volumétrica de saída (m³/h).
    '''
    vaz_saida_fr = vaz_entrada
    brix_fr = (brix_entrada * vaz_entrada) / vaz_saida_fr
    dens_fr = ((0.000028 * brix_fr ** 2) + (0.002951 * brix_fr) + 1.01037)
    vaz_fr_m = vaz_saida_fr / dens_fr

    resultados = {
        'Filtro Rotativo': {
            'Vazão de Saída do Filtro Rotativo (ton/h)': vaz_saida_fr,
            'Vazão de Saída do Filtro Rotativo (m³/h)': vaz_fr_m,
            'Brix de Saída do Filtro Rotativo (º)': brix_fr
        }
    }

    return resultados

def calcular_decantador(vaz_entrada, brix_fr, reten_decant, brix_lodo, pol_decant):
    '''
    Calcula as vazões de lodo gerado, brix, pureza e vazão de saída do equipamento.

    Args:
        vaz_entrada (float): Vazão de caldo na entrada do decantador (ton/h).
        brix_fr (float): Brix do caldo na entrada do decantador (º).
        reten_decant (float): Retenção do decantador (%).
        brix_lodo (float): Brix do lodo (º).
        pol_decant (float): Pol do caldo na saída do decantador (º).

    Returns:
        tuple: Uma tupla contendo a vazão de lodo (ton/h), vazão de caldo de saída (ton/h), Brix do caldo de saída (º), pureza do caldo de saída (%) e vazão volumétrica de saída (m³/h).
    '''
    vaz_lodo = vaz_entrada * reten_decant
    vaz_caldo_decant = vaz_entrada - vaz_lodo
    brix_decant = ((brix_fr * vaz_entrada) - (brix_lodo * vaz_lodo)) / vaz_caldo_decant
    purez_decant = (pol_decant / brix_decant) * 100
    dens_decant = ((0.000028 * brix_decant ** 2) + (0.002951 * brix_decant) + 1.01037)
    vaz_decant_m = vaz_caldo_decant / dens_decant

    resultados = {
        'Decantador': {
            'Vazão de Lodo (ton/h)': vaz_lodo,
            'Vazão de Caldo na Saída do Decantador (ton/h)': vaz_caldo_decant,
            'Vazão de Caldo na Saída do Decantador (m³/h)': vaz_decant_m,
            'Brix do Caldo na Saída do Decantador (º)': brix_decant,
            'Pureza do Caldo na Saída do Decantador (%)': purez_decant
        }
    }

    return resultados

def calcular_filtro_prensa(mass_flow_tph, Ss_kg_m3, B_feed_degBx, xc=0.30):
    '''
    Calcula os parâmetros de saída do Filtro Prensa.

    Args:
        mass_flow_tph (float): Vazão de massa de alimentação (ton/h).
        Ss_kg_m3 (float): Sólidos em suspensão na alimentação (kg/m³).
        B_feed_degBx (float): Brix da alimentação (º).
        xc (float): Fração sólida na torta (%).

    Returns:
        tuple: Uma tupla contendo a vazão volumétrica de filtrado (m³/h), o Brix do filtrado (º) e a vazão de torta (ton/h), ou None em caso de erro.
    '''
    M_feed = mass_flow_tph * 1000.0
    rho_feed = ((0.000028 * B_feed_degBx ** 2) + (0.002951 * B_feed_degBx) + 1.01037) * 1000
    V_feed = M_feed / rho_feed
    M_susp = Ss_kg_m3 * V_feed
    M_liquid = M_feed - M_susp
    if M_liquid <= 0:
        return None, 'Massa líquida negativa ou zero: reveja sólidos em suspensão ou vazão.'
    M_diss = (B_feed_degBx / 100.0) * M_liquid
    M_cake = M_susp / xc
    V_cake = M_cake / 1000.0
    M_filtrado = M_feed - M_cake
    if M_filtrado <= 0:
        return None, 'Massa filtrada <= 0: reveja fração sólida na torta ou sólidos suspensos.'
    B_filtrado = 100.0 * M_diss / M_filtrado
    rho_filtrado = ((0.000028 * B_filtrado ** 2) + (0.002951 * B_filtrado) + 1.01037) * 1000
    V_filtrado = M_filtrado / rho_filtrado
    M_torta_tph = M_cake / 1000.0

    resultados = {
        'Filtro Prensa': {
            'Vazão de Filtrado (m³/h)': V_filtrado,
            'Brix do Filtrado (º)': B_filtrado,
            'Massa da Torta (ton/h)': M_torta_tph
        }
    }

    return resultados

def calcular_peneira_rotativa(vaz_caldo_decant, brix_decant):
    '''
    Calcula os parâmetros de saída da Peneira Rotativa.

    Args:
        vaz_caldo_decant (float): Vazão de caldo na entrada da peneira rotativa (ton/h).
        brix_decant (float): Brix do caldo na entrada da peneira rotativa (º).
        reten_pr (float): Retenção da peneira rotativa (%).

    Returns:
        tuple: Uma tupla contendo a vazão de caldo de saída (ton/h), o Brix do caldo de saída (º) e a vazão volumétrica de saída (m³/h).
    '''
    vaz_caldo_pr = vaz_caldo_decant
    brix_pr = (brix_decant * vaz_caldo_decant) / vaz_caldo_pr
    dens_pr = ((0.000028 * brix_pr ** 2) + (0.002951 * brix_pr) + 1.01037)
    vaz_pr_m = vaz_caldo_pr / dens_pr

    resultados = {
        'Peneira Rotativa': {
            'Vazão de Caldo na Saída da Peneira Rotativa (ton/h)': vaz_caldo_pr,
            'Vazão de Caldo na Saída da Peneira Rotativa (m³/h)': vaz_pr_m,
            'Brix de Saída da Peneira Rotativa (º)': brix_pr
        }
    }
    
    return resultados
    
df_press_abs = pd.DataFrame({
                        'Pressão Absoluta (bar)': [
                            0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08,
                            0.09, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60,
                            0.70, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30, 1.40,
                            1.50, 1.60, 1.80, 2.00, 2.20, 2.40, 2.60, 2.80, 3.00
                        ],
                        'Temperatura (°C)': [
                            6.7, 17.2, 23.8, 28.6, 32.5, 35.8, 38.9, 41.2,
                            43.9, 45.4, 53.6, 59.7, 68.7, 75.9, 81.3, 86.0,
                            90.0, 93.5, 96.6, 99.6, 101.8, 104.8, 107.5, 109.9,
                            112.0, 114.0, 117.6, 120.9, 124.0, 126.8, 129.5, 131.9, 134.2
                        ],
                        'Entalpia do Vapor (kcal/kg)': [
                            600.1, 604.8, 607.7, 609.8, 611.5, 612.9, 613.9, 615.1,
                            616.1, 617.0, 620.5, 623.1, 626.8, 629.4, 631.3, 632.9,
                            634.2, 635.3, 636.3, 637.2, 638.0, 638.7, 639.4, 640.0,
                            640.6, 641.1, 642.1, 643.0, 643.8, 644.5, 645.1, 645.7, 646.2
                        ],
                        'Calor Latente (kcal/kg)': [
                            593.0, 587.4, 583.9, 581.1, 578.9, 577.1, 575.0, 574.1,
                            572.9, 571.6, 567.0, 563.5, 558.2, 553.7, 550.2, 547.0,
                            544.1, 541.6, 539.3, 537.1, 535.4, 533.1, 531.0, 529.1,
                            527.3, 525.6, 522.4, 519.5, 516.7, 514.1, 511.7, 509.4, 507.2
                        ]
                    })

def arrumar_lista(lista):
    return np.round(lista, 2).tolist()

def calcular_pressao_temp(seq, press_inicial, key_inicial, key_final, P_ref, T_ref, H_ref, L_ref):
    frac_queda = (key_inicial - key_final) / (seq - 1)
    queda_rel = [0] + (key_inicial - np.arange(seq) * frac_queda) / (10 * seq)
    queda_total = round((press_inicial - queda_rel[-1]) * 1.01972, 2)
    queda_entre = np.array(queda_rel) * queda_total

    press_efeitos = np.zeros(seq + 1)
    press_efeitos[0] = press_inicial
    for i in range(seq):
        press_efeitos[i + 1] = press_efeitos[i] - queda_entre[i]

    df = pd.DataFrame({
        'Efeito': np.arange(1, seq + 2),
        'Pressão (bar)': np.round(press_efeitos, 3),
        'Temperatura (°C)': np.round(np.interp(press_efeitos, P_ref, T_ref), 2),
        'Entalpia (kcal/kg)': np.round(np.interp(press_efeitos, P_ref, H_ref), 2),
        'Calor Latente (kcal/kg)': np.round(np.interp(press_efeitos, P_ref, L_ref), 2)
    })
    return df, queda_rel, queda_total, queda_entre

# função principal (idêntica à sua, mas retornando arrays diretamente)
def calcular_evaporadores(
    df_press_abs=df_press_abs,
    brix_inicial: float = 14,
    vaz_caldo: float = 250,
    temp_inicial: float = 98,
    press_vapor: float = 2.0,
    perda_rad_frac: float = 0.005,
    perda_incond_frac: float = 0.015,
    listaEvap = [3500, 2500, 2000, 1000, 1000, 1000, 1000],
    alvo_brix_final: tuple = (60, 62)
) -> Dict[str, Any]:
    
    P_ref = df_press_abs["Pressão Absoluta (bar)"].values
    T_ref = df_press_abs["Temperatura (°C)"].values
    H_ref = df_press_abs["Entalpia do Vapor (kcal/kg)"].values
    L_ref = df_press_abs["Calor Latente (kcal/kg)"].values

    def simular(mul_1, mul_2, press_vapor_local):
        # gera tabelas de pressão/temperatura (mesma chamada do original)
        df_seq_impar, *_ = calcular_pressao_temp(3, press_vapor_local, 11.0, 9.0, P_ref, T_ref, H_ref, L_ref)
        df_seq_par, *_ = calcular_pressao_temp(2, press_vapor_local, 11.0, 9.0, P_ref, T_ref, H_ref, L_ref)

        pressao_98C = np.interp([temp_inicial], T_ref, P_ref)[0]
        entalpia_98C = np.interp([temp_inicial], T_ref, H_ref)[0]
        latente_98C = np.interp([temp_inicial], T_ref, L_ref)[0]

        # quantidade de efeitos agora é 6
        quantidade = 6

        # Construção dos arrays de pressão/entalpia/latente seguindo o padrão alternado (impar/par)
        # Pressao_list deve ter comprimento == quantidade
        Pressao_list = [
            press_vapor_local,
            press_vapor_local,
            float(df_seq_impar.loc[1, "Pressão (bar)"]),
            float(df_seq_par.loc[1, "Pressão (bar)"]),
            float(df_seq_impar.loc[2, "Pressão (bar)"]),
            float(df_seq_par.loc[2, "Pressão (bar)"])
        ]

        # Entalpia_list e Latente_list devem ter comprimento == quantidade+1 (um estado adicional inicial)
        Entalpia_list = [
            entalpia_98C,
            float(df_seq_impar.loc[0, "Entalpia (kcal/kg)"]),
            float(df_seq_impar.loc[0, "Entalpia (kcal/kg)"]),
            float(df_seq_impar.loc[1, "Entalpia (kcal/kg)"]),
            float(df_seq_par.loc[1, "Entalpia (kcal/kg)"]),
            float(df_seq_impar.loc[2, "Entalpia (kcal/kg)"]),
            float(df_seq_par.loc[2, "Entalpia (kcal/kg)"])
        ]

        Latente_list = [
            latente_98C,
            float(df_seq_impar.loc[0, "Calor Latente (kcal/kg)"]),
            float(df_seq_impar.loc[0, "Calor Latente (kcal/kg)"]),
            float(df_seq_impar.loc[1, "Calor Latente (kcal/kg)"]),
            float(df_seq_par.loc[1, "Calor Latente (kcal/kg)"]),
            float(df_seq_impar.loc[2, "Calor Latente (kcal/kg)"]),
            float(df_seq_par.loc[2, "Calor Latente (kcal/kg)"])
        ]

        # Brix teórico, EPE, etc (agora baseados em 'quantidade')
        brix_teorico = np.linspace(brix_inicial, 68, quantidade + 1)
        brix_med = (brix_teorico[:-1] + brix_teorico[1:]) / 2
        EPE = np.concatenate(([0], (2 * brix_inicial) / (100 - brix_med)))

        temp_vapor = np.interp(Pressao_list, P_ref, T_ref)
        temp_caldo = [temp_inicial] + arrumar_lista(temp_vapor)
        temp_caldo_ajustada = [t + e for t, e in zip(temp_caldo, EPE)]

        # Vetores de tamanho adequado
        vazao_list = np.zeros(quantidade + 1)
        brix_list = np.zeros(quantidade + 1)
        vazVap_list = np.zeros(quantidade)            # vazão de vapor que entra em cada efeito
        Cp_list = np.zeros(quantidade + 1)
        ConsVap_list = np.zeros(quantidade)
        VapUtil_list = np.zeros(quantidade)
        vapGeradoTotal_list = np.zeros(quantidade)
        vazSangria_list = np.zeros(quantidade)
        taxaEvap = np.zeros(quantidade)

        vazao_list[0] = vaz_caldo * 1000
        brix_list[0] = brix_inicial
        Cp_list[0] = 1 - 0.006 * brix_list[0]

        for i in range(quantidade):
            # Consumo de vapor por entalpia (mantive a regra original: só nos dois primeiros efeitos)
            if i <= 1:
                Consumo_Vapor = vazao_list[i] * Cp_list[i] * (
                    (temp_caldo_ajustada[i + 1] - temp_caldo_ajustada[i]) / Entalpia_list[i]
                )
                ConsVap_list[i] = Consumo_Vapor
            else:
                ConsVap_list[i] = 0.0

            # Vazão de vapor injetada (mantive a regra: i==0 usa mul_1, i==1 usa mul_2)
            if i == 0:
                VazVapor = ConsVap_list[i] * mul_1
                vazVap_list[i] = VazVapor
            elif i == 1:
                VazVapor = ConsVap_list[i] * mul_2
                vazVap_list[i] = VazVapor
            # para i >= 2 vazVap_list[i] pode receber vapor oriundo de efeitos anteriores (através de vazVap_list[i] definido abaixo)
            # se não definido continua zero até ser calculado por propagação abaixo

            PerdRad = perda_rad_frac * vazVap_list[i]
            PerdIncond = perda_incond_frac * vazVap_list[i]
            VapUtil = vazVap_list[i] - PerdRad - PerdIncond - ConsVap_list[i]
            VapUtil_list[i] = VapUtil

            # vap gerado pelo efeito i (ajustado por latentes entre estágios)
            vapGerado = (Latente_list[i] / Latente_list[i + 1]) * VapUtil

            # VazFlash conservado conforme lógica original: não há flash nos dois primeiros efeitos
            VazFlash = 0.0 if i <= 1 else vazao_list[i] * Cp_list[i] * (
                (temp_caldo_ajustada[i] - temp_caldo_ajustada[i + 1]) / Latente_list[i]
            )

            vapGeradoTotal = vapGerado + VazFlash
            vapGeradoTotal_list[i] = vapGeradoTotal

            # Sangrias (mesma regra original)
            if i == 0:
                keySangria = 100 / 350
            elif i <= 2:
                keySangria = 14 / 350
            else:
                keySangria = 0
            vazSangria_list[i] = vazao_list[i] * keySangria

            # Propaga vapor para efeito i+2 se houver (antes havia if i <=2)
            if i + 2 < quantidade:
                vazVap_list[i + 2] = vapGeradoTotal_list[i] - vazSangria_list[i]

            # Atualiza vazões, concentrações e Cp
            vazao_list[i + 1] = vazao_list[i] - vapGeradoTotal_list[i]
            vazao_list[i + 1] = vazao_list[i + 1] if vazao_list[i + 1] != 0 else 1e-9
            brix_list[i + 1] = vazao_list[i] * brix_list[i] / vazao_list[i + 1]
            Cp_list[i + 1] = 1 - 0.006 * brix_list[i + 1]
            taxaEvap[i] = vapGeradoTotal_list[i] / listaEvap[i]

        # Retorna listas completas (observe vapGeradoTotal_list)
        return (
            brix_list[-1],
            brix_list,
            ConsVap_list,
            vazVap_list,
            vapGeradoTotal_list,
            vazao_list,
            Cp_list,
            VapUtil_list,
            taxaEvap,
            temp_caldo_ajustada,
            vazSangria_list
        )

    # Busca automática dos melhores multiplicadores (mesma lógica do original)
    melhor_brix, melhor_par, melhor_cons = None, (0, 0), 0.0
    for m1 in np.linspace(5, 15, 20):
        for m2 in np.linspace(1500, 2500, 20):
            (
                brix_final, brix_list, ConsVap_list, vazVap_list,
                vapGeradoTotal_list, vazao_list, Cp_list, VapUtil_list,
                taxaEvap, temp_caldo_ajustada, vazSangria_list
            ) = simular(m1, m2, press_vapor)
            if alvo_brix_final[0] <= brix_final <= alvo_brix_final[1]:
                melhor_brix = brix_final
                melhor_par = (m1, m2)
                melhor_cons = float(np.sum(ConsVap_list))
                break
        if melhor_brix is not None:
            break

    if melhor_brix is None:
        alvo = 0.5 * (alvo_brix_final[0] + alvo_brix_final[1])
        melhor_erro = 1e12
        for m1 in np.linspace(5, 15, 40):
            for m2 in np.linspace(1200, 2800, 40):
                (
                    brix_final, brix_list, ConsVap_list, vazVap_list,
                    vapGeradoTotal_list, vazao_list, Cp_list, VapUtil_list,
                    taxaEvap, temp_caldo_ajustada, vazSangria_list
                ) = simular(m1, m2, press_vapor)
                erro = abs(brix_final - alvo)
                if erro < melhor_erro:
                    melhor_erro = erro
                    melhor_par = (m1, m2)
                    melhor_brix = brix_final
        (
            brix_final, brix_lista, ConsVap_list, vazVap_list,
            vapGeradoTotal_list, vazao_list, Cp_list, VapUtil_list,
            taxaEvap, temp_caldo_ajustada, vazSangria_list
        ) = simular(*melhor_par, press_vapor)
        melhor_cons = float(np.sum(ConsVap_list))
    else:
        (
            brix_final, brix_lista, ConsVap_list, vazVap_list,
            vapGeradoTotal_list, vazao_list, Cp_list, VapUtil_list,
            taxaEvap, temp_caldo_ajustada, vazSangria_list
        ) = simular(*melhor_par, press_vapor)

    consumo_total_vapor = float(np.sum(ConsVap_list))
    vapor_entrada_12 = float(vazVap_list[0] + vazVap_list[1])

    resultados = {
        'Evaporadores': {
            "Brix Final (º)": round(brix_final, 2),
            "Brix Efeitos (º)": arrumar_lista(brix_lista),
            "Consumo Total de Vapor (kg/h)": round(consumo_total_vapor, 6),
            "Lista Consumo por Efeito (kg/h)": arrumar_lista(ConsVap_list),
            "Lista Vapor Entrada por Efeito (kg/h)": arrumar_lista(vazVap_list),
            "Injeção de Vapor VE (kg/h)": round(vapor_entrada_12, 2),
            "Taxa de Evaporação (%)": arrumar_lista(taxaEvap),
            "Lista de Vapores Gerados (kg/h)": arrumar_lista(vapGeradoTotal_list),
            "Vazão de Caldo em Cada Efeito (kg/h)": arrumar_lista(vazao_list),
            "Lista de Cp do Caldo (kcal/kg)": arrumar_lista(Cp_list),
            "Lista de Vapor Útil (kg/h)": arrumar_lista(VapUtil_list),
            "Lista de Temperatura em cada Efeito (ºC)": arrumar_lista(temp_caldo_ajustada),
            "Lista de Sangrias em cada efeito (kg/h)": arrumar_lista(vazSangria_list)
        }
    }
    return resultados

def calcular_processo_cozedores(
    xarBrix, xarVaz, purXarope, brixMelF, purMelF, disponi_agric, disponi_clim, disponi_indust
):
    
    # Balanço de massa por componente (Sacarose)
    vazSol = xarVaz/1000 * (xarBrix / 100)
    vazSac = vazSol * (purXarope / 100)

    vazImpureza = vazSol - vazSac

    # Vazão de Mel Final
    vazSacMelF = (vazImpureza*(purMelF/(100 - purMelF)))
    vazMelF = (vazSacMelF+vazImpureza)/(brixMelF/100)

    # Vazão de Açúcar
    vazSugar = vazSac - vazSacMelF

    # Sacas

    Sacas = (24*min(disponi_agric, disponi_clim, disponi_indust) * vazSugar * 1000)/50

    # SJM

    SJM = round((vazSugar/vazSac)*100,2)

    # Retornando um dicionário com os resultados
    resultados = {
        'Processo de Cozimento': {
            'Açúcar Produzido (ton/h)': vazSugar,
            'Mel Final Produzido (ton/h)': vazMelF,
            'Sacas Produzidas por Dia (50 kg)': Sacas,
            'SJM (%)': SJM
        }
    }
    
    return resultados

def calcular_tanque_mistura(vazao_entrada, brix_entrada, pol_entrada, vaz_mel, brix_mel, pureza_mel):
    
    '''
    Calcula os parâmetros de saída do Tanque de Mistura.
    Args:
        vaz_caldo_decant (float): Vazão de caldo na entrada do tanque de mistura (ton/h).
        brix_decant (float): Brix do caldo na entrada do tanque de mistura (º).
        vaz_mel (float): Vazão de melaço na entrada do tanque de mistura (ton/h).
        brix_mel (float): Brix do melaço na entrada do tanque de mistura (º).
    Returns:
        tuple: Uma tupla contendo a vazão de caldo misto (ton/h), o Brix do caldo misto (º) e a vazão volumétrica de saída (m³/h).
    '''

    vazao_mosto = vazao_entrada + vaz_mel
    brix_mosto = ((brix_entrada * vazao_entrada) + (brix_mel * vaz_mel)) / vazao_mosto
    dens_mosto = ((0.000028 * brix_mosto ** 2) + (0.002951 * brix_mosto) + 1.01037)
    vaz_mosto_m = vazao_mosto / dens_mosto

    pureza_misto = (pol_entrada / brix_entrada) * 100

    pureza_mosto = ((vazao_entrada * pureza_misto) + (vaz_mel * pureza_mel)) / vazao_mosto

    resultados = {
        'Tanque de Mistura': {
            'Vazão do Mosto Gerado (ton/h)': vazao_mosto,
            'Vazão do Mosto Gerado (m³/h)': vaz_mosto_m,
            'Brix do Mosto Gerado (º)': brix_mosto,
            'Pureza do Mosto (%)': pureza_mosto
        }
    }

    return resultados

def calcular_fermentacao(vazao_mosto, brix_mosto, pureza_mosto, conversao_fermentacao=0.90):
    '''
    Calcula os parâmetros de saída do processo de fermentação.

    Args:
        vazao_mosto (float): Vazão de caldo misto na entrada da fermentação (ton/h).
        brix_mosto (float): Brix do caldo misto na entrada da fermentação (º).
        pureza_mosto (float): Pureza do caldo misto na entrada da fermentação (%).
        convesao_fermentacao (float): Convesão da fermentação (%).

    Returns:
        tuple: Uma tupla contendo a vazão de mosto fermentado (ton/h), o Brix do mosto fermentado (º), a pureza do mosto fermentado (%) e a produção de etanol (litros/h).
    '''
    
    MMSac = 0.342
    MMH2O = 0.018
    MMEt = 0.046
    MMCO2 = 0.044
    
    vazao_Sol = vazao_mosto * (brix_mosto / 100)
    vazao_Sac = vazao_Sol * (pureza_mosto / 100)
    vazao_Agua = vazao_mosto - vazao_Sol
    Vaz_Sol_NS = vazao_Sol - vazao_Sac

    Vaz_Sac_mol_h = (vazao_Sac * 1000) / MMSac
    Vaz_Agua_mol_h = (vazao_Agua * 1000) / MMH2O

    VazEt_kg_h = (4 * (Vaz_Sac_mol_h * conversao_fermentacao) * MMEt)
    Vaz_Agua_ton_h = (vazao_Agua - (vazao_Sac * MMH2O)) * conversao_fermentacao
    Vaz_Co2_kg_h = (4 * (Vaz_Sac_mol_h * conversao_fermentacao) * MMCO2) / 1000
    Vaz_acucar_kg_h_dorna = (vazao_Sac * 1000) - (Vaz_Sac_mol_h * MMSac * conversao_fermentacao)
    Vaz_Saida_Dorna = (VazEt_kg_h + (Vaz_Agua_ton_h * 1000) + (Vaz_Sol_NS * 1000) + Vaz_acucar_kg_h_dorna)

    pEt = 0.789
    pAgua = 0.997

    Vazao_Et_L_h = VazEt_kg_h / pEt
    Vaz_Agua_L_h = ((Vaz_Agua_ton_h * 1000) + (Vaz_Sol_NS * 1000) + Vaz_acucar_kg_h_dorna) / pAgua
    Vaz_Saida_Dorna_L_h = Vaz_Agua_L_h + Vazao_Et_L_h

    GL_dorna = (Vazao_Et_L_h / Vaz_Agua_L_h) * 100

    frac_et = Vazao_Et_L_h/Vaz_Saida_Dorna_L_h

    resultados = {
        'Fermentação': {
            'Vazão do Vinho Fermentado (ton/h)': Vaz_Saida_Dorna/1000,
            'Vazão do Vinho Fermentado (m³/h)': Vaz_Saida_Dorna_L_h/1000,
            'Vazão de Etanol Presente na Dorna (m³/h)': Vazao_Et_L_h/1000,
            'GL na Dorna (º)': GL_dorna,
            'Fração de Etanol Presente no Vinho': frac_et
        }
    }

    return resultados

def coluna_destilacao(nome, vazao_in, frac_in, frac_fundo, frac_vap=None, frac_liq=None):
    etanol_in = vazao_in * frac_in
    saidas = {}

    # Trata valores None
    frac_vap_calc = frac_vap if frac_vap is not None else 0.0
    frac_liq_calc = frac_liq if frac_liq is not None else 0.0

    total_frac_sum = frac_vap_calc + frac_liq_calc + frac_fundo
    if total_frac_sum == 0:
        return {'coluna': nome, 'saidas': {}}

    # Saída vapor
    if frac_vap is not None:
        etanol_vap = etanol_in * (frac_vap_calc / total_frac_sum)
        VAPOR_OUT = etanol_vap / frac_vap if frac_vap > 0 else 0
        saidas['Vapor_Out'] = VAPOR_OUT
        saidas['Etanol_Vapor'] = VAPOR_OUT * frac_vap
        saidas['Frac_Et_Vapor'] = (saidas['Etanol_Vapor'] / VAPOR_OUT) if VAPOR_OUT > 0 else 0

    # Saída líquida
    if frac_liq is not None:
        etanol_liq_topo = etanol_in * (frac_liq_calc / total_frac_sum)
        LIQUIDO_OUT = etanol_liq_topo / frac_liq if frac_liq > 0 else 0
        saidas['Liquido_Out'] = LIQUIDO_OUT
        saidas['Etanol_Liquido'] = LIQUIDO_OUT * frac_liq
        saidas['Frac_Et_Liquido'] = (saidas['Etanol_Liquido'] / LIQUIDO_OUT) if LIQUIDO_OUT > 0 else 0

    # Saída fundo
    etanol_fundo = etanol_in * (frac_fundo / total_frac_sum)
    FUNDO_OUT = etanol_fundo / frac_fundo if frac_fundo > 0 else 0
    saidas['Fundo_Out'] = FUNDO_OUT
    saidas['Etanol_Fundo'] = FUNDO_OUT * frac_fundo
    saidas['Frac_Et_Fundo'] = (saidas['Etanol_Fundo'] / FUNDO_OUT) if FUNDO_OUT > 0 else 0

    return {'coluna': nome, 'saidas': saidas}

def sistema_destilacaoo_etanol_fundo(vazao_vinho, frac_vinho,
                                     frac_topo_AA1_vap, frac_topo_AA1_liq,
                                     frac_fundo_D):
    # --- Coluna AA1 ---
    colAA1 = coluna_destilacao('AA1', vazao_vinho, frac_vinho,
                               frac_fundo=0.01,
                               frac_vap=frac_topo_AA1_vap,
                               frac_liq=frac_topo_AA1_liq)

    # --- Coluna D ---
    feed_D = colAA1['saidas']['Liquido_Out']
    frac_in_D = colAA1['saidas']['Etanol_Liquido'] / feed_D if feed_D > 0 else 0
    colD = coluna_destilacao('D', feed_D, frac_in_D,
                             frac_fundo=frac_fundo_D,  # força etanol no fundo
                             frac_liq=0.05)            # mínimo no topo

    # --- Coluna B ---
    feed_B = colAA1['saidas']['Vapor_Out'] + colD['saidas']['Fundo_Out']
    etanol_feed_B = colAA1['saidas']['Etanol_Vapor'] + colD['saidas']['Etanol_Fundo']
    frac_in_B = etanol_feed_B / feed_B if feed_B > 0 else 0
    colB = coluna_destilacao('B', feed_B, frac_in_B,
                             frac_fundo=0.01,
                             frac_liq=0.95)

    # --- Resultados principais ---
    residuos_totais = (colAA1['saidas']['Fundo_Out'] +
                       colD['saidas']['Fundo_Out'] +
                       colB['saidas']['Fundo_Out'])
    frac_et_residuos = ((colAA1['saidas']['Etanol_Fundo'] +
                         colD['saidas']['Etanol_Fundo'] +
                         colB['saidas']['Etanol_Fundo']) / residuos_totais) if residuos_totais > 0 else 0

    return {
        'Destilação': {
            'Coluna AA1': colAA1,
            'Coluna D': colD,
            'Coluna B': colB,
            'Produto Final (ETANOL-2 Fundo D)': colD['saidas']['Etanol_Fundo'],
            'Frac Etanol (Fundo D)': colD['saidas']['Frac_Et_Fundo'],
            'Produto Final (ETHID B)': colB['saidas']['Etanol_Liquido'],
            'Frac Etanol (ETHID B)': colB['saidas']['Frac_Et_Liquido'],
            'Resíduos Totais': residuos_totais,
            'Frac Etanol Resíduos': frac_et_residuos
        }
    }

def calcular_poderes_calorificos(umidade_pct, C = 0.446, H=0.058, O=0.445, S = 0.001, cinzas_pct=0.6):
    # Base seca
    PCS_seco_kj_kg = 33900 * C + 141800 * ( H - O / 8) + 9200 * S  # kJ/kg
    PCI_seco_kj_kg = PCS_seco_kj_kg - 2440 * (9 * H + umidade_pct)        # kJ/kg
                
    # Base tal qual
    cinzas = cinzas_pct / 100
    PCS_umido_MJ_kg = PCS_seco_kj_kg / 1000 * (1 - umidade_pct - cinzas)  # MJ/kg
    PCI_umido_MJ_kg = PCI_seco_kj_kg / 1000 * (1 - umidade_pct - cinzas) - 2.442 * umidade_pct  # MJ/kg
                
    return PCS_seco_kj_kg / 1000, PCI_seco_kj_kg / 1000, PCS_umido_MJ_kg, PCI_umido_MJ_kg  # MJ/kg

def calcular_vapor_e_eletricidade(vazao_bagaco_ton_h, umidade_pct, eficiencia_caldeira, DELTA_H_MJ_KG):
    '''
    Calcula a energia térmica do bagaço, energia útil do vapor e potência elétrica gerada.
                
    Parâmetros:
    vazao_bagaco_ton_h : float
    Vazão de bagaço fornecido à caldeira (t/h)
    umidade_pct : float
    Umidade do bagaço (%)
    eficiencia_caldeira : float
    Eficiência térmica da caldeira (fração 0-1)
                
    Retorna:
    energia_combustivel_MW : float
    Energia total contida no bagaço (MW)
    energia_vapor_MW : float
    Energia efetivamente convertida em vapor pela caldeira (MW)
    vazao_vapor_ton_h : float
    Vazão de vapor gerado (t/h)
    potencia_eletrica_cogeracao_MW : float
    Potência elétrica gerada para cogeração interna (MW)
    potencia_eletrica_condensacao_MW : float
    Potência elétrica gerada em turbina de condensação (MW)
    kWh_por_ton_bagaco_cogeracao : float
    kWh gerado por tonelada de bagaço na cogeração
    kWh_por_ton_bagaco_condensacao : float
    kWh gerado por tonelada de bagaço na turbina de condensação
    '''
                
    # --- PCI do bagaço úmido ---
    _, _, _, pci_umido_MJ_kg = calcular_poderes_calorificos(umidade_pct)
                
    # --- Conversão de vazão de bagaço t/h para kg/s ---
    vazao_bagaco_kg_s = vazao_bagaco_ton_h * 1000 / 3600
                
    # --- Energia total do combustível (MW) ---
    energia_combustivel_MW = vazao_bagaco_kg_s * pci_umido_MJ_kg
                
    # --- Energia convertida em vapor pela caldeira ---
    energia_vapor_MW = energia_combustivel_MW * eficiencia_caldeira
                
    # --- Vazão de vapor gerado (t/h) ---
    vazao_vapor_ton_h = (energia_vapor_MW / DELTA_H_MJ_KG) * 3600 / 1000
                
    # --- Eficiências elétricas ---
    eficiencia_eletrica_cogeracao = 0.24  # 24% da energia do bagaço vira eletricidade na cogeração
    eficiencia_eletrica_condensacao = 0.30 # 30% da energia do bagaço vira eletricidade na turbina de condensação
                
    # --- Potência elétrica (MW) ---
    potencia_eletrica_cogeracao_MW = energia_combustivel_MW * eficiencia_eletrica_cogeracao
    potencia_eletrica_condensacao_MW = energia_combustivel_MW * eficiencia_eletrica_condensacao
                
    # --- kWh gerado por tonelada de bagaço ---
    kWh_por_ton_bagaco_cogeracao = (potencia_eletrica_cogeracao_MW * 1000) / vazao_bagaco_ton_h
    kWh_por_ton_bagaco_condensacao = (potencia_eletrica_condensacao_MW * 1000) / vazao_bagaco_ton_h

    resultados = {
        'Caldeira': {
            'Energia do Combustível (MW)': energia_combustivel_MW,
            'Energia do Vapor (MW)': energia_vapor_MW,
            'Vazão de Vapor (ton/h)': vazao_vapor_ton_h,
            'Potência Elétrica - Cogeração (MW)': potencia_eletrica_cogeracao_MW,
            'Potência Elétrica - Condensação (MW)': potencia_eletrica_condensacao_MW,
            'kWh por tonelada de bagaço - Cogeração': kWh_por_ton_bagaco_cogeracao,
            'kWh por tonelada de bagaço - Condensação': kWh_por_ton_bagaco_condensacao
        }
    }

    return resultados