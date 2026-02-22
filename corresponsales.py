import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN VISUAL
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

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
    /* LETRAS TÍTULOS EN NEGRO */
    div[data-testid="stMetricLabel"] p { 
        color: #000000 !important; 
        font-size: 1.1rem !important; 
        font-weight: 800 !important;
    }
    /* NÚMEROS EN AZUL */
    div[data-testid="stMetricValue"] div { 
        color: #0033a0 !important; 
        font-size: 2.2rem !important; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. CARGA DE DATOS
@st.cache_data(ttl=30)
def cargar_datos_v3():
    archivos = [f for f in os.listdir('.') if f.lower().endswith('.csv')]
    if not archivos: return None
    archivo_final = "datos_corresponsales.csv" if "datos_corresponsales.csv" in archivos else archivos[0]
    
    for s in [';', ',', '\t']:
        try:
            df = pd.read_csv(archivo_final, sep=s, engine='python', on_bad_lines='skip', encoding_errors='ignore')
            if len(df.columns) > 1:
                # Limpiar nombres de columnas
                cols = []
                for i, col in enumerate(df.columns):
                    n = str(col).upper().strip().replace('\n', ' ')
                    cols.append(n if n not in cols else f"{n}_{i}")
                df.columns = cols
                
                # Limpiar números (TX y $$)
                for c in df.columns:
                    if any(x in c for x in ["TX", "$$", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                        df[c] = df[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                return df
        except: continue
    return None

df = cargar_datos_v3()

if df is not None:
    # --- IDENTIFICAR COLUMNAS ---
    def f_col(keys, d): return next((c for c in df.columns if any(k in c for k in keys)), df.columns[d])
    
    c_esp = f_col(["ESPEC"], 3)
    c_mun = f_col(["CIUD", "MUN"], 1)
    c_dep = f_col(["DEP"], 2)
    c_tx_tot = f_col(["TX ULTIMO SEMESTRE", "TOTAL TX"], -1)
    c_val_tot = f_col(["ENE 2026 $$", "ENE 2026 $"], -2)
    c_estado = f_col(["ESTADO"], 8)

    # --- FILTROS EN CASCADA ---
    st.sidebar.header("🔍 Filtros Inteligentes")
    
    # Filtro Especialista
    lista_esp = ["TODOS"] + sorted([str(x) for x in df[c_esp].unique() if str(x) not in ['nan', '0']])
    esp_sel = st.sidebar.selectbox("Seleccione Especialista:", lista_esp)
    
    # Filtrar DF para que el siguiente desplegable solo muestre lo que corresponde
    df_temp = df.copy()
    if esp_sel != "TODOS":
        df_temp = df_temp[df_temp[c_esp] == esp_sel]
    
    # Filtro Municipio (Solo muestra los del especialista seleccionado)
    lista_mun = ["TODOS"] + sorted([str(x) for x in df_temp[c_mun].unique() if str(x) not in ['nan', '0']])
    mun_sel = st.sidebar.selectbox("Seleccione Ciudad/Municipio:", lista_mun)

    # Aplicar filtros finales
    df_f = df_temp.copy()
    if mun_sel != "TODOS":
        df_f = df_f[df_f[c_mun] == mun_sel]

    # --- KPIs ---
    st.subheader("🚀 Resumen Ejecutivo")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Corresponsales", f"{len(df_f)}")
    k2.metric("TX Totales", f"{df_f[c_tx_tot].sum():,.0f}")
    k3.metric("Monto Total ($)", f"$ {df_f[c_val_tot].sum():,.0f}")
    
    # Departamento del primer registro (o "Varios")
    dep_text = df_f[c_dep].iloc[0] if len(df_f[c_dep].unique()) == 1 else "Múltiples"
    k4.metric("Departamento", dep_text)

    # --- ANÁLISIS MENSUAL ---
    st.divider()
    st.subheader("📈 Evolución Mensual (Jul 2025 - Ene 2026)")
    
    meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
    data_mensual = []
    
    for m in meses:
        col_tx = next((c for c in df.columns if m in c and "TX" in c), None)
        col_val = next((c for c in df.columns if m in c and ("$" in c or "MONTO" in c or "VALOR" in c)), None)
        
        if col_tx or col_val:
            data_mensual.append({
                "Mes": m,
                "Cantidad (TX)": df_f[col_tx].sum() if col_tx else 0,
                "Valor ($$)": df_f[col_val].sum() if col_val else 0
            })
    
    df_mes = pd.DataFrame(data_mensual)
    if not df_mes.empty:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.plotly_chart(px.line(df_mes, x="Mes", y="Cantidad (TX)", markers=True, title="Transacciones por Mes", color_discrete_sequence=['#EBB932']), use_container_width=True)
        with col_m2:
            st.plotly_chart(px.bar(df_mes, x="Mes", y="Valor ($$)", title="Dinero Movilizado por Mes", color_discrete_sequence=['#0033a0']), use_container_width=True)

    # --- PESTAÑAS ---
    t1, t2 = st.tabs(["🏆 Ranking Top 50 Corresponsales", "📋 Base de Datos Completa"])
    
    with t1:
        st.subheader("Top 50 por Volumen de Transacciones")
        top_50 = df_f.sort_values(by=c_tx_tot, ascending=False).head(50)
        st.dataframe(top_50[[c_esp, c_dep, c_mun, c_tx_tot, c_val_tot]], use_container_width=True, hide_index=True)

    with t2:
        st.dataframe(df_f, use_container_width=True)

else:
    st.error("🚨 Sube el archivo 'datos_corresponsales.csv' a tu GitHub.")
