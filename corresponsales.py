import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

# Estilo para subir los números en los paneles blancos y mejorar visibilidad
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] { 
        background-color: #ffffff; 
        border-left: 5px solid #EBB932; 
        border-radius: 10px; 
        padding: 5px 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    div[data-testid="stMetricLabel"] {
        margin-top: -10px !important;
        margin-bottom: -10px !important;
        font-size: 0.85rem !important;
        font-weight: bold !important;
        color: #666 !important;
    }
    div[data-testid="stMetricValue"] { 
        color: #0033a0 !important; 
        font-size: 2.2rem !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. CARGA DE DATOS (Intento manual de separadores)
@st.cache_data(ttl=60)
def cargar_datos_definitivo():
    # Intentamos con los 3 separadores más comunes en Excel
    for s in [';', ',', '\t']:
        try:
            df = pd.read_csv("datos_corresponsales.csv", sep=s, engine='python', on_bad_lines='skip', encoding_errors='ignore')
            if len(df.columns) > 5:
                # Limpiar nombres de columnas
                df.columns = [str(c).upper().strip() for c in df.columns]
                return df
        except:
            continue
    return None

df = cargar_datos_definitivo()

if df is not None:
    # --- ASIGNACIÓN DE COLUMNAS (Manual y Flexible) ---
    # Buscamos por palabras clave, si no, tomamos posiciones fijas
    col_esp = next((c for c in df.columns if "ESPEC" in c), df.columns[3] if len(df.columns)>3 else df.columns[0])
    col_mun = next((c for c in df.columns if "CIUD" in c or "MUN" in c), df.columns[1])
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c or "TOTAL TX" in c), None)
    col_money = next((c for c in df.columns if "ENE 2026 $$" in c or "ENE 2026 $" in c), None)
    col_estado = next((c for c in df.columns if "ESTADO" in c), None)
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO" in c or "TRANSA SI/NO MES" in c), None)

    # Limpieza de datos numéricos para las columnas encontradas
    for c in [col_tx_total, col_money]:
        if c and c in df.columns:
            df[c] = df[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # --- FILTROS LATERALES ---
    st.sidebar.header("🔍 Consultar Información")
    
    opciones_esp = ["TODOS"] + sorted([str(x) for x in df[col_esp].unique() if str(x) not in ['nan', '0', 'None']])
    esp_sel = st.sidebar.selectbox("Filtro Especialista:", opciones_esp)
    
    opciones_mun = ["TODOS"] + sorted([str(x) for x in df[col_mun].unique() if str(x) not in ['nan', '0', 'None']])
    mun_sel = st.sidebar.selectbox("Filtro Ciudad/Municipio:", opciones_mun)

    # Aplicar Filtros
    df_f = df.copy()
    if esp_sel != "TODOS": df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS": df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS (KPIs) ---
    st.subheader("🚀 Indicadores de Gestión")
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("Puntos Red", f"{len(df_f)}")
    
    val_tx = df_f[col_tx_total].sum() if col_tx_total else 0
    k2.metric("TX Semestre", f"{val_tx:,.0f}")
    
    val_money = df_f[col_money].sum() if col_money else 0
    k3.metric("Monto Ene ($)", f"$ {val_money:,.0f}")
    
    if col_si_no:
        activos = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
        k4.metric("Activos (Si)", activos)
    else:
        k4.metric("Activos", "0")

    # --- PESTAÑAS ---
    t1, t2, t3 = st.tabs(["📊 Segmentación", "🏆 Top 50", "📈 Evolución"])

    with t1:
        c_a, c_b = st.columns(2)
        with c_a:
            if col_estado:
                df_pie = df_f[~df_f[col_estado].astype(str).isin(['0', '0.0', 'nan', 'NAN'])]
                if not df_pie.empty:
                    st.plotly_chart(px.pie(df_pie, names=col_estado, title="Nivel Master/Medio", hole=0.4), use_container_width=True)
        with c_b:
            if col_tx_total:
                top_muns = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(10).reset_index()
                st.plotly_chart(px.bar(top_muns, x=col_tx_total, y=col_mun, orientation='h', title="Top 10 Ciudades"), use_container_width=True)

    with t2:
        if col_tx_total:
            top_50 = df_f.nlargest(50, col_tx_total)
            # Intentamos mostrar columnas que existan
            cols_tab = [c for c in [col_esp, col_mun, 'DIRECCIÓN', col_tx_total] if c in df.columns]
            st.dataframe(top_50[cols_tab], use_container_width=True, hide_index=True)

    with t3:
        # Tendencia básica
        st.info("Gráfico de tendencia basado en los datos filtrados.")
        if col_tx_total:
            fig_evol = px.histogram(df_f, x=col_mun, y=col_tx_total, title="Distribución de TX por Ciudad")
            st.plotly_chart(fig_evol, use_container_width=True)

    st.divider()
    st.subheader("📋 Detalle de Registros")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 Error crítico: El archivo CSV no tiene el formato esperado o el nombre es incorrecto.")
    st.info("Asegúrate de que en GitHub el archivo se llame: datos_corresponsales.csv")
