import streamlit as st
import pandas as pd
import numpy as np
import random
from faker import Faker
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.figure_factory as ff 
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from streamlit_calendar import calendar

# =========================================================
# CONFIGURAÇÃO VISUAL (PADRÃO MATERIAL / INDIGO / AMBER)
# =========================================================
PALETA = {
    "Fernando Lixa": "#3F51B5",   # indigo
    "Meleu": "#FFC107",           # amber
    "Carla Torres": "#00BCD4",    # cyan
    "Lucas Braga": "#8BC34A",     # light green
    "Joana Souza": "#FF5722",     # deep orange
}

BG_COLOR = "#21222c"
FG_COLOR = "#FFFFFF"
ACCENT_COLOR = "#FFC107"

# =========================================================
# MOCK DATA – DENSO E REALISTA
# =========================================================
def gerar_viagens_mock(qtd=1000, ano=2025, seed=42):
    Faker.seed(seed)
    random.seed(seed)
    fake = Faker("pt_BR")

    responsaveis = list(PALETA.keys())
    tipos = ["Externo", "Interno"]
    motivos = [
        "Visita Cliente", "Reunião Equipe", "Negociação",
        "Planejamento", "Auditoria Cliente", "Execução PDV",
        "Parceria", "Pós-venda", "Inovação"
    ]
    destinos = [
        "Cliente ABC", "Cliente BCA", "Cliente XPTO",
        "Distribuidor Sul", "Distribuidor Norte",
        "Baly", "Matriz", "Online"
    ]

    registros = []
    eventos = []
    por_mes = qtd // 12

    for mes in range(1, 13):
        dias = pd.date_range(
            start=f"{ano}-{mes:02d}-01",
            end=pd.Timestamp(f"{ano}-{mes:02d}-01") + pd.offsets.MonthEnd(0),
            freq="D"
        )

        for _ in range(por_mes):
            nome = random.choice(responsaveis)
            inicio = random.choice(dias)
            duracao = random.choice([1, 1, 2, 3])
            fim = inicio + pd.Timedelta(days=duracao - 1)
            motivo = random.choice(motivos)
            destino = random.choice(destinos)

            registros.append([
                nome, inicio, fim,
                random.choice(tipos),
                motivo, destino,
                fake.sentence(5) if random.random() < 0.15 else ""
            ])

            eventos.append({
                "title": f"{nome} – {motivo} ({destino})",
                "start": inicio.strftime("%Y-%m-%d"),
                "end": (fim + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                "color": PALETA[nome]
            })

    df = pd.DataFrame(registros, columns=[
        "Nome", "Data Início", "Data Fim",
        "Tipo Roteiro", "Motivo", "Destino", "Observação"
    ])

    df["Data Início"] = pd.to_datetime(df["Data Início"])
    df["Data Fim"] = pd.to_datetime(df["Data Fim"])

    return df.sort_values("Data Início").reset_index(drop=True), eventos


# =========================================================
# APP
# =========================================================
st.set_page_config("Calendário Executivo", layout="wide")
st.title("📅 Calendário Executivo – Viagens e Atividades do Time")

df, eventos = gerar_viagens_mock()

# =========================================================
# FILTROS (COM SELECT ALL CORRETO)
# =========================================================
c1, c2, c3 = st.columns(3)

with c1:
    nomes = df["Nome"].unique().tolist()
    all_nomes = st.checkbox("Selecionar todos (Responsável)", True)
    nomes_sel = st.multiselect(
        "Responsável",
        nomes,
        default=nomes if all_nomes else []
    )

with c2:
    tipos = df["Tipo Roteiro"].unique().tolist()
    all_tipos = st.checkbox("Selecionar todos (Tipo)", True)
    tipos_sel = st.multiselect(
        "Tipo de Roteiro",
        tipos,
        default=tipos if all_tipos else []
    )

with c3:
    meses = sorted(df["Data Início"].dt.month.unique())
    all_meses = st.checkbox("Selecionar todos (Mês)", True)
    meses_sel = st.multiselect(
        "Mês",
        meses,
        default=meses if all_meses else [],
        format_func=lambda m: pd.to_datetime(str(m), format="%m").strftime("%B")
    )

# =========================================================
# DATAFRAME FILTRADO
# =========================================================
df_f = df[
    df["Nome"].isin(nomes_sel) &
    df["Tipo Roteiro"].isin(tipos_sel) &
    df["Data Início"].dt.month.isin(meses_sel)
].copy()

eventos_f = [
    e for e in eventos
    if any(n in e["title"] for n in nomes_sel)
]

# =========================================================
# TABELA
# =========================================================
st.subheader("📋 Tabela detalhada")
gb = GridOptionsBuilder.from_dataframe(df_f)
gb.configure_default_column(filterable=True, sortable=True)
AgGrid(df_f, gridOptions=gb.build(), height=320)

# =========================================================
# VISUALIZAÇÃO CALENDÁRIO
# =========================================================
st.subheader("📆 Visualização do Calendário")
modo = st.radio(
    "Escolha o modo:",
    ["Modelo Google Agenda", "Gantt Plotly"],
    horizontal=True
)

# -------- GOOGLE AGENDA --------
if modo == "Modelo Google Agenda":
    calendar(
        events=eventos_f,
        options={
            "initialView": "dayGridMonth",
            "locale": "pt-br",
            "height": 850,
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,dayGridWeek,listWeek"
            }
        },
        key="calendar"
    )

