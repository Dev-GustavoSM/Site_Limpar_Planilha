import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página do site
st.set_page_config(page_title="DataCleaner Universal", page_icon="🧹", layout="centered")

st.title("🧹 DataCleaner Universal")
st.write("Envie qualquer planilha suja (CSV ou Excel) abaixo. O sistema limpa duplicadas, padroniza erros e entrega o arquivo pronto para uso!")

# 1. Upload universal de arquivos (aceita tanto CSV quanto planilhas do Excel)
arquivo_enviado = st.file_uploader("Arraste ou selecione sua planilha", type=["csv", "xlsx", "xls"])

if arquivo_enviado is not None:
    try:
        # Descobre se é CSV ou Excel pelo formato do arquivo
        if arquivo_enviado.name.endswith('.csv'):
            df = pd.read_csv(arquivo_enviado)
        else:
            df = pd.read_excel(arquivo_enviado)
        
        st.success("Arquivo carregado com sucesso!")
        
        # Mostra as estatísticas iniciais
        st.write(f"📊 **Dimensões originais:** {df.shape[0]} linhas e {df.shape[1]} colunas")
        
        with st.expander("🔍 Ver amostra dos dados originais"):
            st.dataframe(df.head())
        
        # --- PROCESSAMENTO UNIVERSAL DE LIMPEZA ---
        
        # Copia o DataFrame para processar
        df_limpo = df.copy()
        
        # A. Remove linhas que são cópias exatas
        linhas_antes = len(df_limpo)
        df_limpo.drop_duplicates(inplace=True)
        linhas_removidas_dup = linhas_antes - len(df_limpo)
        
        # B. Substitui textos de erro comuns por valores vazios reais (NaN)
        erros_comuns = ['ERROR', 'UNKNOWN', 'N/A', 'NULL', 'null', 'error', 'unknown']
        df_limpo.replace(erros_comuns, np.nan, inplace=True)
        
        # C. Remove espaços em branco antes/depois nas colunas de texto (string)
        for coluna in df_limpo.select_dtypes(include=['object']).columns:
            df_limpo[coluna] = df_limpo[coluna].str.strip()
        
        # D. Preenche valores vazios de texto de forma inteligente
        df_limpo.fillna('Não informado', inplace=True)
        
        # --- EXIBIÇÃO DOS RESULTADOS ---
        st.divider()
        st.subheader("✨ Dados Limpos e Tratados")
        st.write(f"Foram removidas **{linhas_removidas_dup}** linhas duplicadas e os erros foram padronizados.")
        
        with st.expander("🔍 Ver amostra dos dados limpos"):
            st.dataframe(df_limpo.head())
        
        # --- PREPARAÇÃO PARA DOWNLOAD UNIVERSAL ---
        # Deixa o usuário escolher o formato de saída (CSV ou Excel)
        tipo_saida = st.radio("Escolha o formato para baixar:", ["CSV", "Excel (.xlsx)"], horizontal=True)
        
        if tipo_saida == "CSV":
            arquivo_convertido = df_limpo.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Planilha Limpa (CSV)",
                data=arquivo_convertido,
                file_name="dados_limpos_universal.csv",
                mime="text/csv"
            )
        else:
            # Para exportar Excel na nuvem usando BytesIO
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_limpo.to_excel(writer, index=False)
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Baixar Planilha Limpa (Excel)",
                data=excel_data,
                file_name="dados_limpos_universal.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
