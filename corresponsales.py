import streamlit as st
import pandas as pd

# 1. CONEXIÓN (Asegúrate de que sea la base con todas las columnas)
SHEET_ID = "1i998RGnLv8npxSLB5OyBvzNr36dQJD8RFdsKZj4UOfw"
URL_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data
def cargar_todo():
    df = pd.read_csv(URL_SHEET)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = cargar_todo()

# 2. VERIFICACIÓN DE COLUMNAS
# Si esto falla, es porque la hoja de Google NO TIENE esos datos.
st.write("Columnas disponibles para consultar:", list(df.columns))

# 3. FILTROS (Solo funcionan si las columnas existen)
if 'Ciudad' in df.columns:
    ciudad = st.selectbox("Consultar Ciudad", df['Ciudad'].unique())
    # Aquí mostrarías la dirección
    detalle = df[df['Ciudad'] == ciudad][['Dirección', 'ESPECIALISTA', 'Tipo de CBs']]
    st.table(detalle)
