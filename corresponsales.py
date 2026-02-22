import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN E IDENTIDAD VISUAL
st.set_page_config(page_title="BVB - Gestión Estratégica", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stMetricValue"] { color: #0033a0 !important; font-weight: bold; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-left: 5px solid #EBB932;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Gestión Integral de Corresponsalía BVB")

# 2. CARGA DE DATOS BLINDADA (Soluciona el error de Delimiter)
@st.cache_data(ttl=600)
def cargar_datos():
    try:
        # Intentamos leer primero con coma, si falla probamos punto y coma
        try:
            df = pd.read_csv("datos_corresponsales.csv", sep=',', engine='python', on_bad_lines='skip')
            if len(df.columns) <= 1: # Si solo detecta una columna, el separador es incorrecto
                raise ValueError
        except:
            df = pd.read_csv("datos_corresponsales.csv", sep=';', engine='python', on_bad_lines='skip')
        
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Lista de columnas financieras y de transacciones según tu lista
        cols_num = [
            'Tx Ultimo Semestre', 'Jul 2025 TX', 'Ago 2025 TX', 'Sep 2025 TX', 
            'Oct 2025 TX', 'Nov 2025 TX', 'Dic 2025 TX', 'Ene 2026 TX',
            'Ene 2026 $$', 'Ago 2025 $$', 'Sep 2025 $$', 'Oct 2025 $$', 
            'Nov 2025 $$', 'Dic 2025 $$', 'Transa'
        ]
        
        for col in cols_num:
            if col in df.columns:
                # Quitamos símbolos de pesos, espacios y comas para que sean números reales
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error técnico al leer el archivo: {e}")
        return None

df = cargar_datos()

if df is not None:
    # --- FILTROS LATERALES ---
    st.sidebar.header("🔍 Filtros de Gestión")
    
    # Filtro Especialista
    col_esp = 'ESPECIALISTA' if 'ESPECIALISTA' in df.columns else df.columns[0]
    lista_esp = ["Todos"] + sorted(df[col_esp].dropna().unique().tolist())
    esp_sel = st.sidebar.selectbox("Especialista Comercial:", lista_esp)
    
    # Filtro Municipio
    col_mun = 'Ciudad' if 'Ciudad' in df.columns else df.columns[1]
    lista_ciu = ["Todos"] + sorted(df[col_mun].dropna().unique().tolist())
    ciu_sel = st.sidebar.selectbox("Municipio / Ciudad:", lista_ciu)
    
    # Aplicar Filtros
    df_f = df.copy()
    if esp_sel != "Todos":
        df_f = df_f[df_f[col_esp] == esp_sel]
    if ciu_sel != "Todos":
        df_f = df_f[df_f[col_mun] == ciu_sel]

    # --- MÉTRICAS DE ALTO NIVEL ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Corresponsales", f"{len(df_f):,}")
    
    tx_sem = 'Tx Ultimo Semestre' if 'Tx Ultimo Semestre' in df_f.columns else 'Transa'
    m2.metric("TX Total Semestre", f"{df_f[tx_sem].sum():,.0f}")
    
    # Estado (Activos vs Inactivos)
    activos = len(df_f[df_f['Transa si/no MES'] == 'Si']) if 'Transa si/no MES' in df_f.columns else 0
    m3.metric("Puntos Activos", f"{activos:,}")
    
    dinero_ene = 'Ene 2026 $$' if 'Ene 2026 $$' in df_f.columns else df_f.columns[-1]
    m4.metric("Volumen Ene ($$)", f"$ {df_f[dinero_ene].sum():,.0f}")

    # --- CUERPO DEL DASHBOARD ---
    tab1, tab2, tab3 = st.tabs(["📈 Tendencia Semestral", "🏆 Ranking Top 50", "🔎 Consulta Detallada"])

    with tab1:
        st.subheader("Análisis de Transacciones por Mes (Jul 2025 - Ene 2026)")
        
        # Consolidar meses para gráfico
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
                # Análisis por Municipio
                mun_data = df_f.groupby(col_mun)[tx_sem].sum().nlargest(10).reset_index()
                fig_bar = px.bar(mun_data, x=tx_sem, y=col_mun, orientation='h', 
                                 title="Top 10 Municipios", color_discrete_sequence=['#EBB932'])
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No se encontraron las columnas mensuales de transacciones.")

    with tab2:
        st.subheader("🏆 Top 50 Corresponsales con Mejor Desempeño")
        st.write("Ubicación y volumen transaccional de los mejores clientes.")
        
        top_50 = df.nlargest(50, tx_sem)
        # Columnas a mostrar en el ranking
        cols_ranking = [col_esp, col_mun, 'Dirección', tx_sem, 'Ene 2026 TX', 'Estado']
        cols_show = [c for c in cols_ranking if c in top_50.columns]
        
        st.dataframe(top_50[cols_show], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📋 Base de Datos Completa")
        txt_busqueda = st.text_input("Buscar por dirección o nombre específico:")
        
        df_view = df_f.copy()
        if txt_busqueda:
            df_view = df_f[df_f.astype(str).apply(lambda x: x.str.contains(txt_busqueda, case=False)).any(axis=1)]
        
        st.write(f"Mostrando {len(df_view)} registros")
        st.dataframe(df_view, use_container_width=True, hide_index=True)

else:
    st.info("📢 Instrucciones: Sube el archivo 'datos_corresponsales.csv' a la raíz de tu repositorio en GitHub para activar el Panel.")
