import streamlit as st
import matplotlib.pyplot as plt

from core.storage import load_results
from core.metrics import compute_stats

##
# @file dashboard.py
# @brief Dashboard interactivo para visualizar métricas de benchmarking de modelos LLM.
#
# Esta aplicación utiliza Streamlit para mostrar estadísticas como latencia,
# throughput (tokens por segundo) y número de peticiones realizadas por modelo.
#

##
# @brief Configuración inicial de la página de Streamlit.
#
# Define el título de la pestaña y el layout del dashboard.
#
st.set_page_config(page_title="LLM Benchmark Dashboard", layout="wide")

##
# @brief Título principal del dashboard.
#
st.title("LLM Benchmark Control Center")


# --- cargar datos ---

##
# @brief Carga los resultados almacenados de benchmarking.
#
# @return dict Datos crudos de resultados.
#
results = load_results()

##
# @brief Calcula estadísticas agregadas a partir de los resultados.
#
# @param results Resultados crudos cargados.
# @return dict Diccionario con métricas por modelo.
#
stats = compute_stats(results)

##
# @brief Lista de modelos disponibles en los resultados.
#
models = list(stats.keys())

##
# @brief Controla el caso en que no haya datos disponibles.
#
if not models:
    st.warning("No hay datos disponibles todavía.")
    st.stop()


# --- selector interactivo ---

##
# @brief Selector de modelos para filtrar los datos mostrados.
#
# Permite al usuario elegir qué modelos visualizar en el dashboard.
#
# @return list Lista de modelos seleccionados.
#
selected_models = st.multiselect(
    "Selecciona modelos",
    models,
    default=models
)

##
# @brief Filtra las estadísticas según los modelos seleccionados.
#
# @return dict Estadísticas filtradas.
#
filtered = {m: stats[m] for m in selected_models}


# --- métricas base ---

##
# @brief Extrae la latencia media de cada modelo seleccionado.
#
avg_latency = [filtered[m]["avg_latency"] for m in selected_models]

##
# @brief Extrae los tokens por segundo (si existen).
#
tokens_per_sec = [filtered[m].get("tokens_per_sec", 0) for m in selected_models]

##
# @brief Extrae el número de peticiones realizadas por modelo.
#
num_requests = [filtered[m]["num_requests"] for m in selected_models]


# --- layout tipo dashboard ---

##
# @brief Divide la interfaz en dos columnas para visualización.
#
col1, col2 = st.columns(2)


with col1:
    ##
    # @brief Gráfico de latencia media por modelo.
    #
    st.subheader("⚡ Latencia media")
    fig1, ax1 = plt.subplots()
    ax1.bar(selected_models, avg_latency)
    ax1.set_ylabel("segundos")
    plt.xticks(rotation=45)
    st.pyplot(fig1)

    ##
    # @brief Gráfico del número de requests por modelo.
    #
    st.subheader("Requests")
    fig3, ax3 = plt.subplots()
    ax3.bar(selected_models, num_requests)
    st.pyplot(fig3)


with col2:
    ##
    # @brief Gráfico de tokens generados por segundo.
    #
    st.subheader("Tokens por segundo")
    fig2, ax2 = plt.subplots()
    ax2.bar(selected_models, tokens_per_sec)
    st.pyplot(fig2)


# --- tabla resumen ---

##
# @brief Tabla resumen con métricas principales por modelo.
#
st.subheader("Resumen numérico")

##
# @brief Muestra los datos en formato tabular interactivo.
#
# Incluye latencia media, throughput y número de requests.
#
st.dataframe(
    {
        "modelo": selected_models,
        "latencia_media": avg_latency,
        "tokens_por_seg": tokens_per_sec,
        "requests": num_requests,
    }
)