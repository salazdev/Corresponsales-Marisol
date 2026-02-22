import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="BVB - Gestión Comercial", layout="wide")

# Estilo para subir los números en los paneles blancos
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
    }
    div[data-testid="stMetricLabel"] {
        margin-bottom: -20px !important; /* Sube el título */
        font-size: 0.85rem !important;
        font-weight: bold !important;
        color: #666 !important;
    }
    div[data-testid="stMetricValue"] { 
        color: #0033a0 !important; 
        font-size: 2rem !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Panel de Gestión Comercial BVB")

# 2. MOTOR DE CARGA CON BÚSQUEDA AGRESIVA
@st.cache_data(ttl=60)
def cargar_datos_vincular():
    try:
        # Probamos leer el archivo ignorando filas corruptas
        df = pd.read_csv("datos_corresponsales.csv", sep=None, engine='python', on_bad_lines='skip', encoding_errors='ignore')
        
        # Limpiamos nombres de columnas quitando espacios y saltos de línea
        df.columns = [str(c).upper().strip() for c in df.columns]
        
        # Limpiar datos numéricos ($ y comas)
        for col in df.columns:
            if any(x in col for x in ["TX", "$$", "ENE", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]):
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except:
        return None

df = cargar_datos_vincular()

if df is not None:
    # --- BUSCADOR DE COLUMNAS "CIEGO" ---
    # Buscamos la columna que contenga "ESPEC" para Especialistas
    col_esp = next((c for c in df.columns if "ESPEC" in c), df.columns[0])
    # Buscamos la columna que contenga "CIUD" o "MUN" para Ciudades
    col_mun = next((c for c in df.columns if "CIUD" in c or "MUNIC" in c), df.columns[1])
    # Otros datos
    col_tx_total = next((c for c in df.columns if "TX ULTIMO SEMESTRE" in c or "TOTAL TX" in c), None)
    col_money = next((c for c in df.columns if "ENE 2026 $$" in c or "ENE 2026 $" in c), None)
    col_estado = next((c for c in df.columns if "ESTADO" in c), None)
    col_si_no = next((c for c in df.columns if "TRANSA SI/NO MES" in c), None)

    # --- FILTROS LATERALES ---
    st.sidebar.header("🔍 Consultar Información")
    
    # Lista de Especialistas
    opciones_esp = ["TODOS"] + sorted([str(x) for x in df[col_esp].unique() if str(x) != 'nan' and str(x) != '0'])
    esp_sel = st.sidebar.selectbox("Seleccione Especialista:", opciones_esp)
    
    # Lista de Ciudades
    opciones_mun = ["TODOS"] + sorted([str(x) for x in df[col_mun].unique() if str(x) != 'nan' and str(x) != '0'])
    mun_sel = st.sidebar.selectbox("Seleccione Ciudad/Municipio:", opciones_mun)

    # Aplicar Filtros
    df_f = df.copy()
    if esp_sel != "TODOS":
        df_f = df_f[df_f[col_esp] == esp_sel]
    if mun_sel != "TODOS":
        df_f = df_f[df_f[col_mun] == mun_sel]

    # --- MÉTRICAS (KPIs) ---
    st.subheader("🚀 Indicadores Seleccionados")
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("Puntos Red", f"{len(df_f)}")
    
    val_tx = df_f[col_tx_total].sum() if col_tx_total else 0
    k2.metric("TX Semestre (Cant)", f"{val_tx:,.0f}")
    
    val_money = df_f[col_money].sum() if col_money else 0
    k3.metric("Monto Ene ($$)", f"$ {val_money:,.0f}")
    
    if col_si_no:
        activos = len(df_f[df_f[col_si_no].astype(str).str.upper().str.contains("SI")])
        k4.metric("Activos (Si)", activos)
    else:
        k4.metric("Activos", "0")

    # --- PESTAÑAS ---
    t1, t2, t3 = st.tabs(["📊 Segmentación", "🏆 Ranking Top 50", "📈 Tendencia"])

    with t1:
        c_a, c_b = st.columns(2)
        with c_a:
            if col_estado:
                # Quitamos los '0' para que el gráfico no se ensucie
                df_pie = df_f[~df_f[col_estado].astype(str).isin(['0', '0.0', 'nan', 'NAN'])]
                if not df_pie.empty:
                    st.plotly_chart(px.pie(df_pie, names=col_estado, title="Nivel Master/Medio", hole=0.4), use_container_width=True)
        with c_b:
            if col_tx_total:
                top_muns = df_f.groupby(col_mun)[col_tx_total].sum().nlargest(10).reset_index()
                st.plotly_chart(px.bar(top_muns, x=col_tx_total, y=col_mun, orientation='h', title="Top Municipios"), use_container_width=True)

    with t2:
        if col_tx_total:
            top_50 = df_f.nlargest(50, col_tx_total)
            st.dataframe(top_50[[col_esp, col_mun, col_tx_total]], use_container_width=True, hide_index=True)

    with t3:
        # Gráfico de tendencia
        meses = ["JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE"]
        datos_linea = []
        for m in meses:
            c_m = next((c for c in df.columns if m in c and "TX" in c), None)
            if c_m:
                datos_linea.append({"Mes": m, "TX": df_f[c_m].sum()})
        if datos_linea:
            st.plotly_chart(px.line(pd.DataFrame(datos_linea), x="Mes", y="TX", markers=True, title="Evolución TX"), use_container_width=True)

    st.divider()
    st.subheader("📋 Detalle de la Operación")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

else:
    st.error("🚨 No se pudo leer la lista de especialistas. Revisa el archivo 'datos_corresponsales.csv'.")
