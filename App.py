import streamlit as st
import os
import json
from emojis import EMOJIS as em
from Funcoes import *
from Dimensionamento_Equip import *
import plotly_express as px
import plotly.graph_objects as go

st.set_page_config(page_title='Sistema de Registro', layout='wide', page_icon=f'{em['Usina']['fabrica']}')

USERS_FILE = 'usuarios_Simul.json'
DADOS_FILE = 'dados.csv'
EQUIPAMENTOS_FILE = 'dados_por_equipamento.xlsx'

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None
if 'nivel' not in st.session_state:
    st.session_state['nivel'] = None
if 'lista_evaporadores_original' not in st.session_state:
    st.session_state['lista_evaporadores_original'] = [3500, 2500, 2000, 1000, 1000, 1000, 1000]
# Adicionando a variável de estado para controlar a exibição do salvamento
if 'simulacao_enviada' not in st.session_state:
    st.session_state['simulacao_enviada'] = False

tema = st.get_option('theme.base')
if tema == 'dark':
    cor_linha = '#FFB300'  # amarelo/dourado para escuro
    cor_barra = '#FFB300'
else:
    cor_linha = '#103185'  # azul para claro
    cor_barra = '#103185'

def carregar_usuarios():
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def autenticar_usuario(usuario, senha):
    usuarios = carregar_usuarios()
    if usuario in usuarios and usuarios[usuario]['senha'] == senha:
        return usuarios[usuario]['nivel']
    return None

if not os.path.exists(USERS_FILE):
    users = {
        'Fab_user': {'senha': '123', 'nivel': 'Fábrica'},
        'Dest_user':  {'senha': '123', 'nivel': 'Destilaria'},
        'Cald_user':   {'senha': '123', 'nivel': 'Caldeira'},
        'Gest_user': {'senha': '123', 'nivel': 'Gestão'},
        'AS_user': {'senha': '123', 'nivel': 'Análise de Sensibilidade'},
        'PDF_user': {'senha': '123', 'nivel': 'PDF'}
    }

    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# --- Autenticação e Layout Principal ---
if not st.session_state['autenticado']:
    col1, col2, col3, col4, col5, col6, col7 = st.columns([1,1,1,2,1,1,1])
    #col4.image(r'C:\Pessoal - Sans\Portifolio\Python\Projeto de Estagio\V4.0\Captura de tela 2025-08-15 144705.png', width=300)
    st.title('🔐 Login para Sistema de Simulação')
    usuario = st.text_input('Usuário')
    senha = st.text_input('Senha', type='password')
    if st.button('Entrar'):
        nivel = autenticar_usuario(usuario, senha)
        if nivel:
            st.session_state['autenticado'] = True
            st.session_state['usuario'] = usuario
            st.session_state['nivel'] = nivel
            st.rerun()
        else:
            st.error('Usuário ou senha inválidos.')

