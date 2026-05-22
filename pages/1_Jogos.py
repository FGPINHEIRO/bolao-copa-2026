# pages/1_Jogos.py - Tabela de Jogos
import streamlit as st
from utils import get_supabase, require_login, sidebar_autenticada
from datetime import datetime, timezone
import pytz

st.set_page_config(page_title="Jogos | Bolão Copa 2026", page_icon="📅", layout="wide")

supabase = get_supabase()
require_login()
sidebar_autenticada(supabase)

st.title("📅 Tabela de Jogos")

# Buscar todos os jogos
jogos = supabase.table("jogos").select("*").order("data_jogo").order("hora_utc").execute().data

if not jogos:
    st.info("Nenhum jogo cadastrado ainda.")
    st.stop()

# Agrupar por fase e grupo
fases = {}
for j in jogos:
    fase = j["fase"]
    grupo = j["grupo"]
    key = (fase, grupo)
    fases.setdefault(key, []).append(j)

# Mostrar filtro de fase
fase_opcoes = ["Todos", "Fase de Grupos", "Mata-Mata"]
fase_sel = st.radio("Filtrar por fase:", fase_opcoes, horizontal=True)

def formatar_hora_br(data_jogo, hora_utc):
    """Converte UTC para horário de Brasília."""
    dt_utc = datetime.fromisoformat(f"{data_jogo}T{hora_utc}").replace(tzinfo=timezone.utc)
    br_tz = pytz.timezone("America/Sao_Paulo")
    dt_br = dt_utc.astimezone(br_tz)
    return dt_br.strftime("%d/%m/%Y %H:%M")

def badge_resultado(j):
    if j["gols_a"] is not None and j["gols_b"] is not None:
        return f"**{j['gols_a']} x {j['gols_b']}**"
    return "—"

# Renderizar por grupo
grupos_exibidos = set()

for (fase, grupo), lista_jogos in sorted(fases.items()):
    if fase_sel == "Fase de Grupos" and fase != "grupos":
        continue
    if fase_sel == "Mata-Mata" and fase != "mata-mata":
        continue

    chave = f"{fase}_{grupo}"
    if chave not in grupos_exibidos:
        grupos_exibidos.add(chave)
        label_fase = "🏆 Mata-Mata" if fase == "mata-mata" else "🔵 Fase de Grupos"
        st.markdown(f"### {label_fase} › {grupo}")

    cols_header = st.columns([2, 1, 1, 1, 2, 1])
    cols_header[0].markdown("**Time A**")
    cols_header[1].markdown("**Resultado**")
    cols_header[2].markdown("**Data/Hora (Brasília)**")
    cols_header[3].markdown("**Hora UTC**")
    cols_header[4].markdown("**Time B**")
    cols_header[5].markdown("**Status**")

    for j in lista_jogos:
        cols = st.columns([2, 1, 1, 1, 2, 1])
        cols[0].markdown(f"🏴 {j['time_a']}")
        cols[1].markdown(badge_resultado(j))
        cols[2].caption(formatar_hora_br(j["data_jogo"], j["hora_utc"]))
        cols[3].caption(f"{j['hora_utc'][:5]}")
        cols[4].markdown(f"🏴 {j['time_b']}")

        agora = datetime.now(timezone.utc)
        dt_jogo = datetime.fromisoformat(f"{j['data_jogo']}T{j['hora_utc']}").replace(tzinfo=timezone.utc)
        if j["gols_a"] is not None:
            cols[5].success("✅ Finalizado")
        elif agora >= dt_jogo:
            cols[5].warning("🔴 Em jogo")
        else:
            cols[5].info("🟡 Agendado")

    st.divider()
