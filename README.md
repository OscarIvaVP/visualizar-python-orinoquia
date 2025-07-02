# visualizar-python-orinoquia
# Visualizador de Escenarios Hídricos - Orinoquia Water Futures (OWF)

Este proyecto es una aplicación web interactiva construida con Streamlit y Python para visualizar y comparar escenarios de recursos hídricos en la cuenca del río Meta, Colombia. La aplicación es una reimplementación dinámica del visualizador original basado en HTML/JavaScript del proyecto OWF.

## Características

- **Interfaz Dinámica:** Permite a los usuarios configurar y comparar dos escenarios hídricos simultáneamente.
- **Controles Interactivos:** Widgets para ajustar parámetros clave como políticas de asignación, réplicas de modelo, cambios climáticos (temperatura y precipitación) y proyecciones de demanda.
- **Visualizaciones Detalladas:**
  - Mapas coropléticos que muestran el estrés hídrico por subcuenca.
  - Gráficos de pie que desglosan la composición de la demanda de agua.
- **Modular y Extensible:** La estructura del código está diseñada para ser fácilmente mantenible y extensible.

## Cómo Ejecutar la Aplicación

### 1. Prepara tu Repositorio en GitHub

Asegúrate de que tu repositorio tenga la siguiente estructura de archivos. Es fundamental para que Streamlit pueda encontrar los archivos de soporte.

tu-repositorio/├── app.py                  # El código principal de la aplicación Streamlit├── requirements.txt        # Lista de dependencias de Python└── soporte/├── manifest.json       # Tu archivo con los IDs de los datos└── cuencas/└── cuencas.geojson # Tu archivo de mapa con los polígonos
### 2. Despliega en Streamlit Community Cloud

1.  Ve a [share.streamlit.io](https://share.streamlit.io/).
2.  Haz clic en **"New app"**.
3.  Conecta tu repositorio de GitHub.
4.  Asegúrate de que la ruta del archivo principal sea `app.py`.
5.  ¡Haz clic en **"Deploy!"**.

La aplicación leerá tu `manifest.json`, descargará los datos correspondientes desde Google Drive según las selecciones del usuario y mostrará los gráficos.
