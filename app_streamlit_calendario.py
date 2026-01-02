import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.figure_factory as ff
import matplotlib.pyplot as plt
from streamlit_calendar import calendar

# ========= VISUAL CONFIG =========
BG_COLOR = "#21222c"
FG_COLOR = "#FFFFFF"
ACCENT_COLOR = "#FFC107"
PALETTE_POOL = [
    "#3F51B5", "#FFC107", "#00BCD4", "#8BC34A", "#FF5722", "#E91E63",
    "#607D8B", "#C2185B", "#FFEB3B", "#9C27B0", "#03A9F4", "#CDDC39",
    "#F44336", "#00BCD4", "#009688", "#8BC34A", "#795548", "#FF9800",
    "#607D8B", "#673AB7"
]

# ========= LOAD DATA =========
sheet_url = "https://docs.google.com/spreadsheets/d/1D2izOqMKEgSphr7HkdJ34L3Ps3X3R2JIGlHpWX2qqyo/export?format=csv&gid=1348048761"
df = pd.read_csv(sheet_url)
df.columns = df.columns.str.strip()

df["Data Início"] = pd.to_datetime(df["Data Início"], dayfirst=True, errors="coerce")
df["Data Fim"] = pd.to_datetime(df["Data Fim"], dayfirst=True, errors="coerce")
df = df.dropna(subset=["Data Início", "Data Fim"])

responsaveis_unicos = df["Nome"].unique().tolist()
paleta_dinamica = {nome: PALETTE_POOL[i % len(PALETTE_POOL)] for i, nome in enumerate(responsaveis_unicos)}

