import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN E IDENTIDAD VISUAL (ESTILOS CORREGIDOS PARA TEXTO INVISIBLE)
st.set_page_config(page_title="BVB - Gestión Estratégica", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    
    /* Fuerza el color del número (azul corporativo) */
    [data-testid="stMetricValue"] { 
        color: #0033a0 !important; 
        font-weight: bold !important; 
    }
    
    /* Fuerza el color del título del cuadro (negro/gris oscuro visible) */
    [data-testid="stMetricLabel"] { 
        color: #222222 !important; 
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    /* Configuración estructural de las tarjetas */
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


# 2. CARGA DE DATOS ORIGINAL DE CORRESPONSALES (BLINDADA)
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


# 3. CARGA DE DATOS DE CONVENIOS OPTIMIZADA (CSV o Excel)
@st.cache_data(ttl=3600)
def cargar_datos_convenios():
    archivo_csv = "convenios_activos.csv"
    archivo_excel = "listado-de-convenios-activos-corresponsales mayo 2.xlsx"
    
    if os.path.exists(archivo_csv):
        try:
            df_conv = pd.read_csv(archivo_csv, sep=',', encoding='utf-8', on_bad_lines='skip')
            if len(df_conv.columns) <= 1:
                df_conv = pd.read_csv(archivo_csv, sep=';', encoding='latin-1', on_bad_lines='skip')
            df_conv.columns = [str(c).strip() for c in df_conv.columns]
            return df_conv
        except:
            pass

    if os.path.exists(archivo_excel):
        try:
            df_conv = pd.read_excel(archivo_excel, sheet_name="Convenios", header=1)
            df_conv.columns = [str(c).strip() for c in df_conv.columns]
            return df_conv
        except:
            return None
    return None


# --- MENÚ LATERAL DE NAVEGACIÓN ---
st.sidebar.title("Navegación")
modulo_seleccionado = st.sidebar.radio(
    "Seleccione el Módulo:", 
    ["📊 Dashboard Corresponsales", "📄 Buscador de Convenios"]
)
st.sidebar.markdown("---")

# Carga de las bases en memoria controlada por Caché
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

        # --- MÉTRICAS DE ALTO NIVEL CON PARÁMETROS EXPLÍCITOS ---
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

        # --- CUERPO GRÁFICO (Estructura Lineal Original) ---
        st.subheader("Análisis de Transacciones por Mes (Jul 2025 - Ene 2026)")
        meses_cols = ['Jul 2025 TX', 'Ago 2025 TX', 'Sep 2025 TX', 'Oct 2025 TX', 'Nov 2025 TX', 'Dic 2025 TX', 'Ene 2026 TX']
        meses_existentes = [m for m in meses_cols if m in df_f.columns]
        
        if meses_existentes:
            data_meses = df_f[meses_existentes].sum().reset_index()
            data_meses.columns = ['Mes', 'Transacciones']
            
            c1, c2 = st.columns([2, 1])
            with c1:
                fig_line = px.line(data_meses, x='Mes', y='Transacciones', markers=True, 
                                   title="Evolución de la Red", color_discrete_sequence=['#0033a0'])
                st.plotly_chart(fig_line, use_container_width=True)
            with c2:
                mun_data = df_f.groupby(col_mun)[tx_sem].sum().nlargest(10).reset_index()
                fig_bar = px.bar(mun_data, x=tx_sem, y=col_mun, orientation='h', 
                                 title="Top 10 Municipios", color_discrete_sequence=['#EBB932'])
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No se encontraron las columnas mensuales de transacciones.")

        st.subheader("🏆 Top 50 Corresponsales con Mejor Desempeño")
        top_50 = df.nlargest(50, tx_sem)
        cols_ranking = [col_esp, col_mun, 'Dirección', tx_sem, 'Ene 2026 TX', 'Estado']
