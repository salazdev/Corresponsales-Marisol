import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Salaz Analytics - Gestión Comercial", layout="wide")

# 1. --- ENCABEZADO DE MARCA ESTILIZADO ---
st.markdown("""
    <div style="text-align: left;">
        <h2 style="margin-bottom: 0px; color: #3A3A3A; letter-spacing: 2px;">SALAZ ANALYTICS</h2>
        <p style="font-size: 14px; color: #00eb93; margin-top: 0px; text-transform: uppercase;">Plataforma Inteligente de Gestión</p>
    </div>
""", unsafe_allow_html=True)
st.divider()

# ESTILO CSS: Métricas y Colores Corporativos
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
    [data-testid="stMetricLabel"] p { 
        color: #000000 !important; 
        font-size: 1.1rem !important; 
        font-weight: 800 !important;
    }
    [data-testid="stMetricValue"] div { 
        color: #0033a0 !important; 
        font-size: 2.2rem !important; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial Banco de Bogotá")

# 2. CARGA Y LIMPIEZA DE DATOS
@st.cache_data(ttl=30)
def cargar_y_limpiar_datos():
    archivo = "PUNTOS EJE CAFETERO.xlsx"
    if not os.path.exists(archivo): return None
    
    try:
        # Carga de Excel
        df = pd.read_excel(archivo)
        
        # Normalización de nombres de columnas (Mayúsculas y sin espacios raros)
        df.columns = [str(c).replace('\n', ' ').strip().upper() for c in df.columns]
        
        # Manejo de columnas duplicadas
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
        df.columns = cols

        # Limpieza de valores numéricos en columnas de interés
        for c in df.columns:
            if any(x in c for x in ["TX", "$$", "TOTAL"]):
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

df = cargar_y_limpiar_datos()

if df is not None:
    # 3. IDENTIFICACIÓN DINÁMICA DE COLUMNAS (Para evitar KeyErrors)
    # Buscamos columnas que contengan las palabras clave
    c_dep = next((c for c in df.columns if "DEP" in c), "DEPARTAMENTO")
    c_esp = next((c for c in df.columns if "ESP" in c), "ESPECIALISTA")
    c_mun = next((c for c in df.columns if "CIUDAD" in c or "MUN" in c), "CIUDAD")
    
    # Búsqueda flexible para Transacciones (TX) y Valores ($$)
    c_tx_tot = next((c for c in df.columns if "TX" in c and "ULT" in c), None)
    if not c_tx_tot: c_tx_tot = next((c for c in df.columns if "TX" in c), df.columns[0])
    
    c_val_ene = next((c for c in df.columns if "2026 $$" in c or "ENE 2026 $$" in c), None)
    if not c_val_ene: c_val_ene = next((c for c in df.columns if "$$" in c), df.columns[-1])

    # --- FILTROS EN CASCADA ---
    st.sidebar.header("🔍 Filtros de Gestión")
    
    l_dep = ["TODOS"] + sorted([str(x) for x in df[c_dep].unique() if str(x) != 'nan'])
    dep_sel = st.sidebar.selectbox("1. Departamento:", l_dep)
    df_f1 = df if dep_sel == "TODOS" else df[df[c_dep] == dep_sel]

    l_esp = ["TODOS"] + sorted([str(x) for x in df_f1[c_esp].unique() if str(x) != 'nan'])
    esp_sel = st.sidebar.selectbox("2. Especialista:", l_esp)
    df_f2 = df_f1 if esp_sel == "TODOS" else df_f1[df_f1[c_esp] == esp_sel]

    l_mun = ["TODOS"] + sorted([str(x) for x in df_f2[c_mun].unique() if str(x) != 'nan'])
    mun_sel = st.sidebar.selectbox("3. Ciudad/Municipio:", l_mun)
    df_final = df_f2 if mun_sel == "TODOS" else df_f2[df_f2[c_mun] == mun_sel]

    # --- KPIs ---
    st.subheader("🚀 Indicadores de Desempeño")
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("Puntos Red", f"{len(df_final)}")
    
    cant_tx = df_final[c_tx_tot].sum()
    k2.metric("Cantidades (TX)", f"{cant_tx:,.0f}")
    
    monto_val = df_final[c_val_ene].sum()
    k3.metric("Monto Ene 26 (Mill)", f"$ {monto_val / 1_000_000:,.1f} M")
    
    k4.metric("Región", dep_sel if dep_sel != "TODOS" else "Nacional")

    # --- ANÁLISIS MENSUAL ---
    st.divider()
    st.subheader("📈 Evolución Mensual (Julio 2025 - Enero 2026)")
    
    # Mapeo de columnas para el gráfico (se adapta si hay tildes)
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
        # Verificación flexible de nombres de mes
        col_tx = next((c for c in df.columns if m in c and "TX" in c), None)
        col_val = next((c for c in df.columns if m in c and "$$" in c), None)
        
        if col_tx and col_val:
            hist_data.append({
                "Mes": m,
                "Cantidad (TX)": df_final[col_tx].sum(),
                "Valor ($)": df_final[col_val].sum()
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
        cols_ver = [c for c in [c_dep, c_esp, c_mun, c_tx_tot, c_val_ene] if c in df_final.columns]
        ranking = df_final.sort_values(c_tx_tot, ascending=False).head(50)
        st.dataframe(ranking[cols_ver], use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(df_final, use_container_width=True)

    # --- PIE DE PÁGINA ---
    st.markdown("---")
    st.caption("SALAZ ANALYTICS Plataforma Inteligente de Gestión")

else:
    st.warning("⚠️ No se encontró el archivo 'PUNTOS EJE CAFETERO.xlsx'. Por favor verifica que el nombre sea exacto y esté en GitHub.")
