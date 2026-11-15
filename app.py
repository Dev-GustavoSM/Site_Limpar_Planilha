import streamlit as st
import pandas as pd
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
* Sempre mantenha uma cópia de segurança do seu arquivo original.
* A revisão e conferência final dos dados tratados são de inteira responsabilidade do usuário.
""")

aceitou_termos = st.checkbox("Li e concordo que a ferramenta é um auxílio e revisarei os dados finais.")

modo_execucao = "Com IA"
if st.session_state["plano_atual"] == "Pro (Com IA)":
    modo_execucao = st.radio("Escolha o modo para esta planilha:", ["Com IA (Diagnóstico Inteligente)", "Apenas Limpeza Avançada Python"])

# ==========================================
# 5. UPLOAD E LEITURA INTELIGENTE DE COLUNAS
# ==========================================
arquivo = st.file_uploader("Envie sua planilha (CSV ou Excel)", type=["csv", "xlsx"])

if arquivo and aceitou_termos:
    plano = st.session_state["plano_atual"]
    
    if plano == "Gratuito" and st.session_state["usos_gratuitos"] >= 5:
        st.error("🔒 Você atingiu o limite de 5 planilhas gratuitas. Assine o Plano Básico ou Pro na barra lateral para continuar.")
        st.stop()

    if plano == "Gratuito":
        limite_linhas = 2000
    else:  
        limite_linhas = 10000

    try:
        if arquivo.name.endswith(".csv"):
            # Lê o conteúdo do arquivo como texto para detectar o separador exato
            conteudo_bytes = arquivo.read()
            arquivo.seek(0)
            
            # Tenta decodificar com utf-8 ou latin-1 para evitar erros de acentuação
            try:
                texto_amostra = conteudo_bytes.decode('utf-8-sig')
            except:
                texto_amostra = conteudo_bytes.decode('latin-1')

            # Descobre se o delimitador é vírgula ou ponto e vírgula automaticamente
            delimitador = ','
            try:
                dialecto = csv.Sniffer().sniff(texto_amostra[:2048], delimiters=',;')
                delimitador = dialecto.delimiter
            except:
                if ';' in texto_amostra:
                    delimitador = ';'

            # Carrega o DataFrame separando corretamente nas colunas
            df = pd.read_csv(arquivo, sep=delimitador, engine='python')
        else:
            df = pd.read_excel(arquivo)
            
    except Exception as e:
        st.error(f"Erro ao ler o arquivo. Verifique se não está corrompido. Detalhe: {e}")
        st.stop()

    total_linhas, total_colunas = df.shape

    # Segurança extra: se ainda assim vier empacotado em 1 coluna só
    if total_colunas == 1 and len(df) > 0:
        coluna_unica = df.columns[0]
        # Tenta quebrar por vírgula e ponto-e-vírgula na marra
        df = df[coluna_unica].astype(str).str.split(r'[,;]', expand=True)
        if len(df.columns) > 1:
            df.columns = df.iloc[0]
            df = df[1:].reset_index(drop=True)
        total_linhas, total_colunas = df.shape

    st.write(f"📄 **Arquivo carregado:** {total_linhas} linhas e {total_colunas} colunas separadas e estruturadas.")

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

                # Passo 1: Remove linhas e colunas totalmente vazias
                df_limpo = df.dropna(how="all").dropna(axis=1, how="all")
                vazias_removidas = linhas_antes - len(df_limpo)
                if vazias_removidas > 0:
                    relatorio_mudancas.append(f"🗑️ Foram removidas **{vazias_removidas}** linhas totalmente vazias.")

                # Passo 2: Remove duplicatas exatas
                antes_dup = len(df_limpo)
                df_limpo = df_limpo.drop_duplicates()
                duplicadas_removidas = antes_dup - len(df_limpo)
                if duplicadas_removidas > 0:
                    relatorio_mudancas.append(f"🔁 Foram removidas **{duplicadas_removidas}** linhas duplicadas.")

                # Passo 3: Limpeza profunda e padronização por coluna
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
                    relatorio_mudancas.append(f"🧹 Padronização e estruturação aplicadas em **{colunas_formatadas}** colunas de dados.")

                if plano == "Gratuito":
                    st.session_state["usos_gratuitos"] += 1

                st.success("✅ Limpeza e organização estrutural concluídas com sucesso!")
                st.subheader("📋 Relatório de Organização do Python:")
                if relatorio_mudancas:
                    for mudanca in relatorio_mudancas:
                        st.markdown(f"- {mudanca}")
                else:
                    st.info("ℹ️ A planilha já estava estruturada e limpa.")

                # --- CONSULTORIA DA IA (Apenas se for Pro e escolheu o modo com IA) ---
                usa_ia = (plano == "Pro (Com IA)" and "Com IA" in modo_execucao)
                
                if usa_ia:
                    st.subheader("🤖 Diagnóstico Inteligente da IA (Amostra de 10 Linhas)")
                    try:
                        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                        modelo = genai.GenerativeModel("gemini-1.5-flash")

                        amostra_texto = df_limpo.head(10).to_markdown(index=False)
                        
                        prompt = f"""
                        Você é um analista de qualidade de dados. Analise o cabeçalho e as 10 primeiras linhas desta planilha abaixo.
                        Identifique possíveis problemas de padronização (ex: datas em formatos diferentes, preços com texto misturado, nomes mal formatados, colunas confusas) e dê recomendações curtas e diretas do que o usuário deve revisar.
                        Lembre-se: você está vendo apenas uma amostra de 10 linhas e o cabeçalho.

                        Dados:
                        {amostra_texto}
                        """
                        
                        resposta = modelo.generate_content(prompt)
                        st.info(resposta.text)
                    except Exception as e:
                        st.warning("⚠️ Não foi possível conectar à IA neste momento, mas a limpeza avançada em Python foi concluída normalmente.")

                # --- GERAR ARQUIVO PARA DOWNLOAD ---
                buffer = io.BytesIO()
                df_limpo.to_csv(buffer, index=False, encoding="utf-8-sig")
                buffer.seek(0)

                st.download_button(
                    label="📥 Baixar Planilha Organizada (CSV)",
                    data=buffer,
                    file_name=f"organizado_{arquivo.name.split('.')[0]}.csv",
                    mime="text/csv"
                )

elif arquivo and not aceitou_termos:
    st.info("👆 Marque a caixa de seleção acima concordando com os termos de uso para liberar o processamento.")
