import streamlit as st
import matplotlib.pyplot as plt

from core.storage import load_results
from core.metrics import compute_stats


st.set_page_config(page_title="LLM Benchmark Dashboard", layout="wide")

st.title("LLM Benchmark Control Center")


# --- cargar datos ---
results = load_results()
stats = compute_stats(results)

models = list(stats.keys())

if not models:
    st.warning("No hay datos disponibles todavía.")
    st.stop()


# --- selector interactivo ---
selected_models = st.multiselect(
    "Selecciona modelos",
    models,
    default=models
)

filtered = {m: stats[m] for m in selected_models}


# --- métricas base ---
avg_latency = [filtered[m]["avg_latency"] for m in selected_models]
tokens_per_sec = [filtered[m].get("tokens_per_sec", 0) for m in selected_models]
num_requests = [filtered[m]["num_requests"] for m in selected_models]


# --- layout tipo dashboard ---
col1, col2 = st.columns(2)


with col1:
    st.subheader("⚡ Latencia media")
    fig1, ax1 = plt.subplots()
    ax1.bar(selected_models, avg_latency)
    ax1.set_ylabel("segundos")
    plt.xticks(rotation=45)
    st.pyplot(fig1)

    st.subheader("📦 Requests")
    fig3, ax3 = plt.subplots()
    ax3.bar(selected_models, num_requests)
    st.pyplot(fig3)


with col2:
    st.subheader("🚀 Tokens por segundo")
    fig2, ax2 = plt.subplots()
    ax2.bar(selected_models, tokens_per_sec)
    st.pyplot(fig2)


# --- tabla resumen ---
st.subheader("📋 Resumen numérico")

st.dataframe(
    {
        "modelo": selected_models,
        "latencia_media": avg_latency,
        "tokens_por_seg": tokens_per_sec,
        "requests": num_requests,
    }
)