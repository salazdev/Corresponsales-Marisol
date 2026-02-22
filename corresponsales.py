import streamlit as st
import pandas as pd

st.set_page_config(page_title="BVB - Consulta Integral", layout="wide")

st.title("🏦 Sistema de Consulta de Corresponsalía")

# 1. DATOS DE CONEXIÓN
SHEET_ID = "1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw"
GID = "0"  # <--- ASEGÚRATE DE QUE ESTE SEA EL GID DE LA PESTAÑA CON DATOS

# Nueva URL simplificada para evitar el Error 400
URL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=60)
def cargar_datos_maestros():
    try:
        # Método directo de Pandas para leer el CSV de Google
        df = pd.read_csv(URL_SHEET)
        # Limpieza de nombres de columnas (espacios, saltos de línea)
        df.columns = [str(c).strip().replace('\n', '').replace('\r', '') for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al conectar con la pestaña GID {GID}: {e}")
        return None

df = cargar_datos_maestros()

if df is not None:
    # Verificamos qué columnas llegaron
    columnas = list(df.columns)
    
    # Buscador flexible de nombres (por si hay tildes o mayúsculas)
    col_ciudad = next((c for c in columnas if "ciudad" in c.lower()), None)
    col_esp = next((c for c in columnas if "especialista" in c.lower()), None)
    col_dir = next((c for c in columnas if "dirección" in c.lower() or "direccion" in c.lower()), None)

    if col_ciudad and col_esp:
        st.success(f"✅ Conectado con éxito a la base de datos.")
        
        # --- FILTROS ---
        st.sidebar.header("🔍 Opciones de Filtro")
        lista_ciudades = ["Todas"] + sorted(df[col_ciudad].dropna().unique().tolist())
        ciudad_sel = st.sidebar.selectbox("Seleccione Municipio:", lista_ciudades)

        # --- LÓGICA DE FILTRADO ---
        df_filtrado = df.copy()
        if ciudad_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado[col_ciudad] == ciudad_sel]

        # --- VISUALIZACIÓN ---
        m1, m2 = st.columns(2)
        m1.metric(f"Puntos en {ciudad_sel}", len(df_filtrado))
        m2.metric("Total Nacional", len(df))

        st.subheader(f"📍 Detalle de Ubicaciones en {ciudad_sel}")
        
        # Columnas a mostrar (solo las que existan)
        cols_finales = [c for c in [col_ciudad, col_dir, 'Tipo de CBs', col_esp] if c in columnas]
        
        st.dataframe(df_filtrado[cols_existentes := cols_finales], use_container_width=True, hide_index=True)
        
        # Botón de descarga para la Directora
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar este reporte", csv, "reporte_bvb.csv", "text/csv")
    else:
        st.warning("⚠️ Estamos en la pestaña equivocada.")
        st.info(f"La pestaña con GID {GID} solo tiene estas columnas: {columnas}")
        st.write("Tip: Si esta no es la base detallada, busca el GID de la otra pestaña en la URL de Google Sheets.")

else:
    st.info("Intentando reconectar con el servidor de datos...")