# -------- GANTT PLOTLY (figure_factory, igual ao seu modelo original) --------
else:
    st.caption("Gantt agrupado por Motivo, colorido por Responsável (hover para detalhes)")
    if not df_f.empty:
        gantt_df = df_f.rename(
            columns={"Motivo": "Task", "Data Início": "Start", "Data Fim": "Finish", "Nome": "Resource"}
        )
        gantt_df = gantt_df[gantt_df["Start"].notnull() & gantt_df["Finish"].notnull()]
        fig = ff.create_gantt(
            gantt_df[["Task", "Start", "Finish", "Resource"]],
            index_col="Resource",
            show_colorbar=True,
            group_tasks=True,
            showgrid_x=True,
            showgrid_y=True,
            title="Visão Executiva – Agenda do Time",
            height=800,
            bar_width=0.2,
            show_hover_fill=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum evento encontrado para os filtros selecionados.")

# =========================================================
# DASHBOARDS EXECUTIVOS
# =========================================================
st.markdown("---")
st.header("📊 Dashboards Executivos")

plt.style.use("seaborn-v0_8-dark-palette")
plt.rcParams.update({
    "axes.facecolor": BG_COLOR,
    "figure.facecolor": BG_COLOR,
    "axes.labelcolor": FG_COLOR,
    "xtick.color": FG_COLOR,
    "ytick.color": FG_COLOR,
    "text.color": FG_COLOR
})

d1, d2 = st.columns(2)

with d1:
    st.subheader("Viagens por Responsável")
    fig1, ax1 = plt.subplots(figsize=(5,3))
    df_f["Nome"].value_counts().plot(
        kind="bar",
        color=[PALETA[n] for n in df_f["Nome"].value_counts().index],
        ax=ax1
    )
    ax1.set_ylabel("Qtd")
    plt.xticks(rotation=20)
    st.pyplot(fig1)
    plt.close(fig1)

with d2:
    st.subheader("Top Motivos")
    fig2, ax2 = plt.subplots(figsize=(5,3))
    df_f["Motivo"].value_counts().head(8).plot(
        kind="barh",
        color=ACCENT_COLOR,
        ax=ax2
    )
    ax2.set_xlabel("Qtd")
    st.pyplot(fig2)
    plt.close(fig2)

st.info("Os filtros no topo impactam tabela, calendário e dashboards em tempo real.")
