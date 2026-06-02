import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Salaz Analytics - Gestión Comercial", layout="wide")

# # 1. --- ENCABEZADO DE MARCA ESTILIZADO ---
st.markdown("""
    <div style="text-align: left;">
        <h2 style="margin-bottom: 0px; color: #3A3A3A; letter-spacing: 2px;">SALAZ ANALYTICS</h2>
        <p style="font-size: 14px; color: #00eb93; margin-top: 0px; text-transform: uppercase;">Plataforma Inteligente de Gestión</p>
    </div>
""", unsafe_allow_html=True)
st.divider()

# --- FUNCIONES DE CARGA DE DATOS ---
@st.cache_data
def cargar_datos_principales():
    # Tu lógica actual para cargar PUNTOS EJE CAFETERO, csv, etc.
    if os.path.exists("datos_corresponsales.csv"):
        return pd.read_csv("datos_corresponsales.csv")
    return None

@st.cache_data
def cargar_convenios():
    archivo_convenios = "listado-de-convenios-activos-corresponsales mayo 2.xlsx"
    if os.path.exists(archivo_convenios):
        # header=1 para saltar el título principal y tomar la fila de columnas reales
        df_conv = pd.read_excel(archivo_convenios, sheet_name="Convenios", header=1)
        return df_conv
    return None

# --- MENÚ DE NAVEGACIÓN ---
st.sidebar.title("Panel de Control")
opcion_menu = st.sidebar.radio("Seleccione el Tablero:", ["📊 Monitoreo Corresponsales", "📄 Convenios Activos (Mayo 2026)"])

# --- LÓGICA DE VISUALIZACIÓN ---
if opcion_menu == "📊 Monitoreo Corresponsales":
    st.header("📊 Gestión Comercial de Corresponsales")
    df_principal = cargar_datos_principales()
    if df_principal is not None:
        st.dataframe(df_principal, use_container_width=True)
        # Aquí continúa el resto de tu código original (gráficos, filtros, etc.)
    else:
        st.warning("No se encontró el archivo base de corresponsales.")

elif opcion_menu == "📄 Convenios Activos (Mayo 2026)":
    st.header("📄 Consulta de Convenios Activos para Recaudo")
    df_convenios = cargar_convenios()
    
    if df_convenios is not None:
        # Buscador interactivo
        busqueda = st.text_input("🔍 Buscar por Empresa, Convenio o Categoría:")
        
        df_filtrado = df_convenios.copy()
        if busqueda:
            df_filtrado = df_convenios[
                df_convenios['EMPRESA'].astype(str).str.contains(busqueda, case=False) |
                df_convenios['CONVENIO'].astype(str).str.contains(busqueda, case=False) |
                df_convenios['CATEGORIA'].astype(str).str.contains(busqueda, case=False)
            ]
        
        # Métricas rápidas
        c1, c2 = st.columns(2)
        c1.metric("Total Convenios", len(df_convenios))
        c2.metric("Resultados Encontrados", len(df_filtrado))
        
        # Tabla de datos
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Gráfico rápido de Convenios por Categoría
        st.subheader("📊 Distribución de Convenios por Categoría")
        top_categorias = df_filtrado['CATEGORIA'].value_counts().reset_index()
        top_categorias.columns = ['Categoría', 'Cantidad']
        fig = px.bar(top_categorias.head(10), x='Cantidad', y='Categoría', orientation='h', 
                     title="Top 10 Categorías con más Convenios", color='Cantidad', color_continuous_scale='Greens')
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.error("⚠️ El archivo 'listado-de-convenios-activos-corresponsales mayo 2.xlsx' no se encuentra en el repositorio.")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("SALAZ ANALYTICS | Gestión de Datos en Tiempo Real")
