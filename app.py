import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Visualizador Orinoquia Water Futures (OWF)",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS Personalizados ---
st.markdown("""
<style>
    /* Estilos generales */
    .stApp {
        background-color: #f0f4f8;
    }
    /* Estilos para la barra lateral */
    .css-1d391kg {
        background-color: #ffffff;
        border-right: 1px solid #e6e6e6;
    }
    /* Estilos para los títulos */
    h1, h2, h3 {
        color: #003366; /* Azul oscuro */
    }
    /* Estilos para los botones */
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)


# --- Funciones de Lógica y Datos ---

@st.cache_data
def load_manifest(path="soporte/manifest.json"):
    """Carga el manifiesto de datos desde un archivo JSON."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        return manifest
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo '{path}'. Asegúrate de que el archivo existe en la ubicación correcta dentro de tu repositorio de GitHub.")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: El archivo '{path}' no es un JSON válido. Revisa su formato.")
        return None

@st.cache_data
def load_data_from_cloud(scenario_params, data_manifest):
    """
    Construye la URL del archivo en la nube basado en los parámetros del escenario,
    y carga los datos en un DataFrame de pandas.
    """
    # 1. Traducir selecciones de la UI a los códigos de los nombres de archivo
    policy_code = "FCFS" if scenario_params['policy'] == "First Come First Served (FCFS)" else "PE"
    run_code = scenario_params['run']
    temp_code = f"DT{scenario_params['tempChange']}"
    
    precip_val = 100 + scenario_params['precipChange']
    precip_code = f"DP{precip_val}"

    pop_code = f"FW{scenario_params['popYear']}"
    crop_code = f"Irr{scenario_params['cropYear']}"
    livestock_code = f"Liv{scenario_params['livestockYear']}"

    # 2. Construir el nombre del archivo EXACTAMENTE como en manifest.json
    file_name = f"OWF_{policy_code}_{run_code}_{temp_code}_{precip_code}_{pop_code}_{crop_code}_{livestock_code}.csv"
    st.write(f"Buscando archivo en manifiesto: `{file_name}`")

    if data_manifest is None: return pd.DataFrame()
    file_id = data_manifest.get(file_name)
    
    if not file_id:
        st.warning(f"No se encontró un ID de archivo en 'manifest.json' para el escenario: `{file_name}`. Se usarán datos vacíos.")
        return pd.DataFrame()

    base_url = 'https://docs.google.com/uc?export=download&id='
    final_url = base_url + file_id

    # 3. Cargar los datos desde la URL
    try:
        with st.spinner(f"Descargando datos desde la nube para {file_name}..."):
            df = pd.read_csv(final_url)
            df = df.rename(columns={df.columns[0]: 'Date'})
            df['Date'] = pd.to_datetime(df['Date'])
            return df
    except Exception as e:
        st.error(f"Error al descargar o procesar el archivo desde la nube: {file_name}. Verifique el ID y los permisos del archivo. Error: {e}")
        return pd.DataFrame()

# --- Componentes de la Interfaz de Usuario (UI) ---

def sidebar_ui():
    """Crea la barra lateral con los controles de los escenarios."""
    st.sidebar.image("https://www.thegef.org/sites/default/files/styles/gef_landscape_image/public/2022-04/colombia-orinoquia-river-basin.jpg", use_column_width=True)
    st.sidebar.title("Configuración de Escenarios")
    
    with st.sidebar.expander("**Escenario 1**", expanded=True):
        s1_params = scenario_controls("s1")
    
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("**Escenario 2**", expanded=True):
        s2_params = scenario_controls("s2")
        
    st.sidebar.markdown("---")
    
    generate_button = st.sidebar.button("Generar Comparación y Gráficos", use_container_width=True)
    
    return s1_params, s2_params, generate_button

