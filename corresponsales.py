import streamlit as st
import pandas as pd

st.set_page_config(page_title="BVB - Consulta Integral", layout="wide")

st.title("🏦 Sistema de Consulta de Corresponsalía")

# 1. DATOS DE CONEXIÓN
# Usaremos el formato /gviz/tq que es el que Google usa para sus propios dashboards
SHEET_ID = "1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw"
URL_SHEET = f"https://docs.google.com/spreadsheets/d/1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw/edit?usp=sharing"

@st.cache_data(ttl=300)
def cargar_datos_grandes():
    try:
        # Cargamos el archivo usando una técnica que ignora el código basura de Google
        df = pd.read_csv(URL_SHEET, on_bad_lines='skip', engine='python')
        
        # Limpieza profunda de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Si la primera columna tiene basura como '/*', la eliminamos
        if "/*" in df.columns[0] or "html" in df.columns[0].lower():
            # Plan B: Intento de limpieza si Google envió encabezados extraños
            df = pd.read_csv(URL_SHEET, skiprows=1, on_bad_lines='skip')
            df.columns = [str(c).strip() for c in df.columns]
            
        return df
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

df = cargar_datos_grandes()

if df is not None:
    # --- BUSCADOR DINÁMICO DE COLUMNAS ---
    cols = list(df.columns)
    
    # Buscamos 'Ciudad' o algo parecido
    col_ciudad = next((c for c in cols if "ciudad" in c.lower()), None)
    col_esp = next((c for c in cols if "especialista" in c.lower()), None)
    col_dir = next((c for c in cols if "dirección" in c.lower() or "direccion" in c.lower()), None)

    if col_ciudad:
        st.success(f"✅ ¡Conectado! Se encontraron {len(df):,} registros.")
        
        # Filtros laterales
        st.sidebar.header("🔍 Consultar")
        lista_ciudades = ["Todas"] + sorted(df[col_ciudad].dropna().unique().tolist())
        ciudad_sel = st.sidebar.selectbox("Seleccione el Municipio:", lista_ciudades)

        df_filtrado = df.copy()
        if ciudad_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado[col_ciudad] == ciudad_sel]

        # Métricas de la Directora
        m1, m2 = st.columns(2)
        m1.metric(f"Corresponsales en {ciudad_sel}", f"{len(df_filtrado):,}")
        m2.metric("Total Nacional", f"{len(df):,}")

        # Tabla Detallada
        st.subheader(f"📍 Listado Detallado - {ciudad_sel}")
        columnas_finales = [c for c in [col_ciudad, col_dir, 'Tipo de CBs', col_esp] if c in cols]
        st.dataframe(df_filtrado[columnas_finales], use_container_width=True, hide_index=True)

    else:
        st.warning("⚠️ Los datos cargaron pero las columnas son incorrectas.")
        st.write("Columnas detectadas actualmente:", cols)
        st.info("Esto sucede porque el archivo de 25MB está tardando en procesarse. Intenta recargar la página en 10 segundos.")
