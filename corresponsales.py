import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="BVB - Gestión Corresponsales", layout="wide")

# Título con estilo
st.title("🏦 Gestión Estratégica de Corresponsales")
st.markdown("---")

# 2. CONEXIÓN AL GOOGLE SHEET (NUEVO ID)
SHEET_ID = "1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw"
# Usamos el formato 'gviz' que es el más estable para archivos pesados
URL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=300) # Caché de 5 minutos para no saturar la carga
def cargar_datos_banco():
    try:
        # Leemos el archivo. Si hay filas corruptas por el peso, las salta.
        df = pd.read_csv(URL_SHEET, on_bad_lines='skip', engine='python')
        
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Eliminamos filas totalmente vacías
        df = df.dropna(how='all')
        
        return df
    except Exception as e:
        st.error(f"Error al conectar con los datos: {e}")
        return None

df_raw = cargar_datos_banco()

if df_raw is not None:
    # --- FILTROS EN LA BARRA LATERAL ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    # Filtro de Ciudad
    if 'Ciudad' in df_raw.columns:
        lista_ciudades = ["Todas"] + sorted(df_raw['Ciudad'].dropna().unique().tolist())
        ciudad_sel = st.sidebar.selectbox("Seleccione Municipio:", lista_ciudades)
    else:
        st.error("No se encontró la columna 'Ciudad'")
        st.stop()

    # Filtro de Especialista
    if 'ESPECIALISTA' in df_raw.columns:
        lista_esp = ["Todos"] + sorted(df_raw['ESPECIALISTA'].dropna().unique().tolist())
        esp_sel = st.sidebar.selectbox("Filtrar por Especialista:", lista_esp)
    else:
        esp_sel = "Todos"

    # APLICAR FILTROS
    df = df_raw.copy()
    if ciudad_sel != "Todas":
        df = df[df['Ciudad'] == ciudad_sel]
    if esp_sel != "Todos":
        df = df[df['ESPECIALISTA'] == esp_sel]

    # --- MÉTRICAS PRINCIPALES ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric(f"Puntos en {ciudad_sel}", f"{len(df):,}")
    
    with c2:
        # Buscamos a Jorge Arrieta (con manejo de errores por si no está en la vista actual)
        jorge_data = df_raw[df_raw['ESPECIALISTA'].str.contains("JORGE ARRIETA", case=False, na=False)]
        st.metric("Total Jorge Arrieta", len(jorge_data))
        
    with c3:
        # Buscamos tu nombre (Ajustado según el Excel)
        tu_data = df_raw[df_raw['ESPECIALISTA'].str.contains("ALAN", case=False, na=False)]
        st.metric("Total Alan Forero", len(tu_data))

    st.divider()

    # --- TABLA DE RESULTADOS ---
    st.subheader(f"📍 Detalle de Corresponsales: {ciudad_sel}")
    
    # Columnas que solicitó la Directora
    cols_interes = ['Tipo de CBs', 'Dirección', 'Ciudad', 'ESPECIALISTA
