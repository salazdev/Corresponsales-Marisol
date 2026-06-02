import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN E IDENTIDAD VISUAL (ESTILOS PROTEGIDOS)
st.set_page_config(page_title="BVB - Gestión Estratégica", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    
    /* Fuerza el color del número (azul corporativo) */
    [data-testid="stMetricValue"] { 
        color: #0033a0 !important; 
        font-weight: bold !important; 
    }
    
    /* Fuerza el color del título del cuadro (gris oscuro visible) */
    [data-testid="stMetricLabel"] { 
        color: #222222 !important; 
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    /* Estructura de las tarjetas de métricas */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border-left: 5px solid #EBB932 !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1) !important;
        border-radius: 5px !important;
        padding: 10px 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# IDENTIDAD VISUAL - SALAZ ANALYTICS
st.markdown("""
    <div style="text-align: left;">
        <h2 style="margin-bottom: 0px; color: #0033a0; letter-spacing: 2px; font-weight: bold;">SALAZ ANALYTICS</h2>
        <p style="font-size: 14px; color: #EBB932; margin-top: 0px; text-transform: uppercase; font-weight: bold;">Plataforma Inteligente de Gestión</p>
    </div>
""", unsafe_allow_html=True)
st.title("🏦 Gestión Integral de Corresponsalía BVB")
st.divider()


# 2. CARGA DE DATOS ORIGINAL DE CORRESPONSALES (UNIFICANDO CIUDADES REPETIDAS)
@st.cache_data(ttl=600)
def cargar_datos_corresponsales():
    try:
        if not os.path.exists("datos_corresponsales.csv"):
            return None
            
        try:
            df = pd.read_csv("datos_corresponsales.csv", sep=',', engine='python', on_bad_lines='skip')
            if len(df.columns) <= 1: 
                raise ValueError
        except:
            df = pd.read_csv("datos_corresponsales.csv", sep=';', engine='python', on_bad_lines='skip')
        
        df.columns = [str(c).strip() for c in df.columns]
        
        # Desduplicar columnas para PyArrow en st.dataframe
        columnas_limpias = []
        conteo_columnas = {}
        for col in df.columns:
            if col in conteo_columnas:
                conteo_columnas[col] += 1
                columnas_limpias.append(f"{col}.{conteo_columnas[col]}")
            else:
                conteo_columnas[col] = 0
                columnas_limpias.append(col)
        df.columns = columnas_limpias
        
        # Estandarización de Ciudades (Elimina duplicados como PEREIRA / Pereira)
        col_mun = 'Ciudad' if 'Ciudad' in df.columns else df.columns[1]
        if col_mun in df.columns:
            df[col_mun] = df[col_mun].astype(str).str.strip().str.upper()
        
        # Limpieza de columnas numéricas
        cols_num = [
            'Tx Ultimo Semestre', 'Jul 2025 TX', 'Ago 2025 TX', 'Sep 2025 TX', 
            'Oct 2025 TX', 'Nov 2025 TX', 'Dic 2025 TX', 'Ene 2026 TX',
            'Ene 2026 $$', 'Ago 2025 $$', 'Sep 2025 $$', 'Oct 2025 $$', 
            'Nov 2025 $$', 'Dic 2025 $$', 'Transa'
        ]
        
        for col in cols_num:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error técnico al leer el archivo de corresponsales: {e}")
        return None


# 3. CARGA DE DATOS DE CONVENIOS (SOPORTA CSV OPTIMIZADO Y EXCEL ORIGINAL)
@st.cache_data(ttl=3600)
def cargar_datos_convenios():
    archivo_csv = "convenios_activos.csv"
    archivo_excel = "listado-de-convenios-activos-corresponsales mayo 2.xlsx"
    
    # Intenta primero con el CSV optimizado para máxima velocidad
    if os.path.exists(archivo_csv):
        try:
            df_conv = pd.read_csv(archivo_csv, sep=',', encoding='utf-8', on_bad_lines='skip')
            if len(df_conv.columns) <= 1:
                df_conv = pd.read_csv(archivo_csv, sep=';', encoding='latin-1', on_bad_lines='skip')
            df_conv.columns = [str(c).strip() for c in df_conv.columns]
            return df_conv
        except:
            pass

    # Si no se encuentra el CSV, lee directamente el Excel original
    if os.path.exists(archivo_excel):
        try:
            df_conv = pd.read_excel(archivo_excel, sheet_name="Convenios", header=1)
            df_conv.columns = [str(c).strip() for c in df_conv.columns]
            return df_conv
        except Exception as e:
            st.error(f"Error técnico al procesar el Excel de Convenios: {e}")
            return None
    return None


# --- MENÚ LATERAL DE NAVEGACIÓN ---
st.sidebar.title("Navegación")
modulo_seleccionado = st.sidebar.radio(
    "Seleccione el Módulo:", 
    ["📊 Dashboard Corresponsales", "📄 Buscador de Convenios"]
)
st.sidebar.markdown("---")

# Carga global de datos con caché
df = cargar_datos_corresponsales()
df_convenios = cargar_datos_convenios()


# ==========================================
# MÓDULO 1: DASHBOARD DE CORRESPONSALES
# ==========================================
if modulo_seleccionado == "📊 Dashboard Corresponsales":
    if df is not None:
        st.sidebar.header("🔍 Filtros de Gestión")
        
        col_esp = 'ESPECIALISTA' if 'ESPECIALISTA' in df.columns else df.columns[0]
        lista_esp = ["Todos"] + sorted(df[col_esp].dropna().unique().tolist())
        esp_sel = st.sidebar.selectbox("Especialista Comercial:", lista_esp)
        
        col_mun = 'Ciudad' if 'Ciudad' in df.columns else df.columns[1]
        lista_ciu = ["Todos"] + sorted(df[col_mun].dropna().unique().tolist())
        ciu_sel = st.sidebar.selectbox("Municipio / Ciudad:", lista_ciu)
        
        df_f = df.copy()
        if esp_sel != "Todos":
            df_f = df_f[df_f[col_esp] == esp_sel]
        if ciu_sel != "Todos":
            df_f = df_f[df_f[col_mun] == ciu_sel]

        # --- TARJETAS DE MÉTRICAS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(label="👥 Total Corresponsales", value=f"{len(df_f):,}")
        
        tx_sem = 'Tx Ultimo Semestre' if 'Tx Ultimo Semestre' in df_f.columns else 'Transa'
        tx_sum_val = pd.to_numeric(df_f[tx_sem], errors='coerce').fillna(0).sum()
        m2.metric(label="📊 TX Total Semestre", value=f"{tx_sum_val:,.0f}")
        
        activos = len(df_f[df_f['Transa si/no MES'] == 'Si']) if 'Transa si/no MES' in df_f.columns else 0
        m3.metric(label="✅ Puntos Activos", value=f"{activos:,}")
        
        dinero_ene = 'Ene 2026 $$' if 'Ene 2026 $$' in df_f.columns else df_f.columns[-1]
        dinero_sum_val = pd.to_numeric(df_f[dinero_ene], errors='coerce').fillna(0).sum()
        m4.metric(label="💰 Volumen Ene ($$)", value=f"$ {dinero_sum_val:,.0f}")

        # --- GRÁFICOS ---
        st.subheader("Análisis de Transacciones por Mes (Jul 2025
