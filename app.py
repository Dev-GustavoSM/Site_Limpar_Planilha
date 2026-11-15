import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import io
import threading
import csv

# ==========================================
# 1. CONFIGURAÇÃO E TRAVA DE FILA DO SERVIDOR
# ==========================================
st.set_page_config(page_title="DataCleaner Universal", page_icon="📊", layout="centered")

@st.cache_resource
def obter_trava_fila():
    return threading.Lock()

fila_servidor = obter_trava_fila()

# ==========================================
# 2. GERENCIAMENTO DE TOKENS E PLANOS
# ==========================================
TOKENS_BASICO_10_REAIS = ["BASICO_10_001", "BASICO_10_002"]
TOKENS_PRO_COM_IA = ["PRO_IA_001", "PRO_IA_002"]

if "usos_gratuitos" not in st.session_state:
    st.session_state["usos_gratuitos"] = 0
if "plano_atual" not in st.session_state:
    st.session_state["plano_atual"] = "Gratuito"

# ==========================================
# 3. BARRA LATERAL: LOGIN E TABELA DE PREÇOS
# ==========================================
with st.sidebar:
    st.header("🔑 Acesso & Planos")
    token_input = st.text_input("Insira seu Token de Acesso:", type="password")
    
    if st.button("Validar Token"):
        if token_input in TOKENS_PRO_COM_IA:
            st.session_state["plano_atual"] = "Pro (Com IA)"
            st.success("Plano Pro ativado! (Limpeza Avançada + IA liberados)")
        elif token_input in TOKENS_BASICO_10_REAIS:
            st.session_state["plano_atual"] = "Básico (R$ 10/mês)"
            st.success("Plano Básico ativado! (Limpeza Avançada Python)")
        else:
            st.error("Token inválido ou expirado.")

    st.info(f"**Seu Plano Atual:** {st.session_state['plano_atual']}")
    if st.session_state["plano_atual"] == "Gratuito":
        restantes = max(0, 5 - st.session_state["usos_gratuitos"])
        st.write(f"Testes gratuitos restantes: **{restantes}/5**")

    st.divider()
    st.subheader("💎 Nossos Planos")
    st.markdown("""
    * **Gratuito:** Até 5 planilhas (Máx. 2.000 linhas). Limpeza estrutural padrão.
    * **Básico (R$ 10/mês):** Uso contínuo sem IA (Máx. 10.000 linhas). Organização profissional por colunas.
    * **Pro (Mensal com IA):** Inclui TUDO do Básico + **Consultoria com Inteligência Artificial** analisando 10 linhas de amostra (Máx. 10.000 linhas).
    
    *Para assinar, faça o Pix e envie o comprovante no WhatsApp para receber o seu token.*
    """)

# ==========================================
# 4. INTERFACE PRINCIPAL E AVISO JURÍDICO
# ==========================================
st.title("📊 DataCleaner Universal")
st.write("Automatize a limpeza e organização de planilhas corporativas com segurança e velocidade.")

st.warning("""
⚠️ **Aviso Importante & Termos de Uso:**  
Esta plataforma é uma ferramenta de auxílio à produtividade. A Inteligência Artificial e os algoritmos analisam padrões para sugerir melhorias, mas **podem ocorrer imprecisões**.  
- Sempre mantenha uma cópia de segurança do seu arquivo original.
- A revisão e conferência final dos dados tratados são de inteira responsabilidade do usuário.
""")

aceitou_termos = st.checkbox("Li e concordo que a ferramenta é um auxílio e revisarei os dados finais.")

modo_execucao = "Com IA"
if st.session_state["plano_atual"] == "Pro (Com IA)":
    modo_execucao = st.radio("Escolha o modo para esta planilha:", ["Com IA (Diagnóstico Inteligente)", "Apenas Limpeza Avançada Python"])

# ==========================================
# 5. UPLOAD E LEITURA INTELIGENTE DE COLUNAS
# ==========================================
arquivo = st.file_uploader("Envie sua planilha (CSV ou Excel)", type=["csv", "xlsx", "xls"])