# ========= FUNÇÕES AUXILIARES =========
def eventos_from_df(df):
    eventos = []
    for _, row in df.iterrows():
        if pd.isna(row["Data Início"]) or pd.isna(row["Data Fim"]):
            continue
        eventos.append({
            "title": f"{row['Nome']} – {row['Motivo']} ({row['Destino']})",
            "start": row["Data Início"].strftime("%Y-%m-%d"),
            "end": (row["Data Fim"] + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "color": paleta_dinamica.get(row["Nome"], ACCENT_COLOR)
        })
    return eventos

def kpi_card(label, value, color):
    st.markdown(
        f"""
        <div style='background:{color};padding:18px 14px 10px 14px;
                 border-radius:14px;display:inline-block;
                 min-width:160px;text-align:center;margin-right:16px;'>
            <span style='color:#222;font-size:16px;font-weight:bold'>{label}</span><br>
            <span style='font-size:2.2em;font-weight:bold;color:#222'>{value}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# ========= APP =========
st.set_page_config("Calendário Executivo", layout="wide")
st.title("📅 Calendário Executivo – Viagens e Atividades do Time")


# === FILTROS (SELECIONAR TODOS) ===
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    nomes = df["Nome"].unique().tolist()
    all_nomes = st.checkbox("Selecionar todos (Responsável)", True)
    nomes_sel = st.multiselect(
        "Responsável", nomes, default=nomes if all_nomes else []
    )

with c2:
    tipos = df["Tipo Roteiro"].unique().tolist()
    all_tipos = st.checkbox("Selecionar todos (Tipo)", True)
    tipos_sel = st.multiselect(
        "Tipo de Roteiro", tipos, default=tipos if all_tipos else []
    )

with c3:
    status = df["Status Viagem"].unique().tolist()
    all_status = st.checkbox("Selecionar todos (Status Viagem)", True)
    status_sel = st.multiselect(
        "Status Viagem", status, default=status if all_status else []
    )

with c4:
    classes = df["Classe"].unique().tolist()
    all_classes = st.checkbox("Selecionar todos (Classe)", True)
    classes_sel = st.multiselect(
        "Classe", classes, default=classes if all_classes else []
    )

with c5:
    meses = sorted(df["Data Início"].dt.month.unique())
    all_meses = st.checkbox("Selecionar todos (Mês)", True)
    meses_sel = st.multiselect(
        "Mês", meses, default=meses if all_meses else [],
        format_func=lambda m: pd.to_datetime(str(m), format="%m").strftime("%B")
    )

# === DATAFRAME FILTRADO ===
df_f = df[
    df["Nome"].isin(nomes_sel) &
    df["Tipo Roteiro"].isin(tipos_sel) &
    df["Status Viagem"].isin(status_sel) &
    df["Classe"].isin(classes_sel) &
    df["Data Início"].dt.month.isin(meses_sel)
].copy()

eventos_f = [e for e in eventos_from_df(df_f) if any(n in e["title"] for n in nomes_sel)]


# ========= KPI CARDS (NO TOPO) =========
colk1, colk2, colk3, colk4 = st.columns(4)
with colk1:
    kpi_card("Total Compromissos", len(df_f), "#FFC107")

with colk2:
    dias = (df_f["Data Fim"] - df_f["Data Início"]).dt.days.add(1)
    media = dias.mean() if not dias.empty else 0
    kpi_card("Duração Média da Viagem (dias)", f"{media:.1f}", "#8BC34A")

with colk3:
    pessoas = df_f["Nome"].nunique()
    kpi_card("Pessoas em viagem", pessoas, "#00BCD4")

with colk4:
    ufs = df_f["Destino UF"].nunique() if "Destino UF" in df_f.columns else 0
    kpi_card("UFs Visitadas", ufs, "#FF5722")

    

# ========= TABELA =========
st.subheader("📋 Tabela detalhada")
gb = GridOptionsBuilder.from_dataframe(df_f)
gb.configure_default_column(filterable=True, sortable=True)
AgGrid(df_f, gridOptions=gb.build(), height=320)

# ========= VISUALIZAÇÃO CALENDÁRIO =========
st.subheader("📆 Visualização do Calendário")
modo = st.radio("Escolha o modo:", ["Modelo Google Agenda", "Gantt Plotly"], horizontal=True)
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

# ========= DASHBOARDS EXECUTIVOS =========
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

# Gráfico Viagens por Responsável
with d1:
    st.subheader("Viagens por Responsável")
    nomes_grafico = df_f["Nome"].value_counts().sort_values(ascending=False)
    cores = [paleta_dinamica.get(n, ACCENT_COLOR) for n in nomes_grafico.index]
    fig1, ax1 = plt.subplots(figsize=(5, 3))
    nomes_grafico.plot(kind="bar", color=cores, ax=ax1)
    ax1.set_ylabel("Qtd")
    ax1.set_xlabel("Responsável")
    ax1.bar_label(ax1.containers[0], label_type='edge')  # Adiciona os labels nas barras
    plt.xticks(rotation=20)
    st.pyplot(fig1)
    plt.close(fig1)

# Gráfico Principais Tipos de Viagem (Classe)
with d2:
    st.subheader("Principais tipos de viagem")
    classe_grafico = df_f["Classe"].value_counts().head(8).sort_values(ascending=True)
    fig2, ax2 = plt.subplots(figsize=(5, 3))
    bars = classe_grafico.plot(kind="barh", color=ACCENT_COLOR, ax=ax2)
    ax2.set_xlabel("Qtd")
    ax2.set_ylabel("Classe")
    for bar in bars.containers[0]:
        width = bar.get_width()
        ax2.annotate(f'{int(width)}', xy=(width, bar.get_y() + bar.get_height() / 2),
                     va='center', ha='left', fontsize=10, color=FG_COLOR)
    st.pyplot(fig2)
    plt.close(fig2)

# Adicione novas colunas para os gráficos extras
d3, d4 = st.columns(2)

# Gráfico Ranking de UFs Visitadas
with d3:
    if "Destino UF" in df_f.columns:
        st.subheader("🌎 Ranking de UFs Visitadas")
        top_ufs = df_f["Destino UF"].value_counts().sort_values(ascending=False).head(8)
        fig_uf, ax_uf = plt.subplots(figsize=(5, 3))  # Mantém tamanho igual
        bars = top_ufs.plot(
            kind="barh",
            color="#00BCD4",
            ax=ax_uf
        )
        ax_uf.set_xlabel("Qtd", fontsize=10)
        ax_uf.set_ylabel("Destino UF", fontsize=10)
        ax_uf.tick_params(axis='x', labelsize=10)
        ax_uf.tick_params(axis='y', labelsize=12)
        ax_uf.invert_yaxis()
        for i, v in enumerate(top_ufs.values):
            ax_uf.text(
                v + 0.1, i, str(v),
                va='center',
                color=FG_COLOR,
                fontsize=12,
                fontweight='bold'
            )
        fig_uf.tight_layout()
        st.pyplot(fig_uf)
        plt.close(fig_uf)

# Gráfico Ranking de Destinos
with d4:
    if "Destino" in df_f.columns:
        st.subheader("🏙️ Ranking de Destinos Visitados")
        top_destinos = df_f["Destino"].value_counts().sort_values(ascending=False).head(8)
        destinos = top_destinos.index.tolist()
        PALETTE_DEST = [
            "#009688", "#FF9800", "#03A9F4", "#E91E63", "#8BC34A", "#FF5722", "#3F51B5", "#CDDC39",
            "#FFC107", "#00BCD4", "#C2185B", "#607D8B", "#9C27B0", "#795548"
        ]
        cores_dest = [PALETTE_DEST[i % len(PALETTE_DEST)] for i in range(len(destinos))]
        fig_dest, ax_dest = plt.subplots(figsize=(5, 3))
        bars = top_destinos.plot(
            kind="barh",
            color=cores_dest,
            ax=ax_dest
        )
        ax_dest.set_xlabel("Qtd", fontsize=10)
        ax_dest.set_ylabel("Destino", fontsize=10)
        ax_dest.tick_params(axis='x', labelsize=10)
        ax_dest.tick_params(axis='y', labelsize=12)
        ax_dest.invert_yaxis()
        for i, (v, c) in enumerate(zip(top_destinos.values, cores_dest)):
            ax_dest.text(
                v + 0.1, i, str(v),
                va='center',
                color=c,
                fontsize=12,
                fontweight='bold'
            )
        fig_dest.tight_layout()
        st.pyplot(fig_dest)
        plt.close(fig_dest)