else:
    nivel = st.session_state['nivel']
    col1, col2, col3 = st.columns([1, 2, 1])
    #col1.image(r'C:\Pessoal - Sans\Portifolio\Python\Projeto de Estagio\V4.0\Captura de tela 2025-08-15 144705.png', width=300)
    col2.title(f'{em['financeiro']['chart_up']} SIMULAÇÃO DA USINA SONORA: {nivel}')
    st.divider()

    if nivel in ['PDF']:
        st.title('Sistema de Geração de Relatório')
        area_PDF = st.selectbox('Escolha a área',
                            ('Fábrica', 'Destilaria', 'Caldeira'),
                            index = None)
        if area_PDF:
            df_filtrado_PDF = Filtra_area(DADOS_FILE, area_PDF)
            Simulacoes_PDF = Lista_Simulacao(df_filtrado_PDF)
                    
            Simulacao_PDF = st.selectbox('Escolha a Simulação',
                                        Simulacoes_PDF,
                                        index = None)
            if st.button("Gerar Relatório PDF"):
                pdf_gerado = gerar_pdf(DADOS_FILE, area_PDF, Simulacao_PDF)
                if pdf_gerado:
                    st.success(f"PDF gerado com sucesso: {pdf_gerado}")
                    # Permitir download
                    with open(pdf_gerado, "rb") as f:
                        st.download_button("Baixar PDF", f, file_name=pdf_gerado)
        if area_PDF == "Fábrica" and Simulacao_PDF:
            if st.button("Gerar Apresentação LaTeX"):
                slide_gerado = gerar_slide_fabrica(DADOS_FILE, Simulacao_PDF)
                if slide_gerado:
                    st.success(f"Slide gerado com sucesso: {slide_gerado}")
                    with open(slide_gerado, "rb") as f:
                        st.download_button("Baixar Apresentação", f, file_name=slide_gerado)
        

    if nivel in ['Fábrica', 'Destilaria', 'Caldeira', 'Gestão']:
        with st.expander('Entrada de Variáveis'):
            with st.form('form_var_simu'):
                st.title('Dados de Entrada')
                col1, col2 = st.columns(2)
                Ton_cana_dia = col1.number_input('Tonelada de Cana no dia', min_value=0.0, value=9507.0)
                mix_acucar = col2.number_input('Mix para açúcar', min_value=0.0, value=50.0, max_value=100.0) / 100
                st.subheader('Disponibilidade')
                col1, col2, col3 = st.columns(3)
                Disponi_Indust = col1.number_input('Disponibilidade da Indústria (%)', min_value=0.0, value=100.00, max_value = 100.0) / 100
                Disponi_Agric = col2.number_input('Disponibilidade Agrícola (%)', min_value=0.0, value=100.0, max_value = 100.0) / 100
                Disponi_Clim = col3.number_input('Disponibilidade Climática (%)', min_value=0.0, value=100.0, max_value = 100.0) / 100
                with st.expander('Dados da Moenda'):
                    st.subheader(f'Dados Moenda')
                    col1, col2, col3 = st.columns(3)
                    Extra_terno = col1.number_input('Extração do Primeiro Terno (%)', min_value=0.0, value=70.0, max_value = 100.0 ) / 100
                    Embebi_Fibra = col2.number_input('Embebição (% da Fibra)', min_value=0.0, value=190.0) / 100
                    Umid_Bag = col3.number_input('Umidade do Bagaço (%)', min_value=0.0, value=52.2, max_value = 100.0) / 100
                    st.subheader('Caldo Primário')
                    col1, col2, col3 = st.columns(3)
                    Brix_Prim = col1.number_input('Brix do Caldo Primário (º)', min_value=0.0, value=17.08, max_value=100.0)
                    Pol_Prim = col2.number_input('Pol do Caldo Primário (º)', min_value=0.0, value=14.21, max_value=round(Brix_Prim, 2))
                    Fibra_Cana = col3.number_input('Fibra da Cana (%)', min_value=0.0, value=12.29, max_value=100.0) / 100
                    Temp_Cald_Prim = st.number_input('Temperatura do Caldo Primário (ºC)', min_value=0.0, value=27.0)
                    
                    Extracao = calcular_moenda(Ton_cana_dia, Disponi_Agric, Disponi_Clim, Disponi_Indust,
                                                Extra_terno, Embebi_Fibra, Umid_Bag, Brix_Prim, Pol_Prim, 
                                                Fibra_Cana)
                
                if nivel in ['Fábrica', 'Gestão']:
                    st.title(f'FABRICAÇÃO DE AÇÚCAR')
                    
                    st.header('Vazão para a Fábrica')
                    Vaz_Fab = st.number_input('Vazão de Caldo para a Fábrica (m³/h)', min_value=0.0,
                                              value=round(mix_acucar*Extracao['Extração']['Vazão de Caldo Primário (m³/h)'],0),
                                              max_value=Extracao['Extração']['Vazão de Caldo Primário (m³/h)']) * Extracao['Extração']['Densidade do Caldo Primário']
                    st.header('Tratamento de Caldo')
                    col1, col2 = st.columns(2)
                    col1.subheader('Aquecedores')
                    Temp_aque_aq = col1.number_input('Temp. da Água/Vinhaça (Aquecedores)', min_value=0.0, value=90.0)
                    col2.subheader('Trocadores de Calor')
                    Temp_aque_tc = col2.number_input('Temp. da Água/Vinhaça (Trocadores)', min_value=0.0, value=115.0)
                    st.subheader('Decantador')
                    col1, col2, col3, col4, col5 = st.columns(5)
                    Reten_Decant = col1.number_input('Retenção do Decantador (%)', min_value=0.0, value=17.0, max_value=100.0) / 100
                    Brix_Lodo = col2.number_input('Brix do Lodo (º)', min_value=0.0, value = 8.0)
                    Pol_Decant = col3.number_input('Pol do Caldo na Saída do Decantador (%)', min_value=0.0, value=19.2)
                    Dosagem_poli = col4.number_input('Dosagem de Polímero (ppm)', min_value=0.0, value=3.0)
                    Pol_filtrado = col5.number_input('Pol do filtrado (%)', min_value=0.0, value=6.2)
                    st.subheader('Balão Flash')
                    Temp_Said_Balao_Flash = st.number_input('Temp. Saída do Balão Flash (ºC)',min_value=0.0, value=95.0)
                    st.header('Concentração do Caldo')
                    st.subheader('Evaporadores')
                    col1, col2, col3 = st.columns(3)
                    Press_Vap_Escape = col1.number_input('Pressão do Vapor de Escape (kgf/cm²)', min_value=0.0, value=3.0) * 0.980665
                    Press_Vap_Escape = round(Press_Vap_Escape,2)
                    Pol_Xarope = col2.number_input('Pol do Xarope Final (%)', min_value=0.0, value=44.45)

                    with col3:    
                        Evap_Parado = st.selectbox(
                            'Escolha a área do Evaporador parado (m²).',
                            sorted(set(st.session_state['lista_evaporadores_original']), reverse=False),
                            index = 0
                        )
                    st.subheader('Fábrica de Açúcar')
                    col1, col2 = st.columns(2)
                    Brix_Mel_Final = col1.number_input('Brix do Mel Final (%)',min_value=0.0, value=67.92)
                    Purez_Mel_Final = col2.number_input('Pureza do Mel Final (%)', min_value=0.0, value=58.26) / 100
                    st.divider()
    
                if nivel in ['Destilaria', 'Gestão']:
                    st.title(f'PRODUÇÃO DE ETANOL {em['Usina']['etanol']}')
    
                    st.subheader('Caldo Misto')
                    col1, col2, col3 = st.columns(3)
                    vazao_misto = col1.number_input('Vazão de Caldo Misto (ton/h)', min_value=0.0, value=50.0)
                    Brix_misto = col2.number_input('Brix do Caldo Misto (º)', min_value=0.00, value=9.77)
                    Pol_misto  = col3.number_input('Pol do Caldo Misto (º)', min_value=0.00, value=7.99)
    
                    st.subheader('Mel Final')
                    col1, col2, col3 = st.columns(3)
                    vazao_Mel = col1.number_input('Vazão de Mel (ton/h)', min_value=0.0, value=10.0)
                    Brix_Mel_Final = col2.number_input('Brix do Mel Final (º)', min_value=0.0, value=68.0)
                    pureza_Mel_Final = col3.number_input('Pureza do Mel Final (%)', min_value=0.0, value=55.0) / 100
    
                    st.subheader('Destilação')
                    col1, col2, col3, col4 = st.columns(4)
                    frac_fleg_vaptopo = col1.number_input('Fração de Etanol na Flegma Vapor Topo (Coluna AA1)', min_value=0.0, value=0.6)
                    frac_Fleg_vapmeio = col2.number_input('Fração de Etanol na Flegma Vapor Meio (Coluna AA1)', min_value=0.0, value=0.4)
                    frac_Fleg_Liq = col3.number_input('Fração de Etanol na Flegma Líquida (Coluna D)', min_value=0.0, value=0.9)                                                
    
                if nivel in ['Caldeira', 'Gestão']:
                    st.title(f'PRODUÇÃO DE VAPOR E ENERGIA {em['Usina']['vapor']} {em['Usina']['energia']}')
    
                    col1, col2 = st.columns(2)
                    col1.subheader('Caldeira 3')
                    vazao_bag_cald3 = col1.number_input('Vazão de Bagaço para a Caldeira 3 (ton/h)', min_value=0.0, max_value=Extracao['Extração']['Vazão de Bagaço (ton/h)'], value=0.5*Extracao['Extração']['Vazão de Bagaço (ton/h)'])
                    col2.subheader('Caldeira 4')
                    vazao_bag_cald4 = col2.number_input('Vazão de Bagaço para a Caldeira 4 (ton/h)', min_value=0.0, max_value=Extracao['Extração']['Vazão de Bagaço (ton/h)'], value=0.5*Extracao['Extração']['Vazão de Bagaço (ton/h)'])
    
                enviado = st.form_submit_button('Enviar Variáveis')
                
                if enviado:
                    st.session_state['simulacao_enviada'] = True

        if st.session_state['simulacao_enviada']:

            # ========== EXTRAÇÃO ==========
            st.header('EXTRAÇÃO')
            st.subheader('Moenda')
            
            # ---------------- MÉTRICAS ----------------
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric('Tonelada Cana Hora (ton/h)', f'{Extracao['Extração']['Tonelada de Cana por hora']:.2f}')
            col2.metric('Disponibilidade Geral (h)', f'{Extracao['Extração']['Disponibilidade Geral (h)']:.0f}')
            col3.metric('Vazão de Embebição (ton/h)', f'{Extracao['Extração']['Vazão de Embebição (m³/h)']:.2f}')
            if nivel in ['Fábrica', 'Destilaria', 'Gestão']:
                col4.metric('Vazão de Caldo Primário (m³/h)', f'{Extracao['Extração']['Vazão de Caldo Primário (m³/h)']:.2f}')
            elif nivel in ['Caldeira']:
                col4.metric('Vazão de Bagaço (ton/h)', f'{Extracao['Extração']['Vazão de Bagaço (ton/h)']:.2f}')
            st.divider()

        if 'simulacao_enviada' in st.session_state and st.session_state['simulacao_enviada'] and nivel in ['Fábrica', 'Gestão']:
                
                Aquecedor = calcular_aquecimento('Aquecedor',AQUECEDOR['Quantidade'], Temp_Cald_Prim,
                                                 Temp_aque_aq, AQUECEDOR['Diâmetro Interno'],AQUECEDOR['Quantidade de Passes'],
                                                 AQUECEDOR['Quantidade de Tubos'],AQUECEDOR['Comprimento do Tubo'], Brix_Prim,
                                                 Vaz_Fab)
    
                Sulfitacao = calcular_sulfitacao(Vaz_Fab)
    
                Caleacao = calcular_caleacao(Vaz_Fab)
    
                Trocador_de_Calor = calcular_aquecimento('Trocador de Calor',TROCADOR_DE_CALOR['Quantidade'],
                                                         Aquecedor['Aquecedor']['Lista de Temperaturas (ºC)'][-1],
                                                         Temp_aque_tc, TROCADOR_DE_CALOR['Diâmetro Interno'],TROCADOR_DE_CALOR['Quantidade de Passes'],
                                                         TROCADOR_DE_CALOR['Quantidade de Tubos'],TROCADOR_DE_CALOR['Comprimento do Tubo'], Brix_Prim,
                                                         Vaz_Fab)
    
                Balao_Flash = calcular_balao_flash(Vaz_Fab, Brix_Prim,
                                                   Trocador_de_Calor['Trocador de Calor']['Lista de Temperaturas (ºC)'][-1],
                                                   Temp_Said_Balao_Flash)
    
                Filto_Rotativo = calcular_filtro_rotativo(Balao_Flash['Balão Flash']['Vazão de Saída do Balão Flash (ton/h)'],
                                                          Balao_Flash['Balão Flash']['Brix de Saída do Balão Flash (º)'])
    
                Decantador = calcular_decantador(Filto_Rotativo['Filtro Rotativo']['Vazão de Saída do Filtro Rotativo (ton/h)'],
                                                 Filto_Rotativo['Filtro Rotativo']['Brix de Saída do Filtro Rotativo (º)'],
                                                 Reten_Decant, Brix_Lodo, Pol_Decant)
    
                Sol_Susp_kg_m3 = 50
                Filtro_Prensa = calcular_filtro_prensa(Decantador['Decantador']['Vazão de Lodo (ton/h)'],Sol_Susp_kg_m3,Brix_Lodo)
    
                Peneira_Rotativa = calcular_peneira_rotativa(Decantador['Decantador']['Vazão de Caldo na Saída do Decantador (ton/h)'],
                                                             Decantador['Decantador']['Brix do Caldo na Saída do Decantador (º)'])
        
                lista_para_calculo = list(st.session_state['lista_evaporadores_original'])
                lista_para_calculo.remove(Evap_Parado)
                
                Evaporador = calcular_evaporadores(df_press_abs, Peneira_Rotativa['Peneira Rotativa']['Brix de Saída da Peneira Rotativa (º)'],Peneira_Rotativa['Peneira Rotativa']['Vazão de Caldo na Saída da Peneira Rotativa (ton/h)'], Temp_Said_Balao_Flash, Press_Vap_Escape, listaEvap=lista_para_calculo)

                fabAcucar = calcular_processo_cozedores(Evaporador['Evaporadores']['Brix Final (º)'],Evaporador['Evaporadores']['Vazão de Caldo em Cada Efeito (kg/h)'][-1],(Pol_Xarope/Evaporador['Evaporadores']['Brix Final (º)'])*100,Brix_Mel_Final, Purez_Mel_Final*100,Disponi_Agric, Disponi_Clim, Disponi_Indust)
            
                Simulacao = [
                    Extracao,
                    Aquecedor,
                    Sulfitacao,
                    Caleacao,
                    Trocador_de_Calor,
                    Balao_Flash,
                    Filto_Rotativo,
                    Decantador,
                    Filtro_Prensa,
                    Peneira_Rotativa,
                    Evaporador,
                    fabAcucar
                ]

                st.session_state['Simulacao'] = Simulacao
                st.session_state['Lista_Evaporadores_Atual'] = lista_para_calculo

                Extracao = Simulacao[0]
                Aquecedor = Simulacao[1]
                Sulfitacao = Simulacao[2]
                Caleacao = Simulacao[3]
                Trocador_de_Calor = Simulacao[4]
                Balao_Flash = Simulacao[5]
                Filto_Rotativo = Simulacao[6]
                Decantador = Simulacao[7]
                Filtro_Prensa = Simulacao[8]
                Peneira_Rotativa = Simulacao[9]
                Evaporador = Simulacao[10]
                #Cristalizador_Cozedores = Simulacao[11]
        
                st.header('TRATAMENTO DE CALDO')
                
                # ========== AQUECEDORES ==========
        
                st.subheader('Aquecedores')
                
                # ---------------- MÉTRICAS ----------------
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric('Velocidade (m/s)', f'{Aquecedor['Aquecedor']['Velocidade (m/s)']:.2f}',
                            delta=f'{(Aquecedor['Aquecedor']['Velocidade (m/s)'] - 2):.2f}'
                            if Aquecedor['Aquecedor']['Velocidade (m/s)'] > 2
                            else f'{(1.5 - Aquecedor['Aquecedor']['Velocidade (m/s)']):.2f}'
                            if Aquecedor['Aquecedor']['Velocidade (m/s)'] < 1.5 else None, delta_color = 'inverse')
                
                col2.metric('Temperatura Final (ºC)', f'{Aquecedor['Aquecedor']['Lista de Temperaturas (ºC)'][-1]:.2f}',
                            delta=f'{Aquecedor['Aquecedor']['Lista de Temperaturas (ºC)'][-1] - Aquecedor['Aquecedor']['Lista de Temperaturas (ºC)'][0]:.2f}')
                
                col3.metric('Perda de Carga (kgf/cm²)', f'{Aquecedor['Aquecedor']['Lista de Perdas (kgf/cm²)'][-1]:.2f}')
        
                col4.metric('Vazão de Aquecimento Total (ton/h)', f'{Aquecedor['Aquecedor']['Calor trocado (kcal)']:.2f}')
        
                # ---------------- TABELAS ----------------
                
                DF_AQUECEDORES = pd.DataFrame({
                    'Aquecedor': ['Inicial'] + [f'Aquecedor {i}' for i in range(1, len(Aquecedor['Aquecedor']['Lista de Temperaturas (ºC)']))],
                    'Temperatura (ºC)': Aquecedor['Aquecedor']['Lista de Temperaturas (ºC)'],
                    'Perdas (kgf/cm²)': Aquecedor['Aquecedor']['Lista de Perdas (kgf/cm²)']
                })
        
                # ---------------- GRÁFICOS ----------------
        
                fig_temp_aq = px.line(DF_AQUECEDORES, x='Aquecedor',
                                                    y='Temperatura (ºC)',
                                                    title='Temperatura dos Aquecedores',
                                                    text='Temperatura (ºC)')
                fig_temp_aq.update_traces(textposition='top center', line=(dict(color=cor_linha)))
                fig_temp_aq.update_layout(yaxis_range=[20, max(Aquecedor['Aquecedor']['Lista de Temperaturas (ºC)'])*1.2])
                st.plotly_chart(fig_temp_aq, use_container_width=True)
                
                fig_perda_aq = px.bar(DF_AQUECEDORES, x='Aquecedor', 
                                                    y='Perdas (kgf/cm²)',
                                                    title='Perdas dos Aquecedores',
                                                    text='Perdas (kgf/cm²)',
                                                    color_discrete_sequence=[cor_barra])
                fig_perda_aq.update_traces(textposition='outside')
                fig_perda_aq.update_layout(yaxis_range=[0, max(Aquecedor['Aquecedor']['Lista de Perdas (kgf/cm²)'])*1.2])
                st.plotly_chart(fig_perda_aq, use_container_width=True)
        
                # ---------------- VIZUALIZAÇÃO DAS TABELAS ----------------
        
                with st.expander('Tabelas Aquecedores'):
                    st.dataframe(DF_AQUECEDORES, use_container_width=True, hide_index=True)
                st.divider()
        
                # ========== SULFITAÇÃO E CALEAÇÃO ==========
                st.header('Tratamento Químico')
                col1, col2 = st.columns(2)
                col1.subheader('Sulfitação')
                col2.subheader('Caleação')
        
                # ---------------- MÉTRICAS ----------------
        
                col1, col2, col3, col4 = st.columns(4)
                col1.metric('Vazão de Enxofre necessário (kg/h)', f'{Sulfitacao['Sulfitação']['Vazão de Enxofre (kg/h)']:.2f}')
                col2.metric('Vazão de Oxigênio necessário para a queima (kg/h)', f'{Sulfitacao['Sulfitação']['Vazão de Oxigênio']:.2f}')
                col3.metric('Vazão de Cal necessário (kg/h)', f'{Caleacao['Caleação']['Vazão de Cal (kg/h)']:.2f}')
                col4.metric('Vazão de Água necessário para a queima (kg/h)', f'{Caleacao['Caleação']['Vazão de Água (kg/h)']:.2f}')
                st.divider()
        
                # ========== TROCADORES DE CALOR ==========
                st.subheader('Trocadores de Calor')
        
                # ---------------- MÉTRICAS ----------------
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric('Velocidade (m/s)', f'{Trocador_de_Calor['Trocador de Calor']['Velocidade (m/s)']:.2f}',
                            delta=f'{(Trocador_de_Calor['Trocador de Calor']['Velocidade (m/s)'] - 2):.2f}'
                            if Trocador_de_Calor['Trocador de Calor']['Velocidade (m/s)'] > 2
                            else f'{(1.5 - Trocador_de_Calor['Trocador de Calor']['Velocidade (m/s)']):.2f}'
                            if Trocador_de_Calor['Trocador de Calor']['Velocidade (m/s)'] < 1.5 else None, delta_color = 'inverse')
                
                col2.metric('Temperatura Final (ºC)', f'{Trocador_de_Calor['Trocador de Calor']['Lista de Temperaturas (ºC)'][-1]:.2f}',
                            delta=f'{Trocador_de_Calor['Trocador de Calor']['Lista de Temperaturas (ºC)'][-1] - Trocador_de_Calor['Trocador de Calor']['Lista de Temperaturas (ºC)'][0]:.2f}')
                col3.metric('Perda de Carga (kgf/cm²)', f'{Trocador_de_Calor['Trocador de Calor']['Lista de Perdas (kgf/cm²)'][-1]:.2f}')
                col4.metric('Vazão de Aquecimento Total (ton/h)', f'{Trocador_de_Calor['Trocador de Calor']['Calor trocado (kcal)']:.2f}')
        
                # ---------------- TABELAS ----------------
                
                DF_TROCADORC = pd.DataFrame({
                    'Trocador de Calor': ['Inicial'] + [f'Trocador de Calor {i}' for i in range(1, len(Trocador_de_Calor['Trocador de Calor']['Lista de Temperaturas (ºC)']))],
                    'Temperatura (ºC)': Trocador_de_Calor['Trocador de Calor']['Lista de Temperaturas (ºC)'],
                    'Perdas (kgf/cm²)': Trocador_de_Calor['Trocador de Calor']['Lista de Perdas (kgf/cm²)']
                })
        
                # ---------------- GRÁFICOS ----------------
        
                fig_temp_tc = px.line(DF_TROCADORC, x='Trocador de Calor',
                                                    y='Temperatura (ºC)', 
                                                    title='Temperatura dos Trocadores de Calor', 
                                                    text='Temperatura (ºC)',
                                                    markers=True)
                fig_temp_tc.update_traces(textposition='top center', line=(dict(color=cor_linha)))
                fig_temp_tc.update_layout(yaxis_range=[20, max(Trocador_de_Calor['Trocador de Calor']['Lista de Temperaturas (ºC)'])*1.2])
                
                st.plotly_chart(fig_temp_tc, use_container_width=True)
                fig_perda_tc = px.bar(DF_TROCADORC, x='Trocador de Calor', 
                                                    y='Perdas (kgf/cm²)',
                                                    title='Perdas dos Trocadores de Calor',
                                                    text='Perdas (kgf/cm²)',
                                                    color_discrete_sequence=[cor_barra])
                fig_perda_tc.update_traces(textposition='outside')
                fig_perda_tc.update_layout(yaxis_range=[0, max(Trocador_de_Calor['Trocador de Calor']['Lista de Perdas (kgf/cm²)'])*1.2])
                st.plotly_chart(fig_perda_tc, use_container_width=True)
                
                # ---------------- VIZUALIZAÇÃO DAS TABELAS ----------------
                
                with st.expander('Tabelas Trocadores de Calor'):
                    st.dataframe(DF_TROCADORC, use_container_width=True, hide_index=True)
                st.divider()
        
                # ========== BALÃO FLASH ==========
                
                st.subheader('Balão Flash')
        
                # ---------------- MÉTRICAS ----------------
        
                col1, col2 = st.columns(2)
                col1.metric('Vazão de Caldo na Saída do Balão Flash (m³/h)',
                            f'{Balao_Flash['Balão Flash']['Vazão de Saída do Balão Flash (m³/h)']:.2f}',
                            delta=f'{Balao_Flash['Balão Flash']['Vazão de Saída do Balão Flash (m³/h)'] - Vaz_Fab:.2f}')
                
                col2.metric('Brix do Caldo na Saída do Balão Flash (º)',
                            f'{Balao_Flash['Balão Flash']['Brix de Saída do Balão Flash (º)']:.2f}',
                            delta=f'{(((Balao_Flash['Balão Flash']['Brix de Saída do Balão Flash (º)']/Brix_Prim)-1)*100):.2f} %')
                st.divider()
        
                # ========== FILTRO ROTATIVO ==========
                
                st.subheader('Filtro Rotativo')
        
                # ---------------- MÉTRICAS ----------------
        
                col1, col2 = st.columns(2)
                col1.metric('Vazão de Caldo na Saída do Filtro Rotativo (m³/h)',
                            f'{Filto_Rotativo['Filtro Rotativo']['Vazão de Saída do Filtro Rotativo (m³/h)']:.2f}',
                            delta=f'{Filto_Rotativo['Filtro Rotativo']['Vazão de Saída do Filtro Rotativo (m³/h)'] - Balao_Flash['Balão Flash']['Vazão de Saída do Balão Flash (m³/h)']:.2f}')
                
                col2.metric('Brix do Caldo na Saída do Filtro Rotativo (º)',
                            f'{Filto_Rotativo['Filtro Rotativo']['Brix de Saída do Filtro Rotativo (º)']:.2f}',
                            delta=f'{(((Filto_Rotativo['Filtro Rotativo']['Brix de Saída do Filtro Rotativo (º)']/Balao_Flash['Balão Flash']['Brix de Saída do Balão Flash (º)'])-1)*100):.2f} %')
                st.divider()
        
                # ========== DECANTADOR E FILTRO PRENSA ==========
                st.header('Decantador e Filtro Prensa')
                
                # ========== DECANTADOR ==========
        
                st.subheader('Decantador')
        
                # ---------------- MÉTRICAS ----------------
        
                col1, col2, col3, col4 = st.columns(4)
                col1.metric('Vazão de Caldo na Saída do Decantador (ton/h)',
                            f'{Decantador['Decantador']['Vazão de Caldo na Saída do Decantador (m³/h)']:.2f}',
                            delta=f'{Decantador['Decantador']['Vazão de Caldo na Saída do Decantador (m³/h)'] - Filto_Rotativo['Filtro Rotativo']['Vazão de Saída do Filtro Rotativo (m³/h)']:.2f}')
                col2.metric('Brix do Caldo na Saída do Decantador (º)',
                            f'{Decantador['Decantador']['Brix do Caldo na Saída do Decantador (º)']:.2f}',
                            delta=f'{(((Decantador['Decantador']['Brix do Caldo na Saída do Decantador (º)']/Filto_Rotativo['Filtro Rotativo']['Brix de Saída do Filtro Rotativo (º)'])-1)*100):.2f} %')
                col3.metric('Vazão do Lodo na Saída do Decantador (ton/h)', f'{Decantador['Decantador']['Vazão de Lodo (ton/h)']:.2f}')
                col4.metric('Pureza do Caldo na Saída do Decantador (%)', f'{Decantador['Decantador']['Pureza do Caldo na Saída do Decantador (%)']:.0f}')
        
                # ========== FILTRO PRENSA ==========
                
                st.subheader('Filtro Prensa')
        
                # ---------------- MÉTRICAS ----------------
        
                col1, col2, col3 = st.columns(3)
                col1.metric('Vazão de Filtrado Gerado (ton/h)', f'{Filtro_Prensa['Filtro Prensa']['Vazão de Filtrado (m³/h)']:.2f}')
                col2.metric('Brix do Filtrado (º)', f'{Filtro_Prensa['Filtro Prensa']['Brix do Filtrado (º)']:.2f}')
                col3.metric('Torta Gerada (ton/h)', f'{Filtro_Prensa['Filtro Prensa']['Massa da Torta (ton/h)']:.2f}')
                st.divider()
        
                # ========== PENEIRA ROTATIVA ==========
        
                st.subheader('Peneira Rotativa')
        
                # ---------------- MÉTRICAS ----------------
                
                col1, col2 = st.columns(2)
                col1.metric('Vazão de Caldo na Saída da Peneira Rotativa (m³/h)', f'{Peneira_Rotativa['Peneira Rotativa']['Vazão de Caldo na Saída da Peneira Rotativa (m³/h)']:.2f}',
                            delta=f'{Peneira_Rotativa['Peneira Rotativa']['Vazão de Caldo na Saída da Peneira Rotativa (m³/h)'] - Decantador['Decantador']['Vazão de Caldo na Saída do Decantador (m³/h)']:.2f}')
                col2.metric('Brix do Caldo na Saída da Peneira Rotativa (º)',
                            f'{Peneira_Rotativa['Peneira Rotativa']['Brix de Saída da Peneira Rotativa (º)']:.2f}',
                            delta=f'{(((Peneira_Rotativa['Peneira Rotativa']['Brix de Saída da Peneira Rotativa (º)']/Decantador['Decantador']['Brix do Caldo na Saída do Decantador (º)'])-1)*100):.2f} %')
                st.divider()
        
                # ========== EVAPORADOR ==========
        
                st.subheader('Evaporadores')

                # ---------------- MÉTRICAS ----------------
                col1, col2, col3 = st.columns(3)
                col1.metric('Brix Final (º)', f'{Evaporador['Evaporadores']['Brix Final (º)']}', delta=f"Aumento de {(Evaporador['Evaporadores']['Brix Efeitos (º)'][-1]-Evaporador['Evaporadores']['Brix Efeitos (º)'][0])}", delta_color="off")
                col2.metric('Vazão de Caldo Final (ton/h)',f'{Evaporador['Evaporadores']['Vazão de Caldo em Cada Efeito (kg/h)'][-1]/1000:.2f}', f'Redução de {(Evaporador['Evaporadores']['Vazão de Caldo em Cada Efeito (kg/h)'][0]-Evaporador['Evaporadores']['Vazão de Caldo em Cada Efeito (kg/h)'][-1])/1000:.2f}', delta_color="off")
                col3.metric('VE necessário (ton/h)', f"{Evaporador['Evaporadores']['Injeção de Vapor VE (kg/h)']/1000:.2f}")

                # ---------------- TABELAS ----------------
                num_ef_BC = len(lista_para_calculo)
                evaporadores_labels_BC = ['Inicial'] + [f'Evaporador {i}' for i in range(1, num_ef_BC+1)]

                evaporadores_labels_Vap = [f'Evaporador {i}' for i in range(1, num_ef_BC + 1 )]

                DF_EVAPORADOR = pd.DataFrame({
                    'Evaporador': evaporadores_labels_BC,
                    'Brix (º)': Evaporador['Evaporadores']['Brix Efeitos (º)'],
                    'Vazão de Caldo (kg/h)': Evaporador['Evaporadores']['Vazão de Caldo em Cada Efeito (kg/h)'],
                    'Temperatura do Caldo (ºC)': Evaporador['Evaporadores']['Lista de Temperatura em cada Efeito (ºC)']
                })

                DF_EVAPORADOR_Vap = pd.DataFrame({
                    'Evaporador': evaporadores_labels_Vap,
                    'Entrada de Vapor': Evaporador['Evaporadores']['Lista Vapor Entrada por Efeito (kg/h)'],
                    'Consumo de Vapor': Evaporador['Evaporadores']['Lista Consumo por Efeito (kg/h)'],
                    'Vapor Gerado': Evaporador['Evaporadores']['Lista de Vapores Gerados (kg/h)'],
                    'Vapor Útil': Evaporador['Evaporadores']['Lista de Vapor Útil (kg/h)'],
                    'Sangrias': Evaporador['Evaporadores']['Lista de Sangrias em cada efeito (kg/h)'],
                })

                # ---------------- GRÁFICOS ----------------

                col1, col2 = st.columns(2)

                fig_temp_caldo = px.line(
                    DF_EVAPORADOR, x='Evaporador',
                    y='Vazão de Caldo (kg/h)',
                    title='Vazão do Caldo em cada Efeito',
                    text='Vazão de Caldo (kg/h)'
                )

                fig_temp_caldo.update_traces(textposition='top center', line=dict(color=cor_linha))
                fig_temp_caldo.update_layout(yaxis_range=[0, max(DF_EVAPORADOR['Vazão de Caldo (kg/h)'])*1.2])
                col1.plotly_chart(fig_temp_caldo, use_container_width=True)

                fig_temp_temp = px.line(
                    DF_EVAPORADOR, x='Evaporador',
                    y='Temperatura do Caldo (ºC)',
                    title='Temperatura do Caldo em cada Efeito',
                    text='Temperatura do Caldo (ºC)'
                )

                fig_temp_temp.update_traces(textposition='top center', line=dict(color=cor_linha))
                fig_temp_temp.update_layout(yaxis_range=[0, max(DF_EVAPORADOR['Temperatura do Caldo (ºC)'])*1.2])
                col2.plotly_chart(fig_temp_temp, use_container_width=True)

                fig_temp_brix = px.line(
                    DF_EVAPORADOR, x='Evaporador',
                    y='Brix (º)',
                    title='Brix do Caldo em cada Efeito',
                    text='Brix (º)'
                )

                fig_temp_brix.update_traces(textposition='top center', line=dict(color=cor_linha))
                fig_temp_brix.update_layout(yaxis_range=[0, max(DF_EVAPORADOR['Brix (º)'])*1.2])
                st.plotly_chart(fig_temp_brix, use_container_width=True)

                col1, col2 = st.columns(2)

                fig_temp_vapor = px.bar(
                    DF_EVAPORADOR_Vap, x='Evaporador',
                    y='Entrada de Vapor',
                    title='Entrada de Vapor em cada Efeito',
                    text='Entrada de Vapor',
                    color_discrete_sequence=[cor_barra]
                )

                fig_temp_vapor.update_layout(yaxis_range=[0, max(DF_EVAPORADOR_Vap['Entrada de Vapor'])*1.2])
                fig_temp_vapor.update_traces(textposition='outside')
                col1.plotly_chart(fig_temp_vapor, use_container_width=True)

                fig_temp_Sangria = px.bar(
                    DF_EVAPORADOR_Vap, x='Evaporador',
                    y='Sangrias',
                    title='Sangrias em cada Efeito',
                    text='Sangrias',
                    color_discrete_sequence=[cor_barra]
                )

                fig_temp_Sangria.update_layout(yaxis_range=[0, max(DF_EVAPORADOR_Vap['Sangrias'])*1.2])
                fig_temp_Sangria.update_traces(textposition='outside')
                col2.plotly_chart(fig_temp_Sangria, use_container_width=True)

                st.divider()

                # ========== COZEDORES E CRISTALIZADOR ==========
        
                st.subheader('Fábrica de Açúcar')

                col1, col2, col3 = st.columns(3)
                col1.metric('Açúcar Produzido (ton/h)', f"{fabAcucar['Processo de Cozimento']['Açúcar Produzido (ton/h)']:.2f}")
                col2.metric('Sacas Produzidas por Dia (50 kg)', f"{fabAcucar['Processo de Cozimento']['Sacas Produzidas por Dia (50 kg)']:.2f}")
                col3.metric('SJM (%)', f"{fabAcucar['Processo de Cozimento']['SJM (%)']:.2f}")

                # ---------------- MÉTRICAS ----------------
        
                st.divider()
    
        if 'simulacao_enviada' in st.session_state and st.session_state['simulacao_enviada'] and nivel in ['Destilaria', 'Gestão']:

                    
            Tanque_Mistura = calcular_tanque_mistura(vazao_misto, Brix_misto, Pol_misto, vazao_Mel, Brix_Mel_Final, pureza_Mel_Final)
    
            Fermentacao = calcular_fermentacao(Tanque_Mistura['Tanque de Mistura']['Vazão do Mosto Gerado (ton/h)'],
                                                   Tanque_Mistura['Tanque de Mistura']['Brix do Mosto Gerado (º)'],
                                                   Tanque_Mistura['Tanque de Mistura']['Pureza do Mosto (%)'])
                    
            Destilacao = sistema_destilacaoo_etanol_fundo(Fermentacao['Fermentação']['Vazão do Vinho Fermentado (ton/h)'],
                                                              Fermentacao['Fermentação']['Fração de Etanol Presente no Vinho'],
                                                              frac_fleg_vaptopo, frac_Fleg_vapmeio, frac_Fleg_Liq)
                
            Simulacao = [
                Extracao,
                Tanque_Mistura,
                Fermentacao,
                Destilacao
            ]
                
            st.session_state['Simulacao'] = Simulacao

            Extracao = Simulacao[0]
            Tanque_Mistura = Simulacao[1]
            Fermentacao = Simulacao[2]
            Destilacao = Simulacao[3]
        
            # ========== TANQUE DE MISTURA ==========
            st.header('TANQUE DE MISTURA')
            st.subheader('Mistura de Caldo Misto, Caldo Retorno e Mel Final')
            col1, col2, col3 = st.columns(3)
            col1.metric('Vazão do Mosto (ton/h)', f'{Tanque_Mistura['Tanque de Mistura']['Vazão do Mosto Gerado (ton/h)']:.2f}')
            col2.metric('Brix do Mosto (º)', f'{Tanque_Mistura['Tanque de Mistura']['Brix do Mosto Gerado (º)']:.2f}')
            col3.metric('Pureza do Mosto (%)', f'{Tanque_Mistura['Tanque de Mistura']['Pureza do Mosto (%)']:.2f}')
            st.divider()
        
            # ========== FERMENTAÇÃO ==========
            st.header('FERMENTAÇÃO')
            col1, col2, col3 = st.columns(3)
            col1.metric('Vazão do Vinho Fermentado (ton/h)', f'{Fermentacao['Fermentação']['Vazão do Vinho Fermentado (ton/h)']:.2f}')
            col2.metric('Grau GL do Mosto (º)', f'{Fermentacao['Fermentação']['GL na Dorna (º)']:.2f}')
            col3.metric('Vazão de Etanol no Vinho Fermentado (m³/h)', f'{Fermentacao['Fermentação']['Vazão de Etanol Presente na Dorna (m³/h)']:.2f}')
            st.divider()
        
            # ========== DESTILAÇÃO ==========
            st.header('DESTILAÇÃO')
            st.error('Está sendo revisado o BM e BE.')
            st.subheader("Produtos Finais e Frações de Etanol")
        
            col1, col2, col3 = st.columns(3)
        
            with col1:
                st.metric(label="ETANOL-2 (Fundo D)",
                          value=f"{Destilacao['Destilação']['Produto Final (ETANOL-2 Fundo D)']:.2f} kg/h",
                          delta=f"{Destilacao['Destilação']['Frac Etanol (Fundo D)']:.2%}")
        
            with col2:
                st.metric(label="ETHID (Coluna B)",
                          value=f"{Destilacao['Destilação']['Produto Final (ETHID B)']:.2f} kg/h",
                          delta=f"{Destilacao['Destilação']['Frac Etanol (ETHID B)']:.2%}")
        
            with col3:
                st.metric(label="Resíduos Totais",
                          value=f"{Destilacao['Destilação']['Resíduos Totais']:.2f} kg/h",
                          delta=f"{Destilacao['Destilação']['Frac Etanol Resíduos']:.2%}")
        
            fractions_data = {
                "Corrente": ["ETANOL-2 (Fundo D)", "ETHID (B)", "Resíduos"],
                "Fração de Etanol": [
                    Destilacao['Destilação']['Frac Etanol (Fundo D)'],
                    Destilacao['Destilação']['Frac Etanol (ETHID B)'],
                    Destilacao['Destilação']['Frac Etanol Resíduos']
                ]
            }
        
            fig_frac = px.bar(fractions_data,
                            x="Corrente", y="Fração de Etanol",
                            text=[f"{v:.2%}" for v in fractions_data["Fração de Etanol"]],
                            color="Corrente",
                            title="Fração de Etanol em Cada Corrente")
        
            fig_frac.update_layout(yaxis=dict(tickformat=".0%"))
            st.plotly_chart(fig_frac, use_container_width=True)
        
        if 'simulacao_enviada' in st.session_state and st.session_state['simulacao_enviada'] and nivel in ['Caldeira', 'Gestão']:

            # ------------ Constantes físicas e composição do bagaço ------------
            H_VAPOR = 3314  # kJ/kg
            H_AGUA = 378    # kJ/kg
            DELTA_H_MJ_KG = (H_VAPOR - H_AGUA) / 1000  # MJ/kg
            EFI_CALD3 = 0.531
            EFI_CALD4 = 0.5874

            # ------------ Cálculos ------------
            Caldeira3 = calcular_vapor_e_eletricidade(vazao_bag_cald3,Umid_Bag,EFI_CALD3,DELTA_H_MJ_KG)
            Caldeira4 = calcular_vapor_e_eletricidade(vazao_bag_cald4,Umid_Bag,EFI_CALD4,DELTA_H_MJ_KG)

            Simulacao = [Extracao,
                         Caldeira3,
                         Caldeira4]
            
            st.session_state['Simulacao'] = Simulacao

            Extracao = Simulacao[0]
            Caldeira3 = Simulacao[1]
            Caldeira4 = Simulacao[2]

            st.header('Vapor Gerado pelas Caldeiras')
            col1, col2 = st.columns(2)
            col1.subheader('Caldeira 3')
            col1.metric('Vapor gerado (ton/h)', f'{Caldeira3['Caldeira']['Vazão de Vapor (ton/h)']:.2f}')
            col2.subheader('Caldeira 4')
            col2.metric('Vapor gerado (ton/h)', f'{Caldeira4['Caldeira']['Vazão de Vapor (ton/h)']:.2f}')

            st.divider()

            st.header('Energia gerada pelas Caldeiras')
            col1, col2 = st.columns(2)
            col1.subheader('Caldeira 3')
            col2.subheader('Caldeira 4')
            col11, col12 = col1.columns(2)
            col11.metric('Energia gerada - Cogeração (MW)', f'{Caldeira4['Caldeira']['Potência Elétrica - Cogeração (MW)']:.2f}')
            col12.metric('Energia gerada - Condensação (MW)', f'{Caldeira4['Caldeira']['Potência Elétrica - Condensação (MW)']:.2f}')
            col21, col22 = col2.columns(2)
            col21.metric('Energia gerada - Cogeração (MW)', f'{Caldeira4['Caldeira']['Potência Elétrica - Cogeração (MW)']:.2f}')
            col22.metric('Energia gerada - Condensação (MW)', f'{Caldeira4['Caldeira']['Potência Elétrica - Condensação (MW)']:.2f}')

            st.divider()

        if 'simulacao_enviada' in st.session_state and st.session_state['simulacao_enviada']:
            st.subheader('Salvar Simulação')
            col1, col2 = st.columns(2)
            Nome_Simulacao = col1.text_input('Digite o nome da simulação.', key='nome_simu')
            Salvar_Simulacao = col1.button('Salvar Simulação', key='botao_salvar')
            if Salvar_Simulacao:
                if Nome_Simulacao:
                    try:
                        salvar_dados_csv(DADOS_FILE, st.session_state['Simulacao'], Nome_Simulacao, st.session_state['nivel'])
                        st.success('Simulação salva com sucesso!')
                        # Reset o estado para não exibir o bloco após o salvamento
                        st.session_state['simulacao_enviada'] = True 
                    except Exception as e:
                        st.error(f'Ocorreu um erro ao salvar a simulação: {e}')
                else:
                    st.warning("Por favor, digite um nome para a simulação.")
                        
            col2.write('Deseja fazer uma Análise de Sensibilidade das Simulações?')
            col12, col22 = col2.columns(2)
            Sim_AS = col12.button('Sim')
            Nao_AS = col22.button('Não')
            if Sim_AS:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = 'AS_user'
                st.session_state['nivel'] = 'Análise de Sensibilidade'
                st.session_state['Dados_simulacao_1'] = None
                st.session_state['Dados_simulacao_2'] = None
                st.session_state['simulacao_1'] = None
                st.session_state['simulacao_2'] = None
                st.rerun()
            elif Nao_AS:
                # Também limpa o estado se o usuário não quiser a análise de sensibilidade
                st.session_state['simulacao_enviada'] = False
                pass
        
    if nivel in ['Análise de Sensibilidade']:

        st.subheader('Escolha qual área você deseja realizar a análise de sensibilidade.')
        st.session_state['Área'] = st.selectbox('Escolha a área',
                                                ('Fábrica', 'Destilaria', 'Caldeira'),
                                                index = None)
        if st.session_state['Área'] == None:
            st.warning('Escolha uma área para começar a Análise de Sensibilidade')
        
        df_filtrado = Filtra_area(DADOS_FILE, st.session_state['Área'])

        if 'Área' in st.session_state and st.session_state['Área']:
            st.header('Escolha duas simulações para compará-las.')
            Simulacoes = Lista_Simulacao(df_filtrado)
                
            col1, col2 = st.columns(2)
            st.session_state['simulacao_1'] = col1.selectbox(
                'Escolha a primeira Simulação',
                Simulacoes,
                index = None)
                
            st.session_state['simulacao_2'] = col2.selectbox(
                'Escolha a outra simulação',
                Simulacoes,
                index = None)
            
            Simulacoes_Selecionadas = st.button('Selecionar as Simulações')

            if 'simulacao_1' == None or 'simulacao_2' == None:
                st.warning('Selecione as duas simulações para fazer a análise de sensibilidade.')

            if Simulacoes_Selecionadas and 'simulacao_1' in st.session_state and st.session_state['simulacao_1'] and 'simulacao_2' in st.session_state and st.session_state['simulacao_2']:
                st.session_state['Dados_simulacao_1'] = carregar_simulacao(DADOS_FILE, st.session_state['simulacao_1'])
                st.session_state['Dados_simulacao_2'] = carregar_simulacao(DADOS_FILE, st.session_state['simulacao_2'])

                dados1 = st.session_state['Dados_simulacao_1']
                dados2 = st.session_state['Dados_simulacao_2']

                st.divider()

                st.title('Análise de Sensibilidade')

                # ========== EXTRAÇÃO ==========

                st.header('EXTRAÇÃO')
                if st.session_state['Área'] in ['Fábrica', 'Destilaria', 'Caldeira']:
                    st.subheader('Moenda')
                    col1, col2 = st.columns(2)
                    col11, col12 = col1.columns(2)
                    col11.metric(f'TCH da {st.session_state['simulacao_1']}', dados1['Extração']['Tonelada de Cana por hora'])
                    col12.metric(f'TCH da {st.session_state['simulacao_2']}', dados2['Extração']['Tonelada de Cana por hora'])

                    col21,col22 = col2.columns(2)
                    col21.metric(f'Disponibilidade da {st.session_state['simulacao_1']}', dados1['Extração']['Disponibilidade Geral (h)'],2)
                    col22.metric(f'Disponibilidade da {st.session_state['simulacao_2']}', dados2['Extração']['Disponibilidade Geral (h)'],2)

                    col3, col4 = st.columns(2)
                    col31, col32 = col3.columns(2)
                    col31.metric(f'Vazão de Embebição (m³/h) da {st.session_state['simulacao_1']}', dados1['Extração']['Vazão de Embebição (m³/h)'],2)
                    col32.metric(f'Vazão de Embebição (m³/h) da {st.session_state['simulacao_2']}', dados2['Extração']['Vazão de Embebição (m³/h)'],2)

                    if st.session_state['Área'] in ['Fábrica', 'Destilaria']:
                        col41, col42 = col4.columns(2)
                        col41.metric(f'Vazão de Caldo Primário (m³/h) da {st.session_state['simulacao_1']}', dados1['Extração']['Vazão de Caldo Primário (m³/h)'],2)
                        col42.metric(f'Vazão de Caldo Primário (m³/h) da {st.session_state['simulacao_2']}', dados2['Extração']['Vazão de Caldo Primário (m³/h)'],2)
                    if st.session_state['Área'] in ['Caldeira']:
                        col41, col42 = col4.columns(2)
                        col41.metric(f'Vazão de Caldo Primário (m³/h) da {st.session_state['simulacao_1']}', dados1['Extração']['Vazão de Bagaço (ton/h)'],2)
                        col42.metric(f'Vazão de Caldo Primário (m³/h) da {st.session_state['simulacao_2']}', dados2['Extração']['Vazão de Bagaço (ton/h)'],2)
                
                st.divider()
                if st.session_state['Área'] in ['Fábrica', 'Destilaria']:
                    st.header('TRATAMENTO DE CALDO')

                    aba1, aba2, aba3, aba4, aba5, aba6, aba7 = st.tabs(["Aquecedor", "Sulfitação", "Caleação", "Trocador de Calor", "Balão Flash", "Filtro Rotativo", "Decantador e Filtro Prensa"])

                    # =======================================================
                    # Aquecedor
                    # =======================================================
                    with aba1:
                        st.header('Aquecedores')
                        col1, col2 = st.columns(2)
                        col1.subheader('Velocidade do Caldo')
                        col11, col12 = col1.columns(2)
                        col11.metric(f'Velocidade (m/s) da {st.session_state['simulacao_1']}',
                                    f'{dados1['Aquecedor']['Velocidade (m/s)']:.2f}',
                                    delta=f'{(dados1['Aquecedor']['Velocidade (m/s)'] - 2):.2f}'
                                    if dados1['Aquecedor']['Velocidade (m/s)'] > 2
                                    else f'{(1.5 - dados1['Aquecedor']['Velocidade (m/s)']):.2f}'
                                    if dados1['Aquecedor']['Velocidade (m/s)'] < 1.5 else None, delta_color = 'inverse')
                        col12.metric(f'Velocidade (m/s) da {st.session_state['simulacao_2']}',
                                    f'{dados2['Aquecedor']['Velocidade (m/s)']:.2f}',
                                    delta=f'{(dados2['Aquecedor']['Velocidade (m/s)'] - 2):.2f}'
                                    if dados2['Aquecedor']['Velocidade (m/s)'] > 2
                                    else f'{(1.5 - dados2['Aquecedor']['Velocidade (m/s)']):.2f}'
                                    if dados2['Aquecedor']['Velocidade (m/s)'] < 1.5 else None, delta_color = 'inverse')
                        col2.subheader('Temperatura de saída do caldo')
                        col21,col22 = col2.columns(2)
                        col21.metric(f'Temperatura Final (ºC) da {st.session_state['simulacao_1']}',
                                    f'{dados1['Aquecedor']['Lista de Temperaturas (ºC)'][-1]}',
                                    delta=f'{dados1['Aquecedor']['Lista de Temperaturas (ºC)'][-1] - dados1['Aquecedor']['Lista de Temperaturas (ºC)'][0]:.2f}')
                        col22.metric(f'Temperatura Final (ºC) da {st.session_state['simulacao_2']}',
                                    f'{dados2['Aquecedor']['Lista de Temperaturas (ºC)'][-1]}',
                                    delta=f'{dados2['Aquecedor']['Lista de Temperaturas (ºC)'][-1] - dados2['Aquecedor']['Lista de Temperaturas (ºC)'][0]:.2f}')

                        col3, col4 = st.columns(2)
                        col3.subheader('Perdas de carga')
                        col31, col32 = col3.columns(2)
                        col31.metric(f'Perda de Carga (kgf/cm²) da {st.session_state['simulacao_1']}', f'{dados1['Trocador de Calor']['Lista de Perdas (kgf/cm²)'][-1]:.2f}')
                        col32.metric(f'Perda de Carga (kgf/cm²) da {st.session_state['simulacao_2']}', f'{dados2['Trocador de Calor']['Lista de Perdas (kgf/cm²)'][-1]:.2f}')

                        col4.subheader('Vazão de Fluido Quente')
                        col41, col42 = col4.columns(2)
                        col41.metric(f'Vazão de Aquecimento Total (ton/h) da {st.session_state['simulacao_1']}', f'{dados1['Trocador de Calor']['Calor trocado (kcal)']:.2f}')
                        col42.metric(f'Vazão de Aquecimento Total (ton/h) da {st.session_state['simulacao_2']}', f'{dados2['Trocador de Calor']['Calor trocado (kcal)']:.2f}')

                        # ---------------- DADOS ----------------
                        DF_AQUECEDORES_Comparacao = pd.DataFrame({
                            'Aquecedor': ['Inicial'] + [f'Aquecedor {i}' for i in range(1, len(dados1['Aquecedor']['Lista de Temperaturas (ºC)']))],
                            f'Temperaturas (ºC) da {st.session_state["simulacao_1"]}': dados1['Aquecedor']['Lista de Temperaturas (ºC)'],
                            f'Temperaturas (ºC) da {st.session_state["simulacao_2"]}': dados2['Aquecedor']['Lista de Temperaturas (ºC)'],
                            f'Perdas (kgf/cm²) da {st.session_state["simulacao_1"]}': dados1['Aquecedor']['Lista de Perdas (kgf/cm²)'],
                            f'Perdas (kgf/cm²) da {st.session_state["simulacao_2"]}': dados2['Aquecedor']['Lista de Perdas (kgf/cm²)']
                        })

                        # ---------------- GRÁFICO DE TEMPERATURAS ----------------
                        colunas_temp = [
                            f'Temperaturas (ºC) da {st.session_state["simulacao_1"]}',
                            f'Temperaturas (ºC) da {st.session_state["simulacao_2"]}'
                        ]

                        fig_temp_aq = go.Figure()

                        cores_linhas = ['#103185', "#395DD1"]

                        for i, col in enumerate(colunas_temp):
                            fig_temp_aq.add_trace(go.Scatter(
                                x=DF_AQUECEDORES_Comparacao['Aquecedor'],
                                y=DF_AQUECEDORES_Comparacao[col],
                                mode='lines+markers+text',
                                name=col,
                                text=[f'{v:.2f}' for v in DF_AQUECEDORES_Comparacao[col]],
                                textposition='top center',
                                line=dict(color=cores_linhas[i], width=2)
                            ))

                        max_temp = max(dados1['Aquecedor']['Lista de Temperaturas (ºC)'] + dados2['Aquecedor']['Lista de Temperaturas (ºC)'])
                        fig_temp_aq.update_layout(
                            title='Temperatura dos Aquecedores',
                            yaxis_title='Temperatura (ºC)',
                            yaxis_range=[20, max_temp*1.2],
                            xaxis_title='Aquecedor',
                            legend_title='Simulação',
                            template='plotly_white'
                        )

                        st.plotly_chart(fig_temp_aq, use_container_width=True)

                        # ---------------- GRÁFICO DE PERDAS ----------------
                        colunas_perda = [
                            f'Perdas (kgf/cm²) da {st.session_state["simulacao_1"]}',
                            f'Perdas (kgf/cm²) da {st.session_state["simulacao_2"]}'
                        ]

                        fig_perda_aq = go.Figure()

                        cores_barras = ['#103185', '#395DD1']

                        for i, col in enumerate(colunas_perda):
                            fig_perda_aq.add_trace(go.Bar(
                                x=DF_AQUECEDORES_Comparacao['Aquecedor'],
                                y=DF_AQUECEDORES_Comparacao[col],
                                name=col,
                                marker_color=cores_barras[i],
                                text=[f'{v:.2f}' for v in DF_AQUECEDORES_Comparacao[col]],
                                textposition='auto'
                            ))

                        fig_perda_aq.update_layout(
                            title='Perdas de Pressão nos Aquecedores',
                            yaxis_title='Perdas (kgf/cm²)',
                            xaxis_title='Aquecedor',
                            barmode='group',
                            legend_title='Simulação',
                            template='plotly_white'
                        )

                        st.plotly_chart(fig_perda_aq, use_container_width=True)
                        
                        with st.expander('Tabelas'):
                            st.dataframe(DF_AQUECEDORES_Comparacao, use_container_width=True, hide_index=True)

                        # =======================================================
                        # SULFITAÇÃO
                        # =======================================================

                    with aba2:
                        st.header("Sulfitação")

                        col1, col2 = st.columns(2)
                        col1.subheader('Enxofre Necessário')
                        col11, col12 = col1.columns(2)
                        col11.metric(
                            f"Enxofre necessário (kg/h) - {st.session_state['simulacao_1']}",
                            f"{dados1['Sulfitação']['Vazão de Enxofre (kg/h)']:.2f}",
                            delta=f"{dados1['Sulfitação']['Vazão de Enxofre (kg/h)'] - dados2['Sulfitação']['Vazão de Enxofre (kg/h)']:.2f}"
                        )
                         
                        col12.metric(
                            f"Enxofre necessário (kg/h) - {st.session_state['simulacao_2']}",
                            f"{dados2['Sulfitação']['Vazão de Enxofre (kg/h)']:.2f}"
                        )

                        col2.subheader('Enxofre Necessário')
                        col21, col22 = col2.columns(2)
                        col21.metric(
                            f"O₂ para queima (kg/h) - {st.session_state['simulacao_1']}",
                            f"{dados1['Sulfitação']['Vazão de Oxigênio']:.2f}",
                            delta=f"{dados1['Sulfitação']['Vazão de Oxigênio'] - dados2['Sulfitação']['Vazão de Oxigênio']:.2f}"
                        )

                        col22.metric(
                            f"O₂ para queima (kg/h) - {st.session_state['simulacao_2']}",
                            f"{dados2['Sulfitação']['Vazão de Oxigênio']:.2f}"
                        )

                        # =======================================================
                        # CALEAÇÃO
                        # =======================================================

                    with aba3:
                        st.header("Caleação")
                        col1, col2= st.columns(2)

                        col1.subheader('Cal necessário')
                        col11, col12 = col1.columns(2)
                        col11.metric(
                            f"Cal necessário (kg/h) - {st.session_state['simulacao_1']}",
                            f"{dados1['Caleação']['Vazão de Cal (kg/h)']:.2f}",
                            delta=f"{dados1['Caleação']['Vazão de Cal (kg/h)'] - dados2['Caleação']['Vazão de Cal (kg/h)']:.2f}"
                        )
                        col12.metric(
                            f"Cal necessário (kg/h) - {st.session_state['simulacao_2']}",
                            f"{dados2['Caleação']['Vazão de Cal (kg/h)']:.2f}"
                        )

                        col2.subheader('Água necessária')
                        col21, col22 = col2.columns(2)
                        col21.metric(
                            f"Água diluição (kg/h) - {st.session_state['simulacao_1']}",
                            f"{dados1['Caleação']['Vazão de Água (kg/h)']:.2f}",
                            delta=f"{dados1['Caleação']['Vazão de Água (kg/h)'] - dados2['Caleação']['Vazão de Água (kg/h)']:.2f}"
                        )
                        col22.metric(
                            f"Água diluição (kg/h) - {st.session_state['simulacao_2']}",
                            f"{dados2['Caleação']['Vazão de Água (kg/h)']:.2f}"
                        )

                        # =======================================================
                        # TROCADOR DE CALOR
                        # =======================================================

                    with aba4:
                        st.header("Trocador de Calor")

                        # ---------------- MÉTRICAS ----------------
                        col1, col2 = st.columns(2)

                        col1.subheader('Velocidade do Caldo')
                        col11, col12 = col1.columns(2)
                        col11.metric(
                            f"Velocidade (m/s) - {st.session_state['simulacao_1']}",
                            f"{dados1['Trocador de Calor']['Velocidade (m/s)']:.2f}",
                        )
                        col12.metric(
                            f"Velocidade (m/s) - {st.session_state['simulacao_2']}",
                            f"{dados2['Trocador de Calor']['Velocidade (m/s)']:.2f}",
                        )

                        col2.subheader('Temperatura de saída do caldo')
                        col21, col22 = col2.columns(2)
                        col21.metric(
                            f"Temp Final (°C) - {st.session_state['simulacao_1']}",
                            f"{dados1['Trocador de Calor']['Lista de Temperaturas (ºC)'][-1]:.2f}",
                            delta=f"{dados1['Trocador de Calor']['Lista de Temperaturas (ºC)'][-1] - dados1['Trocador de Calor']['Lista de Temperaturas (ºC)'][0]:.2f}"
                        )
                        col22.metric(
                            f"Temp Final (°C) - {st.session_state['simulacao_2']}",
                            f"{dados2['Trocador de Calor']['Lista de Temperaturas (ºC)'][-1]:.2f}",
                            delta=f"{dados2['Trocador de Calor']['Lista de Temperaturas (ºC)'][-1] - dados2['Trocador de Calor']['Lista de Temperaturas (ºC)'][0]:.2f}"
                        )

                        col3, col4 = st.columns(2)
                        col3.subheader('Perdas de carga')
                        col31, col32 = col3.columns(2)
                        col31.metric(
                            f"Perda Carga (kgf/cm²) - {st.session_state['simulacao_1']}",
                            f"{dados1['Trocador de Calor']['Lista de Perdas (kgf/cm²)'][-1]:.2f}"
                        )
                        col32.metric(
                            f"Perda Carga (kgf/cm²) - {st.session_state['simulacao_2']}",
                            f"{dados2['Trocador de Calor']['Lista de Perdas (kgf/cm²)'][-1]:.2f}"
                        )

                        col4.subheader('Vazão de Fluido Quente')
                        col41, col42 = col4.columns(2)
                        col41.metric(
                            f"Aquecimento Total (ton/h) - {st.session_state['simulacao_1']}",
                            f"{dados1['Trocador de Calor']['Calor trocado (kcal)']:.2f}"
                        )
                        col42.metric(
                            f"Aquecimento Total (ton/h) - {st.session_state['simulacao_2']}",
                            f"{dados2['Trocador de Calor']['Calor trocado (kcal)']:.2f}"
                        )

                        # ---------------- DADOS PARA GRÁFICOS ----------------
                        DF_TROCADOR_Comparacao = pd.DataFrame({
                            "Trocador de Calor": ["Inicial"] + [f"Trocador {i}" for i in range(1, len(dados1['Trocador de Calor']['Lista de Temperaturas (ºC)']))],
                            f"Temperaturas (ºC) - {st.session_state['simulacao_1']}": dados1['Trocador de Calor']['Lista de Temperaturas (ºC)'],
                            f"Temperaturas (ºC) - {st.session_state['simulacao_2']}": dados2['Trocador de Calor']['Lista de Temperaturas (ºC)'],
                            f"Perdas (kgf/cm²) - {st.session_state['simulacao_1']}": dados1['Trocador de Calor']['Lista de Perdas (kgf/cm²)'],
                            f"Perdas (kgf/cm²) - {st.session_state['simulacao_2']}": dados2['Trocador de Calor']['Lista de Perdas (kgf/cm²)']
                        })

                        # ---------------- GRÁFICO DE TEMPERATURA ----------------
                        colunas_temp = [
                            f"Temperaturas (ºC) - {st.session_state['simulacao_1']}",
                            f"Temperaturas (ºC) - {st.session_state['simulacao_2']}"
                        ]
                        fig_temp_aq = go.Figure()
                        cores_linhas = ["#103185", "#395DD1"]

                        for i, col in enumerate(colunas_temp):
                            fig_temp_aq.add_trace(go.Scatter(
                                x=DF_TROCADOR_Comparacao["Trocador de Calor"],
                                y=DF_TROCADOR_Comparacao[col],
                                mode="lines+markers+text",
                                name=col,
                                text=[f"{v:.2f}" for v in DF_TROCADOR_Comparacao[col]],
                                textposition="top center",
                                line=dict(color=cores_linhas[i], width=2)
                            ))

                        max_temp = max(dados1['Trocador de Calor']['Lista de Temperaturas (ºC)'] + dados2['Trocador de Calor']['Lista de Temperaturas (ºC)'])
                        fig_temp_aq.update_layout(
                            title="Temperatura dos Trocadores de Calor",
                            yaxis_title="Temperatura (ºC)",
                            yaxis_range=[20, max_temp*1.2],
                            xaxis_title="Trocador de Calor",
                            legend_title="Simulação",
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_temp_aq, use_container_width=True)

                        # ---------------- GRÁFICO DE PERDAS ----------------
                        colunas_perda = [
                            f"Perdas (kgf/cm²) - {st.session_state['simulacao_1']}",
                            f"Perdas (kgf/cm²) - {st.session_state['simulacao_2']}"
                        ]
                        fig_perda_aq = go.Figure()
                        cores_barras = ["#103185", "#395DD1"]

                        for i, col in enumerate(colunas_perda):
                            fig_perda_aq.add_trace(go.Bar(
                                x=DF_TROCADOR_Comparacao["Trocador de Calor"],
                                y=DF_TROCADOR_Comparacao[col],
                                name=col,
                                marker_color=cores_barras[i],
                                text=[f"{v:.2f}" for v in DF_TROCADOR_Comparacao[col]],
                                textposition="auto"
                            ))

                        fig_perda_aq.update_layout(
                            title="Perdas de Pressão nos Trocadores de Calor",
                            yaxis_title="Perdas (kgf/cm²)",
                            xaxis_title="Trocador de Calor",
                            yaxis_range=[0, DF_TROCADOR_Comparacao[col]*1.2],
                            barmode="group",
                            legend_title="Simulação",
                            template="plotly_white"
                        )
                        st.plotly_chart(fig_perda_aq, use_container_width=True)
                        with st.expander('Tabelas'):
                            st.dataframe(DF_TROCADOR_Comparacao, use_container_width=True, hide_index=True)

                    # =======================================================
                    # BALÃO FLASH
                    # =======================================================

                    with aba5:
                        st.header('Balão Flash')

                        col1, col2 = st.columns(2)
                        col1.subheader('Vazão de Saída')
                        col11, col12 = col1.columns(2)
                        col11.metric(f"Vazão Saída (m³/h) — {st.session_state['simulacao_1']}", f"{dados1['Balão Flash']['Vazão de Saída do Balão Flash (m³/h)']:.2f}")
                        col12.metric(f"Vazão Saída (m³/h) — {st.session_state['simulacao_2']}", f"{dados2['Balão Flash']['Vazão de Saída do Balão Flash (m³/h)']:.2f}")

                        col2.subheader('Brix de Saída')
                        col21, col22 = col2.columns(2)
                        col21.metric(f"Brix Saída (º) — {st.session_state['simulacao_1']}", f"{dados1['Balão Flash']['Brix de Saída do Balão Flash (º)']:.2f}")
                        col22.metric(f"Brix Saída (º) — {st.session_state['simulacao_2']}", f"{dados2['Balão Flash']['Brix de Saída do Balão Flash (º)']:.2f}")


                    # =======================================================
                    # FILTRO ROTATIVO
                    # =======================================================

                    with aba6:
                        st.header('Filtro Rotativo')

                        col1, col2 = st.columns(2)
                        col1.subheader('Vazão de Saída')
                        col11, col12 = col1.columns(2)
                        col11.metric(f"Vazão de Filtrado (m³/h) — {st.session_state['simulacao_1']}", f"{dados1['Filtro Rotativo']['Vazão de Saída do Filtro Rotativo (m³/h)']:.2f}")
                        col12.metric(f"Vazão de Filtrado (m³/h) — {st.session_state['simulacao_2']}", f"{dados2['Filtro Rotativo']['Vazão de Saída do Filtro Rotativo (m³/h)']:.2f}")

                        col2.subheader('Brix de Saída')
                        col21, col22 = col2.columns(2)
                        col21.metric(f"Brix do Caldo na Saída do Filtro Rotativo (º)  — {st.session_state['simulacao_1']}", f"{dados1['Filtro Rotativo']['Brix de Saída do Filtro Rotativo (º)']:.2f}")
                        col22.metric(f"Brix do Caldo na Saída do Filtro Rotativo (º) — {st.session_state['simulacao_2']}", f"{dados2['Filtro Rotativo']['Brix de Saída do Filtro Rotativo (º)']:.2f}")

                    # =======================================================
                    # DECANTADOR E FILTRO PRENSA
                    # =======================================================

                    with aba7:
                        st.header('Decantador e Filtro Prensa')
                        
                        st.subheader('DECANTADOR')
                        col1, col2 = st.columns(2)
                        col1.subheader('Vazão de saída')
                        col11, col12 = col1.columns(2)
                        col11.metric(f'Vazão de Caldo na Saída do Decantador (ton/h) — {st.session_state['simulacao_1']}', f'{dados1['Decantador']['Vazão de Caldo na Saída do Decantador (m³/h)']:.2f}')
                        col12.metric(f'Vazão de Caldo na Saída do Decantador (ton/h) — {st.session_state['simulacao_2']}', f'{dados2['Decantador']['Vazão de Caldo na Saída do Decantador (m³/h)']:.2f}')
                        
                        col2.subheader('Brix de saída')
                        col21, col22 = col2.columns(2)
                        col21.metric(f'Brix do Caldo na Saída do Decantador (º) — {st.session_state['simulacao_1']}', f'{dados1['Decantador']['Brix do Caldo na Saída do Decantador (º)']:.2f}')
                        col22.metric(f'Brix do Caldo na Saída do Decantador (º) — {st.session_state['simulacao_2']}', f'{dados2['Decantador']['Brix do Caldo na Saída do Decantador (º)']:.2f}')
                        
                        col3, col4 = st.columns(2)
                        col3.subheader('Vazão de saída')
                        col31, col32 = col3.columns(2)
                        col31.metric(f'Vazão do Lodo na Saída do Decantador (ton/h) — {st.session_state['simulacao_1']}', f'{dados1['Decantador']['Vazão de Lodo (ton/h)']:.2f}')
                        col32.metric(f'Vazão do Lodo na Saída do Decantador (ton/h) — {st.session_state['simulacao_2']}', f'{dados2['Decantador']['Vazão de Lodo (ton/h)']:.2f}')
                        
                        col4.subheader('Pureza do caldo')
                        col41, col42 = col4.columns(2)
                        col41.metric(f'Pureza do Caldo na Saída do Decantador (%) — {st.session_state['simulacao_1']}', f'{dados1['Decantador']['Pureza do Caldo na Saída do Decantador (%)']:.0f}')
                        col42.metric(f'Pureza do Caldo na Saída do Decantador (%) — {st.session_state['simulacao_2']}', f'{dados2['Decantador']['Pureza do Caldo na Saída do Decantador (%)']:.0f}')

                        st.subheader('FILTRO PRENSA')
                        
                        col1, col2, col3 = st.columns(3)
                        
                        col1.subheader('Vazão de Saída')
                        col2.subheader('Brix de saída')
                        col3.subheader('Torta Gerada')
                        col11, col12 = col1.columns(2)
                        col11.metric(f'Vazão de Filtrado Gerado (ton/h) — {st.session_state['simulacao_1']}', f'{dados1['Filtro Prensa']['Vazão de Filtrado (m³/h)']:.2f}')
                        col12.metric(f'Vazão de Filtrado Gerado (ton/h) — {st.session_state['simulacao_2']}', f'{dados2['Filtro Prensa']['Vazão de Filtrado (m³/h)']:.2f}')
                        
                        col21, col22 = col2.columns(2)
                        col21.metric(f'Brix do Filtrado (º) — {st.session_state['simulacao_1']}', f'{dados1['Filtro Prensa']['Brix do Filtrado (º)']:.2f}')
                        col22.metric(f'Brix do Filtrado (º) — {st.session_state['simulacao_2']}', f'{dados2['Filtro Prensa']['Brix do Filtrado (º)']:.2f}')

                        col31, col32 = col3.columns(2)
                        col31.metric(f'Torta Gerada (ton/h) — {st.session_state['simulacao_1']}', f'{dados1['Filtro Prensa']['Massa da Torta (ton/h)']:.2f}')
                        col32.metric(f'Torta Gerada (ton/h)  — {st.session_state['simulacao_2']}', f'{dados2['Filtro Prensa']['Massa da Torta (ton/h)']:.2f}')

                    st.divider()

                    st.header('CONCENTRAÇÃO DO CALDO')

                    # =======================================================
                    # Evaporadores
                    # =======================================================

                    st.subheader('Evaporadores')

                    # ---------------- MÉTRICAS ----------------

                    agua_evap_total_1 = dados1['Evaporadores']['Vazões de Caldo (ton/h)'][0] - dados1['Evaporadores']['Vazões de Caldo (ton/h)'][-1]
                    agua_evap_total_2 = dados2['Evaporadores']['Vazões de Caldo (ton/h)'][0] - dados2['Evaporadores']['Vazões de Caldo (ton/h)'][-1]
                    cond1 = sum(dados1['Evaporadores']['Lista de Vapor Condensado no Efeito (ton/h)'])
                    cond2 = sum(dados2['Evaporadores']['Lista de Vapor Condensado no Efeito (ton/h)'])

                    col1, col2 = st.columns(2)
                    col1.subheader('Vazão de saída')
                    col11, col12 = col1.columns(2)
                    col11.metric(f"Vazão Saída (m³/h) — {st.session_state['simulacao_1']}", f"{dados1['Evaporadores']['Vazões de Caldo (ton/h)'][-1]:.2f}",
                                delta=f"{dados1['Evaporadores']['Vazões de Caldo (ton/h)'][-1] - dados1['Evaporadores']['Vazões de Caldo (ton/h)'][0]:.2f}")
                    col12.metric(f"Vazão Saída (m³/h) — {st.session_state['simulacao_2']}", f"{dados2['Evaporadores']['Vazões de Caldo (ton/h)'][-1]:.2f}",
                                delta=f"{dados2['Evaporadores']['Vazões de Caldo (ton/h)'][-1] - dados2['Evaporadores']['Vazões de Caldo (ton/h)'][0]:.2f}")
                    col2.subheader('Brix de saída')
                    col21, col22 = col2.columns(2)
                    col21.metric(f"Brix Final (º) — {st.session_state['simulacao_1']}", f"{dados1['Evaporadores']['Lista dos Brix do Caldo (º)'][-1]:.2f}",
                                delta=f"{((dados1['Evaporadores']['Lista dos Brix do Caldo (º)'][-1]/dados1['Evaporadores']['Lista dos Brix do Caldo (º)'][0]-1)*100):.2f} %")
                    col22.metric(f"Brix Final (º) — {st.session_state['simulacao_2']}", f"{dados2['Evaporadores']['Lista dos Brix do Caldo (º)'][-1]:.2f}",
                                delta=f"{((dados2['Evaporadores']['Lista dos Brix do Caldo (º)'][-1]/dados2['Evaporadores']['Lista dos Brix do Caldo (º)'][0]-1)*100):.2f} %")

                    col3, col4 = st.columns(2)
                    col3.subheader('Água evaporada')
                    col31, col32 = col3.columns(2)
                    col31.metric(f"Água Evaporada (ton/h) — {st.session_state['simulacao_1']}", f"{agua_evap_total_1:.2f}")
                    col32.metric(f"Água Evaporada (ton/h) — {st.session_state['simulacao_2']}", f"{agua_evap_total_2:.2f}")

                    col4.subheader('Condensado')
                    col41, col42 = col4.columns(2)
                    col41.metric(f"Condensado Total (ton/h) — {st.session_state['simulacao_1']}", f"{cond1:.2f}")
                    col42.metric(f"Condensado Total (ton/h) — {st.session_state['simulacao_2']}", f"{cond2:.2f}")

                    # ---------------- TABELAS ----------------

                    st.write()

                    evaporadores_labels_comparacao = ['Inicial'] + [f'Evaporador {i}' for i in range(1, len(dados1['Evaporadores']['Lista das Pressões no Efeito (kgf/cm²)']))]

                    DF_EVAPORADOR_COMPARACAO_PERDAS = pd.DataFrame({
                        'Evaporador': evaporadores_labels_comparacao,
                        f'Queda de pressão (kgf/cm²) - {st.session_state['simulacao_1']}': dados1['Evaporadores']['Lista das Quedas de Pressão (kgf/cm²)'],
                        f'Pressão no Efeito (kgf/cm²) - {st.session_state['simulacao_1']}': dados1['Evaporadores']['Lista das Pressões no Efeito (kgf/cm²)'],
                        f'Queda de pressão (kgf/cm²) - {st.session_state['simulacao_2']}': dados2['Evaporadores']['Lista das Quedas de Pressão (kgf/cm²)'],
                        f'Pressão no Efeito (kgf/cm²) - {st.session_state['simulacao_2']}': dados2['Evaporadores']['Lista das Pressões no Efeito (kgf/cm²)']
                    })

                    DF_EVAPORADOR_COMPARACAO_PERDAS['Evaporador'] = pd.Categorical(
                        DF_EVAPORADOR_COMPARACAO_PERDAS['Evaporador'],
                        categories=['Inicial'] + [f'Evaporador {i}' for i in range(1, len(dados1['Evaporadores']['Lista das Pressões no Efeito (kgf/cm²)']))],
                        ordered=True
                    )
                    
                    DF_EVAPORADOR_COMPARACAO_CALDO = pd.DataFrame({
                        'Evaporador': evaporadores_labels_comparacao,
                        f'Vazão do Caldo (m³/h) - {st.session_state['simulacao_1']}': dados1['Evaporadores']['Vazões de Caldo (ton/h)'],
                        f'Brix do Caldo (º) - {st.session_state['simulacao_1']}': dados1['Evaporadores']['Lista dos Brix do Caldo (º)'],
                        f'Cp do Caldo - {st.session_state['simulacao_1']}': dados1['Evaporadores']['Lista das Capacidades Caloríficas do Caldo (kcal/kg.ºC)'],
                        f'Elevação do Ponto de Ebulição (ºC) - {st.session_state['simulacao_1']}': dados1['Evaporadores']['Elevação do Ponto de Ebulição (ºC)'],
                        f'Temperatura do Caldo (ºC) - {st.session_state['simulacao_1']}': dados1['Evaporadores']['Lista de Temperaturas do Caldo no Efeito (ºC)'],
                        f'Vazão do Caldo (m³/h) - {st.session_state['simulacao_2']}': dados2['Evaporadores']['Vazões de Caldo (ton/h)'],
                        f'Brix do Caldo (º) - {st.session_state['simulacao_2']}': dados2['Evaporadores']['Lista dos Brix do Caldo (º)'],
                        f'Cp do Caldo - {st.session_state['simulacao_2']}': dados2['Evaporadores']['Lista das Capacidades Caloríficas do Caldo (kcal/kg.ºC)'],
                        f'Elevação do Ponto de Ebulição (ºC) - {st.session_state['simulacao_2']}': dados2['Evaporadores']['Elevação do Ponto de Ebulição (ºC)'],
                        f'Temperatura do Caldo (ºC) - {st.session_state['simulacao_2']}': dados2['Evaporadores']['Lista de Temperaturas do Caldo no Efeito (ºC)'],
                    })

                    DF_EVAPORADOR_COMPARACAO_CALDO['Evaporador'] = pd.Categorical(
                        DF_EVAPORADOR_COMPARACAO_CALDO['Evaporador'],
                        categories=['Inicial'] + [f'Evaporador {i}' for i in range(1, len(dados1['Evaporadores']['Lista das Pressões no Efeito (kgf/cm²)']))],
                        ordered=True
                    )

                    DF_EVAPORADOR_COMPARACAO_VAPOR = pd.DataFrame({
                        'Evaporador': evaporadores_labels_comparacao,
                        'Vapor Útil (ton/h)': dados1['Evaporadores']['Lista de Vapor Útil no efeito (ton/h)'],
                        'Vapor no Efeito (ton/h)': dados1['Evaporadores']['Lista dos Vapor presentes no efeito (ton/h)'],
                        'Vapor Gerado (ton/h)': dados1['Evaporadores']['Lista de Vapor Gerado no Efeito (ton/h)'],
                        'Vapor Sangria (ton/h)': dados1['Evaporadores']['Lista das Sangrias Geradas no Efeito (ton/h)'],
                        'Vapor Flash (ton/h)': dados1['Evaporadores']['Lista do Vapor Gerado por Flash no Efeito (ton/h)']
                    })

                    DF_EVAPORADOR_COMPARACAO_VAPOR['Evaporador'] = pd.Categorical(
                        DF_EVAPORADOR_COMPARACAO_VAPOR['Evaporador'],
                        categories=['Inicial'] + [f'Evaporador {i}' for i in range(1, len(dados1['Evaporadores']['Lista das Pressões no Efeito (kgf/cm²)']))],
                        ordered=True
                    )

                    # ---------------- COLUNAS PARA OS GRÁFICOS ----------------

                    colunas_evap_perdas_efeito = [
                        f'Pressão no Efeito (kgf/cm²) - {st.session_state['simulacao_1']}',
                        f'Pressão no Efeito (kgf/cm²) - {st.session_state['simulacao_2']}',
                    ]

                    colunas_evap_perdas_atual = [
                        f'Queda de pressão (kgf/cm²) - {st.session_state['simulacao_1']}',
                        f'Queda de pressão (kgf/cm²) - {st.session_state['simulacao_2']}'
                    ]

                    colunas_evap_vazao = [
                        f'Vazão do Caldo (m³/h) - {st.session_state['simulacao_1']}',
                        f'Vazão do Caldo (m³/h) - {st.session_state['simulacao_2']}'
                    ]

                    
                    colunas_evap_temp = [
                        f'Temperatura do Caldo (ºC) - {st.session_state['simulacao_1']}',
                        f'Temperatura do Caldo (ºC) - {st.session_state['simulacao_2']}'
                    ]

                    colunas_evap_brix = [
                        f'Brix do Caldo (º) - {st.session_state['simulacao_1']}',
                        f'Brix do Caldo (º) - {st.session_state['simulacao_2']}',
                    ]

                    # ---------------- GRÁFICOS ----------------

                    fig_perdas_evap_efeito = go.Figure()

                    for i, col in enumerate(colunas_evap_perdas_efeito):
                        fig_perdas_evap_efeito.add_trace(go.Bar(
                            x=DF_EVAPORADOR_COMPARACAO_PERDAS['Evaporador'],
                            y=DF_EVAPORADOR_COMPARACAO_PERDAS[col],
                            name=col,
                            marker_color=cores_barras[i],
                            text=[f'{v:.2f}' for v in DF_EVAPORADOR_COMPARACAO_PERDAS[col]],
                            textposition='auto'
                        ))

                    fig_perdas_evap_efeito.update_layout(
                        title='Perdas de Pressão nos Aquecedores',
                        yaxis_title='Perdas (kgf/cm²)',
                        xaxis_title='Evaporador',
                        barmode='group',
                        legend_title='Simulação',
                        template='plotly_white'
                    )
                    
                    fig_perdas_evap_atual = go.Figure()

                    for i, col in enumerate(colunas_evap_perdas_atual):
                        fig_perdas_evap_atual.add_trace(go.Bar(
                            x=DF_EVAPORADOR_COMPARACAO_PERDAS['Evaporador'],
                            y=DF_EVAPORADOR_COMPARACAO_PERDAS[col],
                            name=col,
                            marker_color=cores_barras[i],
                            text=[f'{v:.2f}' for v in DF_EVAPORADOR_COMPARACAO_PERDAS[col]],
                            textposition='auto'
                        ))

                    fig_perdas_evap_atual.update_layout(
                        title='Perdas de Pressão nos Aquecedores',
                        yaxis_title='Perdas (kgf/cm²)',
                        xaxis_title='Evaporador',
                        barmode='group',
                        legend_title='Simulação',
                        template='plotly_white'
                    )

                    fig_vazao_evap = go.Figure()

                    for i, col in enumerate(colunas_evap_vazao):
                        fig_vazao_evap.add_trace(go.Scatter(
                            x=DF_EVAPORADOR_COMPARACAO_CALDO['Evaporador'],
                            y=DF_EVAPORADOR_COMPARACAO_CALDO[col],
                            name=col,
                            line=dict(color=cores_linhas[i]),
                            text=[f'{v:.2f}' for v in DF_EVAPORADOR_COMPARACAO_CALDO[col]],
                            mode='lines+markers+text',
                            textposition='top center'
                        ))

                    fig_vazao_evap.update_layout(
                        title='Perdas de Pressão nos Aquecedores',
                        yaxis_title='Perdas (kgf/cm²)',
                        xaxis_title='Evaporador',
                        barmode='group',
                        legend_title='Simulação',
                        template='plotly_white'
                    )

                    fig_temp_evap = go.Figure()

                    for i, col in enumerate(colunas_evap_temp):
                        fig_temp_evap.add_trace(go.Scatter(
                            x=DF_EVAPORADOR_COMPARACAO_CALDO['Evaporador'],
                            y=DF_EVAPORADOR_COMPARACAO_CALDO[col],
                            name=col,
                            line=dict(color=cores_linhas[i]),
                            text=[f'{v:.2f}' for v in DF_EVAPORADOR_COMPARACAO_CALDO[col]],
                            mode='lines+markers+text',
                            textposition='top center'
                        ))

                    fig_temp_evap.update_layout(
                        title='Perdas de Pressão nos Aquecedores',
                        yaxis_title='Perdas (kgf/cm²)',
                        xaxis_title='Evaporador',
                        barmode='group',
                        legend_title='Simulação',
                        template='plotly_white'
                    )
                    
                    fig_brix_evap = go.Figure()

                    for i, col in enumerate(colunas_evap_brix):
                        fig_brix_evap.add_trace(go.Scatter(
                            x=DF_EVAPORADOR_COMPARACAO_CALDO['Evaporador'],
                            y=DF_EVAPORADOR_COMPARACAO_CALDO[col],
                            name=col,
                            line=dict(color=cores_linhas[i]),
                            text=[f'{v:.2f}' for v in DF_EVAPORADOR_COMPARACAO_CALDO[col]],
                            mode='lines+markers+text',
                            textposition='top center'
                        ))

                    fig_brix_evap.update_layout(
                        title='Perdas de Pressão nos Aquecedores',
                        yaxis_title='Perdas (kgf/cm²)',
                        xaxis_title='Evaporador',
                        barmode='group',
                        legend_title='Simulação',
                        template='plotly_white'
                    )

                    col1, col2 = st.columns(2)
                    col1.plotly_chart(fig_perdas_evap_atual, use_container_width=True)
                    col1.plotly_chart(fig_vazao_evap, use_container_width=True)
                    col2.plotly_chart(fig_perdas_evap_efeito, use_container_width=True)
                    col2.plotly_chart(fig_temp_evap, use_container_width=True)

                    st.plotly_chart(fig_brix_evap, use_container_width=True)

                    # ---------------- VISUALIZAÇÃO DAS TABELAS ----------------

                    with st.expander('Tabelas'):
                        st.dataframe(DF_EVAPORADOR_COMPARACAO_CALDO, use_container_width=True, hide_index=True)
                        st.dataframe(DF_EVAPORADOR_COMPARACAO_PERDAS, use_container_width=True, hide_index=True)

        st.divider()

    logout = st.button('Logout', key='logout_top')
    if logout:
        st.session_state['lista_evaporadores_original'] = [3500, 2500, 2000, 1000, 1000, 1000]
        st.session_state['autenticado'] = False
        st.session_state['usuario'] = None
        st.session_state['nivel'] = None
        st.session_state['Simulacao'] = None
        st.session_state['simulacao_enviada'] = False
        st.session_state['Dados_simulacao_1'] = None
        st.session_state['Dados_simulacao_2'] = None
        st.session_state['simulacao_1'] = None
        st.session_state['simulacao_2'] = None
        st.rerun()