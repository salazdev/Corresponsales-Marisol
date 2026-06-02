import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Salaz Analytics - Gestión Comercial", layout="wide")

# --- ENCABEZADO DE MARCA ESTILIZADO ---
st.markdown("""
    <div style="text-align: left;">
        <h2 style="margin-bottom: 0px; color: #3A3A3A; letter-spacing: 2px;">SALAZ ANALYTICS</h2>
        <p style="font-size: 14px; color: #00eb93; margin-top: 0px; text-transform: uppercase;">Plataforma Inteligente de Gestión</p>
    </div>
""", unsafe_allow_html=True)
st.divider()

# --- PRIMERO SE DEFINEN TODAS LAS FUNCIONES ---

@st.cache_data
def cargar_datos_principales():
    """
    Carga los datos históricos y principales de los corresponsales.
    """
    # Si tienes el archivo original como CSV:
    if os.path.exists("datos_corresponsales.csv"):
        return pd.read_csv("datos_corresponsales.csv")
    
    # Si usabas el archivo PUNTOS EJE CAFETERO.xlsx como principal:
    elif os.path.exists("PUNTOS EJE CAFETERO.xlsx"):
        return pd.read_excel("PUNTOS EJE CAFETERO.xlsx")
        
    return None

@st.cache_data(ttl=3600)
def cargar_convenios_optimizado():
    """
    Carga de manera ultra veloz el listado de convenios (procesado desde el CSV optimizado).
    """
    archivo_csv = "convenios_activos.csv"
    if os.path.exists(archivo_csv):
        # Se lee con una codificación estándar para evitar errores de tildes o eñes
        return pd.read_csv(archivo_csv, sep=",", encoding="latin-1")
    return None


# --- LUEGO SE CONSTRUIE EL MENÚ LATERAL Y LA LÓGICA ---

st.sidebar.title("Panel de Control")
opcion_menu = st.sidebar.radio("Seleccione el Tablero:", ["📊 Monitoreo Corresponsales", "📄 Convenios Activos (Mayo 2026)"])

# --- LÓGICA DE VISUALIZACIÓN ---

if opcion_menu == "📊 Monitoreo Corresponsales":
    st.header("📊 Gestión Comercial de Corresponsales")
    
    # Aquí llamamos a la función cuando YA está completamente definida arriba
    df_principal = cargar_datos_principales()
    
    if df_principal is not None:
        st.dataframe(df_principal, use_container_width=True)
        # --- EN ESTA SECCIÓN DEBES COLOCAR TU CÓDIGO ORIGINAL ---
        # (Todos tus gráficos de Plotly, tus filtros por municipio, 
        # y KPI's que ya tenías programados para Marisol deben ir aquí dentro)
        
    else:
        st.warning("No se encontró el archivo base de corresponsales (datos_corresponsales.csv o PUNTOS EJE CAFETERO.xlsx).")

elif opcion_menu == "📄 Convenios Activos (Mayo 2026)":
    st.header("📄 Consulta de Convenios Activos para Recaudo")
    
    df_convenios = cargar_convenios_optimizado()
    
    if df_convenios is not None:
        # Buscador interactivo en tiempo real
        busqueda = st.text_input("🔍 Buscar por Empresa, Convenio o Categoría:")
        
        df_filtrado = df_convenios.copy()
        if busqueda:
            df_filtrado = df_convenios[
                df_convenios['EMPRESA'].astype(str).str.contains(busqueda, case=False) |
                df_convenios['CONVENIO'].astype(str).str.contains(busqueda, case=False) |
                df_filtrado['CATEGORIA'].astype(str).str.contains(busqueda, case=False)
            ]
        
        # Indicadores en la parte superior
        c1, c2 = st.columns(2)
        c1.metric("Total Convenios en Base", len(df_convenios))
        c2.metric("Resultados Filtrados", len(df_filtrado))
        
        # Despliegue de la tabla optimizada
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Gráfica analítica de distribución
        st.subheader("📊 Distribución de Convenios por Categoría")
        top_categorias = df_filtrado['CATEGORIA'].value_counts().reset_index()
        top_categorias.columns = ['Categoría', 'Cantidad']
        
        fig = px.bar(top_categorias.head(10), x='Cantidad', y='Categoría', orientation='h', 
                     title="Top 10 Categorías con más Convenios", color='Cantidad', color_continuous_scale='Greens')
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.error("⚠️ El archivo 'convenios_activos.csv' no se encuentra en la raíz de tu repositorio de GitHub.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("SALAZ ANALYTICS | Gestión de Datos en Tiempo Real")