def scenario_controls(key_prefix):
    """Crea un conjunto de controles para un escenario."""
    params = {}
    params['policy'] = st.selectbox("Política de Asignación:", ["First Come First Served (FCFS)", "Policy Enforced (PE)"], key=f"policy_{key_prefix}")
    params['run'] = st.selectbox("Réplica:", ["R1", "R2", "R3", "R4", "R5"], key=f"run_{key_prefix}")
    params['tempChange'] = st.slider("Cambio de Temperatura (°C):", 0, 5, 2, key=f"temp_{key_prefix}")
    params['precipChange'] = st.slider("Cambio de Precipitación (%):", -30, 30, 0, 10, key=f"precip_{key_prefix}")
    params['popYear'] = st.selectbox("Año Proy. Población:", [2022, 2030, 2040, 2050], index=1, key=f"pop_{key_prefix}")
    params['cropYear'] = st.selectbox("Año Proy. Cultivos:", [2022, 2030, 2040, 2050], index=0, key=f"crop_{key_prefix}")
    params['livestockYear'] = st.selectbox("Año Proy. Pecuario:", [2022, 2030, 2040, 2050], index=1, key=f"livestock_{key_prefix}")
    return params

# --- Funciones de Gráficos ---

def plot_demand_composition(df, title):
    """Dibuja un gráfico de pie con la composición de la demanda."""
    if df is None or df.empty:
        st.warning(f"No hay datos para generar el gráfico de demanda para: {title}")
        return
        
    demand_cols = [col for col in df.columns if col.startswith(('Denv_', 'Dfwr_', 'Dfwu_', 'Dirr_', 'Dliv_'))]
    demand_totals = df[demand_cols].sum()
    
    composition = {
        "Ambiental": demand_totals[[c for c in demand_cols if 'Denv_' in c]].sum(),
        "Rural": demand_totals[[c for c in demand_cols if 'Dfwr_' in c]].sum(),
        "Urbano": demand_totals[[c for c in demand_cols if 'Dfwu_' in c]].sum(),
        "Irrigación": demand_totals[[c for c in demand_cols if 'Dirr_' in c]].sum(),
        "Pecuario": demand_totals[[c for c in demand_cols if 'Dliv_' in c]].sum(),
    }
    
    df_comp = pd.DataFrame(list(composition.items()), columns=['Componente', 'Valor'])
    
    fig = px.pie(df_comp, values='Valor', names='Componente', title=title, hole=0.3)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

# --- Aplicación Principal ---

def main():
    """Función principal que ejecuta la aplicación Streamlit."""
    
    st.title("💧 Visualizador de Escenarios Hídricos - Orinoquia Water Futures")
    st.markdown("Esta herramienta permite comparar dinámicamente dos escenarios de recursos hídricos para la cuenca del río Meta.")
    st.info("**Instrucción:** Asegúrate de que tu archivo `manifest.json` esté en la carpeta `soporte/` de tu repositorio de GitHub.")

    data_manifest = load_manifest()
    s1_params, s2_params, generate_button = sidebar_ui()
    
    if generate_button:
        if data_manifest:
            df_s1 = load_data_from_cloud(s1_params, data_manifest)
            df_s2 = load_data_from_cloud(s2_params, data_manifest)
            
            if df_s1.empty or df_s2.empty:
                st.error("No se pudieron cargar los datos para uno o ambos escenarios. Por favor, verifique la configuración y el contenido de 'manifest.json'.")
            else:
                st.header("Composición de la Demanda de Agua Anual")
                col1, col2 = st.columns(2)
                with col1:
                    plot_demand_composition(df_s1, "Escenario 1")
                with col2:
                    plot_demand_composition(df_s2, "Escenario 2")
        else:
            st.error("No se puede continuar. Revisa que 'manifest.json' esté cargado correctamente.")
    else:
        st.info("Configure los escenarios en la barra lateral y presione 'Generar Comparación' para ver los resultados.")

if __name__ == "__main__":
    main()
