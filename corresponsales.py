import streamlit as st
import pandas as pd

st.set_page_config(page_title="BVB - Consulta Integral", layout="wide")

st.title("🏦 Sistema de Consulta de Corresponsalía")

# 1. DATOS DE CONEXIÓN (Verificados)
SHEET_ID = "1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw"
# Si el GID 0 te da error, es posible que la base detallada tenga otro ID.
# Pero probaremos con este formato que es más robusto:
URL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Hoja1" 

@st.cache_data(ttl=60)
def cargar_datos_maestros():
    try:
        # Usamos un motor de lectura más flexible para archivos grandes
        df = pd.read_csv(URL_SHEET, on_bad_lines='skip', engine='python')
        
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip().replace('\n', '').replace('\r', '') for c in df.columns]
        
        # Si el archivo leyó basura (como código HTML), lanzamos error para manejarlo
        if df.empty or "Unnamed" in df.columns[0] and len(df) < 2:
            return None
            
        return df
    except Exception as e:
        # Si el error 400 persiste, intentamos la ruta alternativa automáticamente
        try:
            alt_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
            df = pd.read_csv(alt_url)
            return df
        except:
            st.error(f"Error crítico de conexión: {e}")
            return None

df = cargar_datos_maestros()

if df is not None:
    # Identificar columnas dinámicamente
    cols = list(df.columns)
    col_ciudad = next((c for c in cols if "ciudad" in c.lower()), None)
    col_esp = next((c for c in cols if "especialista" in c.lower()), None)

    if col_ciudad:
        st.success("✅ ¡Conectado con éxito!")
        
        # Filtros
        ciudad_sel = st.sidebar.selectbox("Municipio:", ["Todos"] + sorted(df[col_ciudad].dropna().unique().tolist()))
        
        df_filtrado = df.copy()
        if ciudad_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado[col_ciudad] == ciudad_sel]
            
        # Métricas
        c1, c2 = st.columns(2)
        c1.metric(f"Puntos en {ciudad_sel}", len(df_filtrado))
        c2.metric("Total Base de Datos", len(df))
        
        # Mostrar Tabla
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("⚠️ El archivo cargó, pero no encuentro la columna 'Ciudad'.")
        st.write("Columnas encontradas:", cols)
        st.info("Asegúrate de que la primera hoja del Excel sea la que tiene todas las columnas.")
else:
    st.error("❌ No se pudo obtener la información.")
    st.markdown("""
    **Posibles soluciones:**
    1. Verifica que el archivo en Google Sheets siga siendo **Público** (Cualquiera con el enlace).
    2. En el Google Sheet, ve a **Archivo > Compartir > Publicar en la Web**. Dale a 'Publicar' y selecciona 'Valores separados por comas (.csv)'. Esto genera un enlace infalible.
    """)
