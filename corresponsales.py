@st.cache_data(ttl=3600)
def cargar_datos_convenios():
    # Intentamos con los dos nombres de archivo que hemos usado en el repositorio
    archivo_opcion1 = "convenios.csv"
    archivo_opcion2 = "convenios_activos.csv"
    
    archivo = archivo_opcion1 if os.path.exists(archivo_opcion1) else archivo_opcion2
    
    if not os.path.exists(archivo):
        return None
    try:
        try:
            df = pd.read_csv(archivo, sep=',', encoding='utf-8', on_bad_lines='skip', low_memory=False)
            if len(df.columns) <= 1: raise ValueError
        except:
            df = pd.read_csv(archivo, sep=';', encoding='latin-1', on_bad_lines='skip', low_memory=False)
            
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except:
        return None
