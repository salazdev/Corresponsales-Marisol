import streamlit as st
import pandas as pd

st.set_page_config(page_title="BVB - Consulta Directa", layout="wide")

st.title("🏦 Sistema de Consulta de Corresponsalía (Versión Alta Velocidad)")

# 1. CARGA DESDE GITHUB (Súper rápido y estable)
@st.cache_data(ttl=3600) # Se guarda en memoria por 1 hora
def cargar_datos_locales():
    try:
        # Al estar en la misma carpeta de GitHub, solo ponemos el nombre del archivo
        df = pd.read_csv("datos_corresponsales.csv", on_bad_lines='skip', engine='python')
        # Limpieza de columnas
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except FileNotFoundError:
        st.error("🚨 ¡Archivo no encontrado en GitHub! Asegúrate de subir 'datos_corresponsales.csv' a tu repositorio.")
        return None
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

df = cargar_datos_locales()

if df is not None:
    # Identificar columnas
    cols = list(df.columns)
    col_ciudad = next((c for c in cols if "ciudad" in c.lower()), None)
    col_esp = next((c for c in cols if "especialista" in c.lower()), None)
    col_dir = next((c for c in cols if "dirección" in c.lower() or "direccion" in c.lower()), None)

    if col_ciudad:
        st.success(f"✅ Base de datos cargada localmente: {len(df):,} registros.")
        
        # --- FILTROS ---
        st.sidebar.header("🔍 Consultar")
        lista_ciudades = ["Todas"] + sorted(df[col_ciudad].dropna().unique().tolist())
        ciudad_sel = st.sidebar.selectbox("Seleccione Municipio:", lista_ciudades)

        df_filtrado = df.copy()
        if ciudad_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado[col_ciudad] == ciudad_sel]

        # --- MÉTRICAS ---
        m1, m2 = st.columns(2)
        m1.metric(f"Corresponsales en {ciudad_sel}", f"{len(df_filtrado):,}")
        m2.metric("Total Base BVB", f"{len(df):,}")

        # --- TABLA ---
        st.subheader(f"📍 Listado Detallado - {ciudad_sel}")
        columnas_finales = [c for c in [col_ciudad, col_dir, 'Tipo de CBs', col_esp] if c in cols]
        st.dataframe(df_filtrado[columnas_finales], use_container_width=True, hide_index=True)

    else:
        st.warning("⚠️ El archivo subido no tiene la columna 'Ciudad'.")
        st.write("Columnas detectadas:", cols)
