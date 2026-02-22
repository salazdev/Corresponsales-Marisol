import streamlit as st
import pandas as pd

st.set_page_config(page_title="BVB - Gestión Corresponsales", layout="wide")

st.title("🏦 Gestión Estratégica de Corresponsales")
st.markdown("---")

# URL Robusta para Google Sheets
SHEET_ID = "1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw"
URL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Cargamos el archivo saltando líneas corruptas
        df = pd.read_csv(URL_SHEET, on_bad_lines='skip', engine='python')
        # Limpiamos los nombres de las columnas de espacios y saltos de línea
        df.columns = [str(c).strip().replace('\n', '').replace('\r', '') for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al conectar: {e}")
        return None

df_raw = cargar_datos()

if df_raw is not None:
    # --- BUSCADOR INTELIGENTE DE COLUMNAS ---
    # Esto busca las columnas aunque el nombre no sea exacto
    def encontrar_columna(nombre_deseado, lista_columnas):
        for c in lista_columnas:
            if nombre_deseado.lower() in c.lower():
                return c
        return None

    col_ciudad = encontrar_columna("Ciudad", df_raw.columns)
    col_esp = encontrar_columna("ESPECIALISTA", df_raw.columns)
    col_dir = encontrar_columna("Dirección", df_raw.columns)
    col_tipo = encontrar_columna("Tipo", df_raw.columns)

    if not col_ciudad:
        st.error("🚨 No se encontró una columna que diga 'Ciudad'.")
        st.write("Columnas detectadas en el archivo:", list(df_raw.columns))
        st.stop()

    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros")
    
    ciudades = ["Todas"] + sorted(df_raw[col_ciudad].dropna().unique().tolist())
    ciudad_sel = st.sidebar.selectbox("Seleccione Municipio:", ciudades)

    df_filtrado = df_raw.copy()
    if ciudad_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_ciudad] == ciudad_sel]

    # --- MÉTRICAS ---
    c1, c2 = st.columns(2)
    c1.metric(f"Corresponsales en {ciudad_sel}", len(df_filtrado))
    c2.metric("Total en Base de Datos", len(df_raw))

    # --- TABLA ---
    st.subheader(f"📍 Detalle de Puntos en {ciudad_sel}")
    
    # Armamos la vista con las columnas encontradas
    columnas_mostrar = [c for c in [col_ciudad, col_dir, col_tipo, col_esp] if c is not None]
    
    st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True, hide_index=True)

else:
    st.info("Configurando conexión con Google Sheets...")