if arquivo and aceitou_termos:
    plano = st.session_state["plano_atual"]
    
    if plano == "Gratuito" and st.session_state["usos_gratuitos"] >= 5:
        st.error("🔒 Você atingiu o limite de 5 planilhas gratuitas. Assine o Plano Básico ou Pro na barra lateral para continuar.")
        st.stop()

    limite_linhas = 2000 if plano == "Gratuito" else 10000

    try:
        if arquivo.name.endswith(".csv"):
            conteudo_bytes = arquivo.read()
            arquivo.seek(0)
            
            try:
                texto_linhas = conteudo_bytes.decode('utf-8-sig').splitlines()
            except:
                texto_linhas = conteudo_bytes.decode('latin-1').splitlines()

            amostra_texto = "\n".join(texto_linhas[:10])
            delimitador = ','
            try:
                dialecto = csv.Sniffer().sniff(amostra_texto, delimiters=',;')
                delimitador = dialecto.delimiter
            except:
                if ';' in amostra_texto:
                    delimitador = ';'

            leitor = csv.reader(texto_linhas, delimiter=delimitador)
            linhas_dados = list(leitor)
            
            if len(linhas_dados) > 1:
                cabecalho = linhas_dados[0]
                corpo = linhas_dados[1:]
                df = pd.DataFrame(corpo, columns=cabecalho)
            else:
                df = pd.read_csv(arquivo, sep=delimitador, engine='python')
        else:
            df = pd.read_excel(arquivo)
            
    except Exception as e:
        st.error(f"Erro ao ler o arquivo. Verifique se não está corrompido. Detalhe: {e}")
        st.stop()

    total_linhas, total_colunas = df.shape

    # Se ainda assim vier condensado em 1 coluna só, força a quebra por vírgula
    if total_colunas <= 1 and len(df) > 0:
        st.warning("⚠️ Detectamos um arquivo condensado. Reorganizando colunas à força...")
        coluna_unica = df.columns[0]
        dados_divididos = df[coluna_unica].astype(str).str.split(r'[,;]', expand=True)
        if len(dados_divididos.columns) > 1:
            dados_divididos.columns = dados_divididos.iloc[0]
            df = dados_divididos[1:].reset_index(drop=True)
            total_linhas, total_colunas = df.shape

    st.write(f"📄 **Arquivo carregado:** {total_linhas} linhas e {total_colunas} colunas estruturadas.")

    if total_linhas > limite_linhas:
        st.error(f"🚫 **Limite Excedido:** Seu plano suporta até **{limite_linhas:,} linhas**. Este arquivo possui **{total_linhas:,} linhas**.")
        st.stop()

    # ==========================================
    # 6. PROCESSAMENTO E LIMPEZA ESTRUTURAL AVANÇADA
    # ==========================================
    if st.button("🚀 Iniciar Limpeza e Organização"):
        with st.spinner("Aguardando fila do servidor e organizando dados..."):
            with fila_servidor:
                linhas_antes = len(df)
                relatorio_mudancas = []

                # Faxina inicial de colunas fantasma
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

                # 1. Remove linhas e colunas totalmente vazias
                df_limpo = df.dropna(how="all").dropna(axis=1, how="all")
                vazias_removidas = linhas_antes - len(df_limpo)
                if vazias_removidas > 0:
                    relatorio_mudancas.append(f"🗑️ Removidas **{vazias_removidas}** linhas totalmente vazias.")

                # 2. Remove duplicatas exatas
                antes_dup = len(df_limpo)
                df_limpo = df_limpo.drop_duplicates()
                duplicadas_removidas = antes_dup - len(df_limpo)
                if duplicadas_removidas > 0:
                    relatorio_mudancas.append(f"🔁 Removidas **{duplicadas_removidas}** linhas duplicadas.")

                # 3. Limpeza e alinhamento de texto em cada célula
                colunas_formatadas = 0
                for col in df_limpo.columns:
                    novo_nome_col = str(col).strip()
                    if novo_nome_col != str(col):
                        df_limpo.rename(columns={col: novo_nome_col}, inplace=True)
                    
                    if df_limpo[col].dtype == 'object':
                        df_limpo[col] = df_limpo[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
                        df_limpo[col] = df_limpo[col].replace({'nan': None, 'None': None, '': None})
                        colunas_formatadas += 1

                if colunas_formatadas > 0:
                    relatorio_mudancas.append(f"🧹 Alinhamento e estruturação aplicados em **{colunas_formatadas}** colunas.")

                if plano == "Gratuito":
                    st.session_state["usos_gratuitos"] += 1

                st.success("✅ Limpeza e organização estrutural concluídas!")
                st.subheader("📋 Relatório de Organização:")
                for mudanca in relatorio_mudancas:
                    st.markdown(f"- {mudanca}")

                # --- CONSULTORIA DA IA (Apenas se for Pro e escolheu o modo com IA) ---
                usa_ia = (plano == "Pro (Com IA)" and "Com IA" in modo_execucao)
                
                if usa_ia:
                    st.subheader("🤖 Diagnóstico Inteligente da IA (Amostra de 10 Linhas)")
                    try:
                        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                        modelo = genai.GenerativeModel("gemini-1.5-flash")

                        amostra_texto_ia = df_limpo.head(10).to_markdown(index=False)
                        
                        prompt = f"""
                        Você é um analista de qualidade de dados. Analise o cabeçalho e as 10 primeiras linhas desta planilha abaixo.
                        Identifique possíveis problemas de padronização e dê recomendações curtas e diretas do que o usuário deve revisar.
                        Dados:
                        {amostra_texto_ia}
                        """
                        
                        resposta = modelo.generate_content(prompt)
                        st.info(resposta.text)
                    except Exception as e:
                        st.warning("⚠️ Não foi possível conectar à IA, mas a organização avançada foi concluída.")

                # --- PREPARAÇÃO PARA DOWNLOAD (CSV ou Excel) ---
                st.divider()
                st.subheader("📥 Exportar Planilha Organizada")
                tipo_saida = st.radio("Escolha o formato para baixar:", ["CSV", "Excel (.xlsx)"], horizontal=True)

                if tipo_saida == "CSV":
                    buffer = io.BytesIO()
                    df_limpo.to_csv(buffer, index=False, encoding="utf-8-sig")
                    buffer.seek(0)

                    st.download_button(
                        label="📥 Baixar Planilha Organizada (CSV)",
                        data=buffer,
                        file_name=f"organizado_{arquivo.name.rsplit('.', 1)[0]}.csv",
                        mime="text/csv"
                    )
                else:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_limpo.to_excel(writer, index=False)
                    excel_data = output.getvalue()

                    st.download_button(
                        label="📥 Baixar Planilha Organizada (Excel)",
                        data=excel_data,
                        file_name=f"organizado_{arquivo.name.rsplit('.', 1)[0]}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

elif arquivo and not aceitou_termos:
    st.info("👆 Marque a caixa de seleção acima concordando com os termos de uso para liberar o processamento.")
