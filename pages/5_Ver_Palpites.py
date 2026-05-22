# pages/5_Ver_Palpites.py - Ver palpites de outros usuários
import streamlit as st
from utils import get_supabase, require_login, sidebar_autenticada, palpite_aberto
from datetime import datetime, timezone

st.set_page_config(page_title="Ver Palpites | Bolão Copa 2026", page_icon="👁️", layout="wide")

supabase = get_supabase()
require_login()
sidebar_autenticada(supabase)

usuario_atual = st.session_state["usuario"]

st.title("👁️ Ver Palpites Alheios")
st.caption("Apenas palpites de jogos cujo prazo já encerrou são exibidos.")

# ── Carregar dados ────────────────────────────────────────────────────────────
jogos = supabase.table("jogos").select("*").order("data_jogo").order("hora_utc").execute().data
usuarios = supabase.table("usuarios").select("id, nome").execute().data
palpites = supabase.table("palpites").select("*").execute().data
palpites_comp = supabase.table("palpites_competicao").select("*").execute().data

# Filtrar apenas jogos com prazo encerrado
jogos_encerrados = [j for j in jogos if not palpite_aberto(j["data_jogo"], j["hora_utc"])]

if not jogos_encerrados:
    st.info("Nenhum jogo com prazo encerrado ainda. Volte quando o primeiro prazo fechar.")
    st.stop()

# Indexar
usuarios_map = {u["id"]: u["nome"] for u in usuarios}
palpites_por_jogo = {}
for p in palpites:
    palpites_por_jogo.setdefault(p["jogo_id"], []).append(p)

palpites_comp_map = {p["usuario_id"]: p for p in palpites_comp}

# ── Seletor de jogo ────────────────────────────────────────────────────────────
st.subheader("🎯 Palpites por Jogo")

opcoes_jogos = {
    j["id"]: f"{j['data_jogo']} | {j['grupo']} | {j['time_a']} x {j['time_b']}"
    for j in jogos_encerrados
}

jogo_sel_id = st.selectbox("Selecione o jogo:", options=list(opcoes_jogos.keys()),
                            format_func=lambda x: opcoes_jogos[x])

if jogo_sel_id:
    jogo = next(j for j in jogos if j["id"] == jogo_sel_id)
    pals = palpites_por_jogo.get(jogo_sel_id, [])

    resultado_str = f"{jogo['gols_a']} x {jogo['gols_b']}" if jogo["gols_a"] is not None else "Aguardando"

    c1, c2, c3 = st.columns(3)
    c1.metric("Time A", jogo["time_a"])
    c2.metric("Resultado Oficial", resultado_str)
    c3.metric("Time B", jogo["time_b"])

    st.divider()
    if not pals:
        st.info("Nenhum palpite registrado para este jogo.")
    else:
        cols = st.columns([2, 1, 1, 1])
        cols[0].markdown("**Usuário**")
        cols[1].markdown("**Palpite**")
        cols[2].markdown("**Resultado**")
        cols[3].markdown("**Pontos**")

        from utils import calcular_pontos_jogo
        is_mata = jogo["fase"] == "mata-mata"
        pals_sorted = sorted(pals, key=lambda p: (
            -calcular_pontos_jogo(
                jogo["gols_a"] or 0, jogo["gols_b"] or 0,
                p["gols_a"], p["gols_b"], is_mata
            ) if jogo["gols_a"] is not None else 0
        ))

        for p in pals_sorted:
            nome = usuarios_map.get(p["usuario_id"], "?")
            palpite_str = f"{p['gols_a']} x {p['gols_b']}"
            eh_voce = p["usuario_id"] == usuario_atual["id"]
            marcador = " 👈 você" if eh_voce else ""

            if jogo["gols_a"] is not None:
                pts = calcular_pontos_jogo(
                    jogo["gols_a"], jogo["gols_b"],
                    p["gols_a"], p["gols_b"], is_mata
                )
                pts_str = f"{pts} pts"
                acertou = p["gols_a"] == jogo["gols_a"] and p["gols_b"] == jogo["gols_b"]
                icone = "🎯" if acertou else ("✅" if pts > 0 else "❌")
            else:
                pts_str = "—"
                icone = "🕐"

            cols = st.columns([2, 1, 1, 1])
            cols[0].write(f"{icone} {nome}{marcador}")
            cols[1].write(palpite_str)
            cols[2].write(resultado_str)
            cols[3].write(pts_str)

# ── Palpites da competição (se prazo encerrado) ────────────────────────────────
primeiro_jogo = supabase.table("jogos").select("data_jogo, hora_utc").eq("fase","grupos")\
    .order("data_jogo").order("hora_utc").limit(1).execute().data
comp_encerrado = not palpite_aberto(primeiro_jogo[0]["data_jogo"], primeiro_jogo[0]["hora_utc"]) if primeiro_jogo else False

if comp_encerrado and palpites_comp:
    st.divider()
    st.subheader("🏆 Palpites da Competição")

    resultado_comp_resp = supabase.table("resultado_competicao").select("*").execute()
    resultado_comp = resultado_comp_resp.data[0] if resultado_comp_resp.data else {}

    cols = st.columns([2, 1, 1, 1, 1])
    cols[0].markdown("**Usuário**")
    cols[1].markdown("**Campeão**")
    cols[2].markdown("**Vice**")
    cols[3].markdown("**Artilheiro**")
    cols[4].markdown("**Melhor Jogador**")

    for p in palpites_comp:
        nome = usuarios_map.get(p["usuario_id"], "?")
        eh_voce = p["usuario_id"] == usuario_atual["id"]
        marcador = " 👈" if eh_voce else ""
        cols = st.columns([2, 1, 1, 1, 1])
        cols[0].write(f"{nome}{marcador}")
        cols[1].write(p.get("campeao") or "—")
        cols[2].write(p.get("vice") or "—")
        cols[3].write(p.get("artilheiro") or "—")
        cols[4].write(p.get("melhor_jogador") or "—")
