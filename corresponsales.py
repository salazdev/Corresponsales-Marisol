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
    /* LETRAS TÍTULOS EN NEGRO ABSOLUTO */
    div[data-testid="stMetricLabel"] p { 
        color: #000000 !important; 
        font-size: 1.1rem !important; 
        font-weight: 800 !important;
        opacity: 1 !important;
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
def cargar_datos_v4():
    archivos = [f for f in os.listdir('.') if f.lower().endswith('.csv')]
    if not archivos: return None
    archivo_final = "datos_corresponsales.csv" if "datos_corresponsales.csv" in archivos else archivos[0]
    
    for s in [';', ',', '\t']:
        try:
            df = pd.read_csv(archivo_final, sep=s, engine='python', on_bad_lines='skip', encoding_errors='ignore')
            if len(df.columns) > 1:
                cols = []
                for i, col in enumerate(df.columns):
                    n = str(col).upper().strip().replace('\n', ' ')
                    cols.append(n if n not in cols else f"{n}_{i}")
                df.columns = cols
                
                # Limpiar números
                for c in df.columns:
                    if any(x in c for x in ["TX", "$$", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]):
                        df[c] = df[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                return df
        except: continue
    return None

df = cargar_datos_v4()

if df is not None:
    # --- IDENTIFICAR COLUMNAS ---
    def f_col(keys, d): return next((c for c in df.columns if any(k in c for k in keys)), df.columns[d])
    
    c_dep = f_col(["DEP"], 2)
    c_esp = f_col(["ESPEC"], 3)
    c_mun = f_col(["CIUD", "MUN"], 1)
    c_tx_tot = f_col(["TX ULTIMO SEMESTRE", "TOTAL TX"], -1)
    c_val_tot = f_col(["ENE 2026 $$", "ENE 2026 $"], -2)

    # --- FILTROS EN CASCADA ---
    st.sidebar.header("🔍 Filtros de Territorio")
    
    # 1. Filtro Departamento
    lista_dep = ["TODOS"] + sorted([str(x) for x in df[c_dep].unique() if str(x) not in ['nan', '0']])
    dep_sel = st.sidebar.selectbox("Seleccione Departamento:", lista_dep)
    
    df_f1 = df.copy()
    if dep_sel != "TODOS": df_f1 = df_f1[df_f1[c_dep] == dep_sel]

    # 2. Filtro Especialista (Basado en Departamento)
    lista_esp = ["TODOS"] + sorted([str(x) for x in df_f1[c_esp].unique() if str(x) not in ['nan', '0']])
    esp_sel = st.sidebar.selectbox("Seleccione Especialista:", lista_esp)
    
    df_f2 = df_f1.copy()
    if esp_sel != "TODOS": df_f2 = df_f2[df_f2[c_esp] == esp_sel]

    # 3. Filtro Municipio (Basado en Especialista)
    lista_mun = ["TODOS"] + sorted([str(x) for x in df_f2[c_mun].unique() if str(x) not in ['nan', '0']])
    mun_sel = st.sidebar.selectbox("Seleccione Ciudad/Municipio:", lista_mun)

    df_final = df_f2.copy()
    if mun_sel != "TODOS": df_final = df_final[df_final[c_mun] == mun_sel]

    # --- KPIs ---
    st.subheader("🚀 Indicadores de Desempeño")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Puntos Red", f"{len(df_final)}")
    k2.metric("Cantidades (TX)", f"{df_final[c_tx_tot].sum():,.0f}")
    k3.metric("Valores (Monto)", f"$ {df_final[c_val_tot].sum():,.0f}")
    k4.metric("Departamento", dep_sel if dep_sel != "TODOS" else "Nacional")

    # --- ANÁLISIS MENSUAL DESDE JULIO 2025 ---
    st.divider()
    st.subheader("📈 Comportamiento Mensual (Cantidades vs Valores)")
    
    meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
    data_m = []
    for m in meses:
        # Buscamos columnas de cantidad y valor para cada mes
        c_t = next((c for c in df.columns if m in c and ("TX" in c or "CANT" in c)), None)
        c_v = next((c for c in df.columns if m in c and ("$" in c or "VALOR" in c or "MONTO" in c)), None)
        if c_t or c_v:
            data_m.append({
                "Mes": f"{m} 2025" if m != "ENE" else "ENE 2026",
                "Cantidades (TX)": df_final[c_t].sum() if c_t else 0,
                "Valores ($)": df_final[c_v].sum() if c_v else 0
            })

    if data_m:
        df_plot = pd.DataFrame(data_m)
        c_izq, c_der = st.columns(2)
        with c_izq:
            st.plotly_chart(px.bar(df_plot, x="Mes", y="Cantidades (TX)", title="Evolución en Cantidades", color_discrete_sequence=['#0033a0']), use_container_width=True)
        with c_der:
            st.plotly_chart(px.line(df_plot, x="Mes", y="Valores ($)", markers=True, title="Evolución en Valores (Pesos)", color_discrete_sequence=['#EBB932']), use_container_width=True)

    # --- TABLAS ---
    t1, t2 = st.tabs(["🏆 Ranking Top 50", "📋 Detalle Completo"])
    with t1:
        st.subheader("Ranking por Cantidad de Transacciones")
        top_50 = df_final.sort_values(by=c_tx_tot, ascending=False).head(50)
        st.dataframe(top_50[[c_dep, c_esp, c_mun, c_tx_tot, c_val_tot]], use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(df_final, use_container_width=True)

else:
    st.error("🚨 Sube el archivo CSV a GitHub para visualizar el panel.")
