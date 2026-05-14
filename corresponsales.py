import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. --- ENCABEZADO DE MARCA ESTILIZADO ---
st.markdown("""
    <div style="text-align: left;">
        <h2 style="margin-bottom: 0px; color: #3A3A3A; letter-spacing: 2px;">Salaz Analytics</h2>
        <p style="font-size: 14px; color: #00eb93; margin-top: 0px; text-transform: uppercase;">Soluciones de Inteligencia de Negocios</p>
    </div>
""", unsafe_allow_html=True)
st.divider()

# ESTILO: Color de letras NEGRO absoluto para títulos de métricas
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff !important; 
        border-left: 5px solid #EBB932 !important; 
        border-radius: 10px !important; 
        padding: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; 
        height: 120px !important;
    }
    /* TÍTULOS EN NEGRO ABSOLUTO (Línea solicitada) */
    [data-testid="stMetricLabel"] p { 
        color: #000000 !important; 
        font-size: 1.1rem !important; 
        font-weight: 800 !important;
        opacity: 1 !important;
    }
    /* NÚMEROS EN AZUL Banco de Bogotá */
    [data-testid="stMetricValue"] div { 
        color: #0033a0 !important; 
        font-size: 2.2rem !important; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial Banco de Bogotá")

# 2. CARGA Y DES-DUPLICACIÓN DE COLUMNAS
@st.cache_data(ttl=30)
def cargar_y_limpiar_datos():
    archivo = "PUNTOS EJE CAFETERO.xlsx"
    if not os.path.exists(archivo): return None
    
    try:
        # CAMBIO CLAVE: Leer como Excel
        df = pd.read_excel(archivo)
        
        # Normalización de columnas
        df.columns = [str(c).replace('\n', ' ').strip().upper() for c in df.columns]
        
        # Eliminar posibles duplicados en los nombres de columnas
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
        df.columns = cols

        # Limpiar datos numéricos
        for c in df.columns:
            if any(x in c for x in ["TX", "$$", "TOTAL"]):
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

df = cargar_y_limpiar_datos()

if df is not None:
    # 1. ASIGNACIÓN DE COLUMNAS (Indispensable definir esto antes de usar los filtros)
    # Estos nombres deben coincidir exactamente con los de tu archivo Excel
    c_dep = "DEPARTAMENTO"
    c_esp = "ESPECIALISTA"
    c_mun = "CIUDAD"
    c_tx_tot = "TX ULTIMO SEMESTRE"
    c_val_ene = "ENE 2026 $$"

    # Línea de diagnóstico temporal
    st.write("Columnas detectadas:", list(df.columns))

    # --- FILTROS EN CASCADA ---
    st.sidebar.header("🔍 Filtros de Gestión")
    
    # Departamento
    l_dep = ["TODOS"] + sorted([str(x) for x in df[c_dep].unique() if str(x) != 'nan'])
    dep_sel = st.sidebar.selectbox("1. Departamento:", l_dep)
    df_f1 = df if dep_sel == "TODOS" else df[df[c_dep] == dep_sel]

    # Especialista
    l_esp = ["TODOS"] + sorted([str(x) for x in df_f1[c_esp].unique() if str(x) != 'nan'])
    esp_sel = st.sidebar.selectbox("2. Especialista:", l_esp)
    df_f2 = df_f1 if esp_sel == "TODOS" else df_f1[df_f1[c_esp] == esp_sel]

    # Ciudad
    l_mun = ["TODOS"] + sorted([str(x) for x in df_f2[c_mun].unique() if str(x) != 'nan'])
    mun_sel = st.sidebar.selectbox("3. Ciudad/Municipio:", l_mun)
    df_final = df_f2 if mun_sel == "TODOS" else df_f2[df_f2[c_mun] == mun_sel]

    # --- KPIs (MONTO EN MILLONES) ---
    st.subheader("🚀 Indicadores de Desempeño")
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("Puntos Red", f"{len(df_final)}")
    
    # Sumatoria de Cantidades
    cant_tx = df_final[c_tx_tot].sum() if c_tx_tot in df_final.columns else 0
    k2.metric("Cantidades (TX)", f"{cant_tx:,.0f}")
    
    # Monto en Millones
    monto_val = df_final[c_val_ene].sum() if c_val_ene in df_final.columns else 0
    k3.metric("Monto Ene 26 (Mill)", f"$ {monto_val / 1_000_000:,.1f} M")
    
    k4.metric("Región", dep_sel if dep_sel != "TODOS" else "Nacional")

    # --- ANÁLISIS MENSUAL ---
    st.divider()
    st.subheader("📈 Evolución Mensual (Julio 2025 - Enero 2026)")
    
    meses_map = {
        "JUL": ("JUL 2025 TX", "JUL 2025 $$"),
        "AGO": ("AGO 2025 TX", "AGO 2025 $$"),
        "SEP": ("SEP 2025 TX", "SEP 2025 $$"),
        "OCT": ("OCT 2025 TX", "OCT 2025 $$"),
        "NOV": ("NOV 2025 TX", "NOV 2025 $$"),
        "DIC": ("DIC 2025 TX", "DIC  2025 $$"),
        "ENE": ("ENE 2026 TX", "ENE 2026 $$")
    }
    
    hist_data = []
    for m, (tx, val) in meses_map.items():
        if tx in df.columns and val in df.columns:
            hist_data.append({
                "Mes": m,
                "Cantidad (TX)": df_final[tx].sum(),
                "Valor ($)": df_final[val].sum()
            })
    
    if hist_data:
        df_h = pd.DataFrame(hist_data)
        c_bar, c_line = st.columns(2)
        with c_bar:
            st.plotly_chart(px.bar(df_h, x="Mes", y="Cantidad (TX)", title="Cantidades por Mes", color_discrete_sequence=['#0033a0']), use_container_width=True)
        with c_line:
            st.plotly_chart(px.line(df_h, x="Mes", y="Valor ($)", markers=True, title="Valores por Mes", color_discrete_sequence=['#EBB932']), use_container_width=True)

    # --- TABLAS ---
    st.divider()
    t1, t2 = st.tabs(["🏆 Ranking Top 50", "📋 Detalle de Registros"])
    with t1:
        cols_ver = [c_dep, c_esp, c_mun, c_tx_tot, c_val_ene]
        # Verificamos que las columnas existan antes de mostrar el ranking
        cols_existentes = [c for c in cols_ver if c in df_final.columns]
        ranking = df_final.sort_values(c_tx_tot, ascending=False).head(50)
        st.dataframe(ranking[cols_existentes], use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(df_final, use_container_width=True)

    # --- PIE DE PÁGINA DE MARCA ---
    st.markdown("---")
    st.caption("SALAZ ANALYTICS Plataforma Inteligente de Gestión")

else:
    st.warning("⚠️ Esperando carga de datos. Asegúrate de que el archivo Excel esté en la carpeta del proyecto.")
