import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA APP
st.set_page_config(page_title="Banco de Bogotá - Corresponsalía", layout="wide")

# Estilo visual corporativo
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Gestión Estratégica de Corresponsales")
st.info("Plataforma de consulta rápida para la Dirección de Corresponsalía.")

# 2. CONEXIÓN A GOOGLE SHEETS
# Reemplaza con el ID del archivo de la Directora
SHEET_ID = "1VltkgOm0rb6aWso2wuSH7kmcoH_HJSWZGadNmnAEofc" 
URL_SHEET = f"https://docs.google.com/spreadsheets/d/1VltkgOm0rb6aWso2wuSH7kmcoH_HJSWZGadNmnAEofc/edit?usp=sharing"

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_csv(URL_SHEET)
        df.columns = df.columns.str.strip() # Limpiar espacios en encabezados
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

df_raw = cargar_datos()

if df_raw is not None:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Criterios de Búsqueda")
    
    # Filtro de Ciudad (Municipio)
    lista_ciudades = ["Todas"] + sorted(df_raw['Ciudad'].dropna().unique().tolist())
    ciudad_sel = st.sidebar.selectbox("Seleccione Municipio/Ciudad:", lista_ciudades)
    
    # Filtro de Especialista
    lista_especialistas = ["Todos"] + sorted(df_raw['ESPECIALISTA'].dropna().unique().tolist())
    especialista_sel = st.sidebar.selectbox("Filtrar por Especialista:", lista_especialistas)

    # APLICAR FILTROS AL DATAFRAME
    df = df_raw.copy()
    if ciudad_sel != "Todas":
        df = df[df['Ciudad'] == ciudad_sel]
    if especialista_sel != "Todos":
        df = df[df['ESPECIALISTA'] == especialista_sel]

    # --- MÉTRICAS DINÁMICAS ---
    st.subheader(f"📊 Resumen: {ciudad_sel}")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # Aquí está la respuesta a tu solicitud: Conteo automático por Ciudad
        st.metric(f"Corresponsales en {ciudad_sel}", len(df))
    
    with c2:
        # Conteo para Jorge Arrieta
        cant_jorge = len(df[df['ESPECIALISTA'].str.contains("JORGE ARRIETA", case=False, na=False)])
        st.metric("Liderados por Jorge A.", cant_jorge)
        
    with c3:
        # Conteo para tu nombre (Ajustar nombre exacto)
        tu_nombre = "ALAN FORERO" 
        cant_tu = len(df[df['ESPECIALISTA'].str.contains(tu_nombre, case=False, na=False)])
        st.metric(f"Liderados por {tu_nombre}", cant_tu)

    st.divider()

    # --- DETALLE DE DIRECCIONES ---
    st.subheader("📍 Direcciones y Tipos de Corresponsal")
    
    # Seleccionamos las columnas exactas que mencionaste
    columnas_vista = ['Ciudad', 'Dirección', 'Tipo de CBs', 'ESPECIALISTA']
    
    if not df.empty:
        # Buscador de texto libre para nombres específicos
        busqueda = st.text_input("🔍 Buscar por dirección o tipo:")
        if busqueda:
            df_final = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        else:
            df_final = df

        # Mostramos la tabla limpia
        st.dataframe(df_final[columnas_vista], use_container_width=True, hide_index=True)
        
        # Gráfico rápido de apoyo
        if ciudad_sel == "Todas":
            st.subheader("📈 Distribución por Ciudad (Top 10)")
            top_ciudades = df_raw['Ciudad'].value_counts().head(10).reset_index()
            fig = px.bar(top_ciudades, x='Ciudad', y='count', labels={'count':'Cantidad'}, color='Ciudad')
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.warning("No se encontraron corresponsales con los filtros seleccionados.")

else:
    st.error("Verifica el acceso al Google Sheet y los nombres de las columnas.")
