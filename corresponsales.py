import streamlit as st
import pandas as pd

st.set_page_config(page_title="BVB - Consulta Integral", layout="wide")

# 1. DATOS DE CONEXIÓN
SHEET_ID = "1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw"
# REEMPLAZA ESTE NÚMERO con el GID de la pestaña que tiene la base completa
GID = "0"  # <--- Pon aquí el número que encontraste después de 'gid='

URL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=60)
def cargar_datos_maestros():
    try:
        # Forzamos la lectura como CSV desde la pestaña específica
        df = pd.read_csv(URL_SHEET, on_bad_lines='skip')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

st.title("🏦 Sistema de Consulta de Corresponsalía")
df = cargar_datos_maestros()

if df is not None:
    # Mostramos las columnas para estar seguros de qué estamos leyendo
    # st.write("Columnas detectadas:", list(df.columns)) # Solo para pruebas

    # Intentamos encontrar las columnas aunque tengan nombres ligeramente distintos
    col_ciudad = next((c for c in df.columns if "ciudad" in c.lower()), None)
    col_esp = next((c for c in df.columns if "especialista" in c.lower()), None)
    
    if col_ciudad and col_esp:
        st.success(f"✅ Conectado a la base de {len(df)} registros.")
        
        # --- FILTROS ---
        ciudades = ["Todas"] + sorted(df[col_ciudad].dropna().unique().tolist())
        ciudad_sel = st.selectbox("Seleccione Municipio:", ciudades)

        # --- FILTRADO ---
        df_filtrado = df.copy()
        if ciudad_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado[col_ciudad] == ciudad_sel]

        # --- RESULTADOS ---
        c1, c2 = st.columns(2)
        c1.metric(f"Puntos en {ciudad_sel}", len(df_filtrado))
        
        # Tabla detallada
        columnas_finales = [c for c in [col_ciudad, 'Dirección', 'Tipo de CBs', col_esp] if c in df.columns]
        st.dataframe(df_filtrado[columnas_finales], use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Aún no detecto la columna 'Ciudad'.")
        st.info(f"Revisa que el GID ({GID}) sea el de la pestaña correcta.")
        st.write("Columnas en esta pestaña:", list(df.columns))
