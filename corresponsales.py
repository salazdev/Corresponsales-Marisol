import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN E IDENTIDAD VISUAL
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

# =============================================================================
# LOGO CORPORATIVO E IDENTIDAD VISUAL - SALAZ ANALYTICS
# =============================================================================
# Intentamos cargar el logo directamente como imagen nativa
if os.path.exists("logo-salazanalytics.svg"):
    # Esto dibuja tu logo exacto en pantalla. Ajusta el 'width' si lo quieres más grande o pequeño.
    st.image("logo-salazanalytics.svg", width=280)
    st.markdown("""
        <div style="margin-top: -10px; margin-bottom: 15px; padding-left: 5px;">
            <p style="margin: 0; font-size: 12px; color: #EBB932; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px;">
                Plataforma Inteligente de Gestión
            </p>
            <a href="https://salazanalytics.com/" target="_blank" style="color: #0033a0; text-decoration: underline; font-size: 14px; font-weight: 600;">
                🌐 salazanalytics.com
            </a>
        </div>
    """, unsafe_allow_html=True)
else:
    # Respaldo en texto solo por seguridad si el archivo no está en GitHub
    st.markdown("""
        <div style="text-align: left; margin-bottom: 15px;">
            <h2 style="margin-bottom: 0px; color: #0033a0; letter-spacing: 1px; font-weight: bold; font-size: 28px;">SALAZ ANALYTICS</h2>
            <p style="font-size: 13px; color: #EBB932; margin-top: 0px; margin-bottom: 5px; text-transform: uppercase; font-weight: bold;">Plataforma Inteligente de Gestión</p>
            <a href="https://salazanalytics.com/" target="_blank" style="color: #0033a0; text-decoration: underline; font-size: 14px; font-weight: 600;">🌐 salazanalytics.com</a>
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


# 3. CARGA ULTRA-RÁPIDA DE CONVENIOS MEDIANTE CSV
# 3. CARGA ULTRA-RÁPIDA DE CONVENIOS MEDIANTE CSV (CON DETECCIÓN INTELIGENTE)
# 3. CARGA ULTRA-RÁPIDA DE CONVENIOS MEDIANTE CSV (CON DETECCIÓN INTELIGENTE)
# 3. CARGA DE CONVENIOS HÍBRIDA (MÁXIMA VELOCIDAD + RESPALDO SEGURO)
@st.cache_data(ttl=3600)
def cargar_datos_convenios():
    archivo_csv = "convenios_activos.csv"
    archivo_excel = "listado-de-convenios-activos-corresponsales mayo 2.xlsx"
    
    # Intenta primero con el CSV optimizado para máxima velocidad (0.2 segundos)
    if os.path.exists(archivo_csv):
        try:
            df_conv = pd.read_csv(archivo_csv, sep=',', encoding='utf-8', on_bad_lines='skip', low_memory=False)
            if len(df_conv.columns) <= 1:
                df_conv = pd.read_csv(archivo_csv, sep=';', encoding='latin-1', on_bad_lines='skip', low_memory=False)
            
            df_conv.columns = [str(c).strip().upper() for c in df_conv.columns]
            return df_conv
        except:
            pass

    # SI EL CSV FALLA O NO EXISTE: Abre el Excel original para que la app no se detenga
    if os.path.exists(archivo_excel):
        try:
            df_conv = pd.read_excel(archivo_excel, sheet_name="Convenios", header=1)
            df_conv.columns = [str(c).strip().upper() for c in df_conv.columns]
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

# Carga global de datos con caché optimizado
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

        st.subheader("Top 50 Corresponsales con Mejor Desempeño")
        top_50 = df.nlargest(50, tx_sem)
        cols_ranking = [col_esp, col_mun, 'Dirección', tx_sem, 'Ene 2026 TX', 'Estado']
        cols_show = [c for c in cols_ranking if c in top_50.columns]
        st.dataframe(top_50[cols_show], use_container_width=True, hide_index=True)

        # --- BASE DE DATOS INFERIOR ---
        st.subheader("📋 Base de Datos Completa")
        txt_busqueda = st.text_input("Buscar por dirección o nombre específico:")
        
        df_view = df_f.copy()
        if txt_busqueda:
            busqueda_str = str(txt_busqueda).lower()
            col_dir = 'Dirección' if 'Dirección' in df_view.columns else df_view.columns[2]
            col_nom = 'Nombre' if 'Nombre' in df_view.columns else df_view.columns[0]
            
            df_view = df_view[
                df_view[col_dir].astype(str).str.lower().str.contains(busqueda_str) |
                df_view[col_nom].astype(str).str.lower().str.contains(busqueda_str)
            ]
        
        st.write(f"Mostrando {len(df_view)} registros")
        if not df_view.empty:
            st.dataframe(df_view, use_container_width=True, hide_index=True)
        else:
            st.info("🔍 No se encontraron registros que coincidan con la búsqueda.")
            
    else:
        st.info("📢 Instrucciones: Sube el archivo 'datos_corresponsales.csv' a la raíz de tu repositorio en GitHub para activar el Panel.")


# ==========================================
# MÓDULO 2: BUSCADOR DE CONVENIOS (CON FILTRO POR DEPARTAMENTO)
# ==========================================
elif modulo_seleccionado == "📄 Buscador de Convenios":
    st.header("📄 Consulta de Convenios Activos para Recaudo")
    
    if df_convenios is not None:
        # --- NUEVA INTERVENCIÓN: FILTRO POR DEPARTAMENTO EN LA BARRA LATERAL ---
        st.sidebar.header("🔍 Filtros de Convenios")
        
        # Identificamos si la columna se llama 'DEPARTAMENTO' o similar
        col_dep_lista = [c for c in df_convenios.columns if 'DEP' in c]
        c_dep = col_dep_lista[0] if col_dep_lista else None
        
        if c_dep:
            # Extraemos los departamentos únicos, los ordenamos y armamos la lista
            lista_deps = ["Todos"] + sorted(df_convenios[c_dep].dropna().unique().tolist())
            dep_sel = st.sidebar.selectbox("Seleccione Departamento / Región:", lista_deps)
        else:
            dep_sel = "Todos"
            st.sidebar.warning("⚠️ No se detectó la columna 'DEPARTAMENTO' en el CSV.")
            
        # --- BUSCADOR EN TIEMPO REAL ---
        busqueda = st.text_input("🔍 Buscar convenio en tiempo real (por Empresa, Convenio o Categoría):")
        
        # Aplicamos los filtros en cascada sobre la base de datos
        df_filtrado = df_convenios.copy()
        
        # 1. Filtro por el Departamento seleccionado
        if dep_sel != "Todos" and c_dep:
            df_filtrado = df_filtrado[df_filtrado[c_dep] == dep_sel]
            
        # 2. Filtro por el texto de búsqueda
        if busqueda:
            busqueda_str = str(busqueda).lower()
            col_emp = [c for c in df_filtrado.columns if 'EMP' in c]
            col_conv = [c for c in df_filtrado.columns if 'CONV' in c]
            col_cat = [c for c in df_filtrado.columns if 'CAT' in c]
            
            c_emp = col_emp[0] if col_emp else df_filtrado.columns[0]
            c_conv = col_conv[0] if col_conv else df_filtrado.columns[1]
            c_cat = col_cat[0] if col_cat else df_filtrado.columns[2]
            
            df_filtrado = df_filtrado[
                df_filtrado[c_emp].astype(str).str.lower().str.contains(busqueda_str) |
                df_filtrado[c_conv].astype(str).str.lower().str.contains(busqueda_str) |
                df_filtrado[c_cat].astype(str).str.lower().str.contains(busqueda_str)
            ]
        
        # --- TARJETAS DE CONTEO RÁPIDO ---
        c1, c2 = st.columns(2)
        c1.metric(label="Total Convenios en este Segmento", value=f"{len(df_filtrado):,}")
        c2.metric(label="Resultados de Búsqueda", value=f"{len(df_filtrado) if busqueda else 0:,}")
        
        # --- TABLA DETALLADA ---
        st.subheader("📋 Detalle de Convenios")
        if not df_filtrado.empty:
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        else:
            st.info("🔍 No se encontraron convenios que coincidan con los filtros aplicados.")
            
    else:
        st.info("⏳ Esperando el archivo de convenios veloz. Recuerda subir 'convenios_activos.csv' a tu GitHub.")

# PIE DE PÁGINA CORPORATIVO
st.markdown("---")
st.caption("SALAZ ANALYTICS | Plataforma Inteligente de Gestión")
# PIE DE PÁGINA CORPORATIVO
st.markdown("---")
st.caption("SALAZ ANALYTICS | Plataforma Inteligente de Gestión")
