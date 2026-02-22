import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestión Corresponsales", layout="wide")

SHEET_ID = "d/1VltkgOm0rb6aWso2wuSH7kmcoH_HJSWZGadNmnAEofc" 
URL_SHEET = f"https://docs.google.com/spreadsheets/d/1VltkgOm0rb6aWso2wuSH7kmcoH_HJSWZGadNmnAEofc/edit?usp=sharing"

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Leemos ignorando filas problemáticas
        df = pd.read_csv(URL_SHEET, on_bad_lines='skip', engine='python')
        
        # LIMPIEZA EXTREMA DE COLUMNAS
        # 1. Quitar espacios, tabulaciones y saltos de línea de los nombres
        df.columns = df.columns.str.strip().str.replace('\n', '').str.replace('\r', '')
        
        # 2. Eliminar columnas que no tengan nombre (fantasmas)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        return df
    except Exception as e:
        st.error(f"Error al cargar: {e}")
        return None

df_raw = cargar_datos()

if df_raw is not None:
    # --- DIAGNÓSTICO (Solo aparecerá si hay error) ---
    # Esto nos dirá cómo leyó Python los nombres de tus columnas
    nombres_reales = df_raw.columns.tolist()
    
    # Intentamos encontrar la columna 'Ciudad' incluso si tiene tildes o variaciones
    col_ciudad = None
    for c in nombres_reales:
        if "ciudad" in c.lower():
            col_ciudad = c
            break
            
    if col_ciudad is None:
        st.error("🚨 No encontré la columna 'Ciudad'.")
        st.write("Columnas detectadas en tu Excel:", nombres_reales)
        st.stop() # Detiene la ejecución para que no salga el error rojo feo

    # --- FILTRO LATERAL ---
    st.sidebar.header("🔍 Filtros")
    lista_ciudades = ["Todas"] + sorted(df_raw[col_ciudad].dropna().unique().tolist())
    ciudad_sel = st.sidebar.selectbox("Seleccione Municipio:", lista_ciudades)

    # ... Resto de tu código usando col_ciudad en lugar de 'Ciudad' ...
    st.success(f"Conectado con éxito. Columna detectada: {col_ciudad}")
    st.write(df_raw.head())
