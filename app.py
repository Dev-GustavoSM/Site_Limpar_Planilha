import streamlit as st
import pandas as pd
import google.generativeai as genai
import io
import threading

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
            st.success("Plano Pro ativado! (Limpeza + IA liberados)")
        elif token_input in TOKENS_BASICO_10_REAIS:
            st.session_state["plano_atual"] = "Básico (R$ 10/mês)"
            st.success("Plano Básico ativado! (Apenas limpeza Python)")
        else:
            st.error("Token inválido ou expirado.")

    st.info(f"**Seu Plano Atual:** {st.session_state['plano_atual']}")
    if st.session_state["plano_atual"] == "Gratuito":
        restantes = max(0, 5 - st.session_state["usos_gratuitos"])
        st.write(f"Testes gratuitos restantes: **{restantes}/5**")

    st.divider()
    st.subheader("💎 Nossos Planos")
    st.markdown("""
    * **Gratuito:** Até 5 planilhas (Máx. 2.000 linhas). Apenas limpeza básica.
    * **Básico (R$ 10/mês):** Uso contínuo sem IA (Máx. 10.000 linhas). Limpeza rápida estrutural.
    * **Pro (Mensal com IA):** Inclui TUDO do Básico + **Consultoria com Inteligência Artificial** analisando 10 linhas de amostra (Máx. 10.000 linhas).
    
    *Para assinar, faça o Pix e envie o comprovante no WhatsApp para receber o seu token.*
    """)

# ==========================================
# 4. INTERFACE PRINCIPAL E AVISO JURÍDICO
# ==========================================
st.title("📊 DataCleaner Universal")
st.write("Automatize a limpeza de planilhas corporativas com segurança e velocidade.")

st.warning("""
⚠️ **Aviso Importante & Termos de Uso:** 
Esta plataforma é uma ferramenta de auxílio à produtividade. A Inteligência Artificial analisa padrões para sugerir melhorias, mas **pode cometer erros ou interpretações imprecisas**. 
* Sempre mantenha uma cópia de segurança do seu arquivo original.
* A revisão e conferência final dos dados tratados são de inteira responsabilidade do usuário.
""")

aceitou_termos = st.checkbox("Li e concordo que a ferramenta é um auxílio e revisarei os dados finais.")

modo_execucao = "Com IA"
if st.session_state["plano_atual"] == "Pro (Com IA)":
    modo_execucao = st.radio("Escolha o modo para esta planilha:", ["Com IA (Diagnóstico Inteligente)", "Apenas Limpeza Python (Básico)"])

# ==========================================
# 5. UPLOAD E VERIFICAÇÃO DE LIMITES
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
            df = pd.read_csv(arquivo)
        else:
            df = pd.read_excel(arquivo)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo. Verifique se não está corrompido. Detalhe: {e}")
        st.stop()

    total_linhas, total_colunas = df.shape
    st.write(f"📄 **Arquivo carregado:** {total_linhas} linhas e {total_colunas} colunas.")

    if total_linhas > limite_linhas:
        st.error(f"🚫 **Limite Excedido:** Seu plano suporta até **{limite_linhas:,} linhas**. Este arquivo possui **{total_linhas:,} linhas**.")
        st.stop()

    # ==========================================
    # 6. PROCESSAMENTO EM FILA (PYTHON + IA + RELATÓRIO)
    # ==========================================
    if st.button("🚀 Iniciar Limpeza Agora"):
        with st.spinner("Aguardando fila do servidor e processando dados..."):
            with fila_servidor:
                # --- LIMPEZA DURA EM PYTHON COM RELATÓRIO DETALHADO ---
                linhas_antes = len(df)
                relatorio_mudancas = []

                # 1. Remove linhas totalmente vazias
                df_limpo = df.dropna(how="all")
                vazias_removidas = linhas_antes - len(df_limpo)
                if vazias_removidas > 0:
                    relatorio_mudancas.append(f"🗑️ Foram removidas **{vazias_removidas}** linhas totalmente vazias.")

                # 2. Remove duplicatas exatas
                antes_dup = len(df_limpo)
                df_limpo = df_limpo.drop_duplicates()
                duplicadas_removidas = antes_dup - len(df_limpo)
                if duplicadas_removidas > 0:
                    relatorio_mudancas.append(f"🔁 Foram removidas **{duplicadas_removidas}** linhas duplicadas.")

                # 3. Limpa espaços extras nas pontas dos textos
                colunas_texto_modificadas = 0
                for col in df_limpo.select_dtypes(include=["object"]).columns:
                    tem_espacos = df_limpo[col].astype(str).str.contains(r'^\s+|\s+$', regex=True).any()
                    if tem_espacos:
                        df_limpo[col] = df_limpo[col].astype(str).str.strip()
                        colunas_texto_modificadas += 1

                if colunas_texto_modificadas > 0:
                    relatorio_mudancas.append(f"🧹 Foram limpos espaços em branco desnecessários em **{colunas_texto_modificadas}** colunas de texto.")

                # Atualiza contador se for gratuito
                if plano == "Gratuito":
                    st.session_state["usos_gratuitos"] += 1

                # Mostra o relatório na tela para o cliente
                st.success("✅ Limpeza estrutural concluída com sucesso!")
                st.subheader("📋 Relatório de Ações do Python:")
                if relatorio_mudancas:
                    for mudanca in relatorio_mudancas:
                        st.markdown(f"- {mudanca}")
                else:
                    st.info("ℹ️ A planilha já estava limpa estruturalmente (nenhuma linha vazia ou duplicada encontrada).")

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
                        st.warning("⚠️ Não foi possível conectar à IA neste momento, mas a limpeza em Python foi concluída normalmente.")

                # --- GERAR ARQUIVO PARA DOWNLOAD ---
                buffer = io.BytesIO()
                df_limpo.to_csv(buffer, index=False, encoding="utf-8-sig")
                buffer.seek(0)

                st.download_button(
                    label="📥 Baixar Planilha Limpa (CSV)",
                    data=buffer,
                    file_name=f"limpo_{arquivo.name.split('.')[0]}.csv",
                    mime="text/csv"
                )

elif arquivo and not aceitou_termos:
    st.info("👆 Marque a caixa de seleção acima concordando com os termos de uso para liberar o processamento.")
