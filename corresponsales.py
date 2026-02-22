import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN VISUAL
st.set_page_config(page_title="Banco de Bogotá - Gestión Comercial", layout="wide")

st.markdown("""
    <style>
    /* 1. Fondo del panel y borde */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border-left: 5px solid #EBB932 !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }

    /* 2. TÍTULOS EN NEGRO (Lo que necesitas) */
    /* Apuntamos directamente al párrafo del label */
    [data-testid="stMetricLabel"] p {
        color: #000000 !important; /* Negro absoluto */
        font-weight: 800 !important; /* Grosor de letra alto */
        font-size: 1.1rem !important;
        opacity: 1 !important; /* Evita que se vea grisáceo */
    }

    /* 3. NÚMEROS (VALORES) EN AZUL */
    [data-testid="stMetricValue"] div {
        color: #0033a0 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial Banco de Bogotá")

# 2. CARGA Y LIMPIEZA (Adaptado a tu archivo real)
@st.cache_data(ttl=30)
def cargar_datos_reales():
    archivo = "datos_corresponsales.csv"
    if not os.path.exists(archivo): return None
    
    try:
        # Cargamos el archivo
        df = pd.read_csv(archivo, sep=',', engine='python', on_bad_lines='skip', encoding_errors='ignore')
        
        # LIMPIEZA CRÍTICA: Quitamos saltos de línea (\n) y espacios de los títulos
        df.columns = [str(c).replace('\n', ' ').strip().upper() for c in df.columns]
        
        # Limpiar números de las columnas de TX y $$
        columnas_numericas = [c for c in df.columns if any(m in c for m in ["TX", "$$", "TOTAL"])]
        for c in columnas_numericas:
            df[c] = df[c].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Error al procesar: {e}")
        return None

df = cargar_datos_reales()

if df is not None:
    # --- ASIGNACIÓN DE COLUMNAS REALES ---
    c_dep = "DEPARTAMENTO"
    c_esp = "ESPECIALISTA"
    c_mun = "CIUDAD"
    c_tx_tot = "TX ULTIMO SEMESTRE"
    c_val_tot = "ENE 2026 $$"

    # --- FILTROS EN CASCADA ---
    st.sidebar.header("🔍 Filtros de Gestión")
    
    # 1. Departamento
    l_dep = ["TODOS"] + sorted([str(x) for x in df[c_dep].unique() if str(x) != 'nan'])
    dep_sel = st.sidebar.selectbox("1. Departamento:", l_dep)
    
    df_f1 = df if dep_sel == "TODOS" else df[df[c_dep] == dep_sel]

    # 2. Especialista (Solo los del departamento)
    l_esp = ["TODOS"] + sorted([str(x) for x in df_f1[c_esp].unique() if str(x) != 'nan'])
    esp_sel = st.sidebar.selectbox("2. Especialista:", l_esp)
    
    df_f2 = df_f1 if esp_sel == "TODOS" else df_f1[df_f1[c_esp] == esp_sel]

    # 3. Ciudad (Solo las del especialista)
    l_mun = ["TODOS"] + sorted([str(x) for x in df_f2[c_mun].unique() if str(x) != 'nan'])
    mun_sel = st.sidebar.selectbox("3. Ciudad/Municipio:", l_mun)

    df_final = df_f2 if mun_sel == "TODOS" else df_f2[df_f2[c_mun] == mun_sel]

    # --- KPIs ---
    st.subheader("🚀 Indicadores Seleccionados")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Corresponsales", f"{len(df_final)}")
    k2.metric("Total TX (Semestre)", f"{df_final[c_tx_tot].sum():,.0f}")
    k3.metric("Monto Ene 2026", f"$ {df_final[c_val_tot].sum():,.0f}")
    k4.metric("Filtro Activo", dep_sel if dep_sel != "TODOS" else "Nacional")

    # --- ANÁLISIS MENSUAL ---
    st.divider()
    st.subheader("📅 Histórico Mensual (Cantidades vs Valores)")
    
    # Mapeo de columnas según tu archivo
    meses_map = {
        "JUL": ("JUL 2025 TX", "JUL 2025 $$"),
        "AGO": ("AGO 2025 TX", "AGO 2025 $$"),
        "SEP": ("SEP 2025 TX", "SEP 2025 $$"),
        "OCT": ("OCT 2025 TX", "OCT 2025 $$"),
        "NOV": ("NOV 2025 TX", "NOV 2025 $$"),
        "DIC": ("DIC 2025 TX", "DIC 2025 $$"),
        "ENE": ("ENE 2026 TX", "ENE 2026 $$")
    }
    
    data_h = []
    for mes, (col_tx, col_val) in meses_map.items():
        if col_tx in df.columns and col_val in df.columns:
            data_h.append({
                "Mes": mes,
                "Cantidad (TX)": df_final[col_tx].sum(),
                "Valor ($)": df_final[col_val].sum()
            })
    
    if data_h:
        df_h = pd.DataFrame(data_h)
        c_i, c_d = st.columns(2)
        with c_i:
            st.plotly_chart(px.bar(df_h, x="Mes", y="Cantidad (TX)", title="Transacciones por Mes", color_discrete_sequence=['#0033a0']), use_container_width=True)
        with c_d:
            st.plotly_chart(px.line(df_h, x="Mes", y="Valor ($)", markers=True, title="Valores por Mes", color_discrete_sequence=['#EBB932']), use_container_width=True)

    # --- TABLAS ---
    st.divider()
    t1, t2 = st.tabs(["🏆 Top 50 Corresponsales", "📋 Ver todo"])
    with t1:
        st.dataframe(df_final.sort_values(c_tx_tot, ascending=False).head(50)[[c_esp, c_dep, c_mun, c_tx_tot, c_val_tot]], use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(df_final, use_container_width=True)

else:
    st.warning("⚠️ Esperando archivo 'datos_corresponsales.csv'...")

