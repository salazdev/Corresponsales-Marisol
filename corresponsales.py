import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE LA APP
st.set_page_config(page_title="BVB - Consulta Integral", layout="wide")

# Estilo personalizado para el Banco de Bogotá
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; border-left: 5px solid #0033a0; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Control: Corresponsalía Bancaria")
st.info("Consulta detallada de Especialistas, Ciudades y Direcciones.")

# 2. CARGA DE DATOS (Desde el archivo que subiste a GitHub)
@st.cache_data(ttl=3600)
def cargar_datos_locales():
    try:
        # Cargamos el archivo local
        df = pd.read_csv("datos_corresponsales.csv", on_bad_lines='skip', engine='python')
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except FileNotFoundError:
        st.error("🚨 Error: No se encuentra el archivo 'datos_corresponsales.csv' en el repositorio.")
        return None
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        return None

df = cargar_datos_locales()

if df is not None:
    # --- BUSCADOR DE COLUMNAS (Para que el código no falle) ---
    cols = df.columns.tolist()
    col_ciudad = next((c for c in cols if "ciudad" in c.lower()), None)
    col_esp = next((c for c in cols if "especialista" in c.lower()), None)
    col_dir = next((c for c in cols if "dirección" in c.lower() or "direccion" in c.lower()), None)
    col_tipo = next((c for c in cols if "tipo" in c.lower()), None)

    # --- BARRA LATERAL: FILTROS MULTIPLES ---
    st.sidebar.header("🔍 Criterios de Consulta")
    
    # Filtro 1: Especialista (Jorge Arrieta, Alan Forero, etc.)
    if col_esp:
        lista_esp = ["Todos"] + sorted(df[col_esp].dropna().unique().tolist())
        esp_sel = st.sidebar.selectbox("Filtrar por Especialista:", lista_esp)
    else:
        esp_sel = "Todos"

    # Filtro 2: Ciudad (Se actualiza según el Especialista elegido)
    df_temp = df.copy()
    if esp_sel != "Todos":
        df_temp = df_temp[df_temp[col_esp] == esp_sel]
    
    if col_ciudad:
        lista_ciudades = ["Todas"] + sorted(df_temp[col_ciudad].dropna().unique().tolist())
        ciudad_sel = st.sidebar.selectbox("Filtrar por Ciudad:", lista_ciudades)
    else:
        ciudad_sel = "Todas"

    # --- LÓGICA DE FILTRADO FINAL ---
    df_final = df.copy()
    if esp_sel != "Todos":
        df_final = df_final[df_final[col_esp] == esp_sel]
    if ciudad_sel != "Todas":
        df_final = df_final[df_final[col_ciudad] == ciudad_sel]

    # --- MÉTRICAS ---
    st.subheader("📊 Resumen de la Selección")
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.metric("Corresponsales Visualizados", f"{len(df_final):,}")
    with m2:
        st.metric("Especialista Seleccionado", esp_sel if esp_sel != "Todos" else "Varios")
    with m3:
        st.metric("Ciudad", ciudad_sel if ciudad_sel != "Todas" else "Nacional")

    st.divider()

    # --- CONSULTA DE DIRECCIONES Y DETALLES ---
    st.subheader("📍 Detalle de Direcciones y Puntos")
    
    # Buscador de texto libre (para buscar una dirección específica o nombre de local)
    busqueda = st.text_input("🔍 Buscar por palabra clave (Dirección, nombre, etc.):")
    if busqueda:
        # Buscamos en todas las columnas para dar el resultado más amplio
        df_final = df_final[df_final.astype(str).apply(lambda x: x.str.contains(busqueda, case=False, na=False)).any(axis=1)]

    # Seleccionamos el orden de las columnas para la Directora
    columnas_vista = [c for c in [col_esp, col_ciudad, col_dir, col_tipo] if c is not None]
    
    # Mostramos la tabla interactiva
    st.dataframe(
        df_final[columnas_vista], 
        use_container_width=True, 
        hide_index=True
    )

    # --- OPCIÓN DE DESCARGA ---
    st.sidebar.markdown("---")
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Descargar consulta (CSV)",
        data=csv,
        file_name=f"reporte_{ciudad_sel}_{esp_sel}.csv",
        mime="text/csv",
    )

else:
    st.warning("Esperando carga de datos...")
