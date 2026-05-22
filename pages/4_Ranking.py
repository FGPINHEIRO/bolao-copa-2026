# pages/4_Ranking.py - Ranking
import streamlit as st
from utils import (get_supabase, require_login, sidebar_autenticada,
                   calcular_pontos_jogo, calcular_pontos_competicao)

st.set_page_config(page_title="Ranking | Bolão Copa 2026", page_icon="📊", layout="wide")

supabase = get_supabase()
require_login()
sidebar_autenticada(supabase)

usuario_atual = st.session_state["usuario"]

st.title("📊 Ranking")

# ── Carregar dados ────────────────────────────────────────────────────────────
usuarios = supabase.table("usuarios").select("id, nome").execute().data
jogos = supabase.table("jogos").select("*").execute().data
palpites = supabase.table("palpites").select("*").execute().data
palpites_comp = supabase.table("palpites_competicao").select("*").execute().data
resultado_comp_resp = supabase.table("resultado_competicao").select("*").execute()
resultado_comp = resultado_comp_resp.data[0] if resultado_comp_resp.data else {}

# Indexar jogos com resultado
jogos_com_resultado = {j["id"]: j for j in jogos if j["gols_a"] is not None and j["gols_b"] is not None}

# Indexar palpites por (usuario_id, jogo_id)
palpites_idx = {}
for p in palpites:
    palpites_idx[(p["usuario_id"], p["jogo_id"])] = p

# Indexar palpites_comp por usuario_id
palpites_comp_idx = {p["usuario_id"]: p for p in palpites_comp}

# ── Calcular pontuação de cada usuário ───────────────────────────────────────
ranking = []
detalhes_usuarios = {}

for u in usuarios:
    if u["nome"] == "admin":
        continue
    uid = u["id"]
    pontos_total = 0
    acertos_exatos = 0
    jogos_palpitados = 0
    detalhes = []

    # Pontos por jogo
    for jogo_id, jogo in jogos_com_resultado.items():
        p = palpites_idx.get((uid, jogo_id))
        if p is None:
            continue
        jogos_palpitados += 1
        is_mata = jogo["fase"] == "mata-mata"
        pts = calcular_pontos_jogo(
            jogo["gols_a"], jogo["gols_b"],
            p["gols_a"], p["gols_b"],
            is_mata_mata=is_mata
        )
        pontos_total += pts
        if pts == 10 or (pts == 20 and is_mata):
            acertos_exatos += 1
        detalhes.append({
            "jogo": f"{jogo['time_a']} x {jogo['time_b']}",
            "resultado": f"{jogo['gols_a']}x{jogo['gols_b']}",
            "palpite": f"{p['gols_a']}x{p['gols_b']}",
            "pontos": pts,
            "fase": jogo["fase"],
        })

    # Pontos da competição
    p_comp = palpites_comp_idx.get(uid)
    pts_comp = calcular_pontos_competicao(p_comp, resultado_comp)
    pontos_total += pts_comp

    ranking.append({
        "usuario": u["nome"],
        "id": uid,
        "pontos": pontos_total,
        "acertos_exatos": acertos_exatos,
        "jogos_palpitados": jogos_palpitados,
        "pts_competicao": pts_comp,
    })
    detalhes_usuarios[uid] = detalhes

ranking.sort(key=lambda x: (-x["pontos"], -x["acertos_exatos"]))

# ── Exibir pódio ──────────────────────────────────────────────────────────────
if ranking:
    st.subheader("🏅 Pódio")
    cols = st.columns(min(3, len(ranking)))
    medalhas = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(ranking[:3]):
        with cols[i]:
            destaque = "**" if r["id"] == usuario_atual["id"] else ""
            st.metric(
                label=f"{medalhas[i]} {destaque}{r['usuario']}{destaque}",
                value=f"{r['pontos']} pts",
                delta=f"{r['acertos_exatos']} placares exatos",
            )

st.divider()

# ── Tabela completa ───────────────────────────────────────────────────────────
st.subheader("📋 Classificação Geral")

for pos, r in enumerate(ranking, 1):
    eh_voce = r["id"] == usuario_atual["id"]
    cor = "🟢" if eh_voce else "⚪"
    with st.expander(f"{cor} #{pos} — {r['usuario']}  |  **{r['pontos']} pts**  ({r['jogos_palpitados']} jogos palpitados)", expanded=eh_voce):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Pontos", r["pontos"])
        c2.metric("Placares Exatos", r["acertos_exatos"])
        c3.metric("Jogos Palpitados", r["jogos_palpitados"])
        c4.metric("Pts Competição", r["pts_competicao"])

        det = detalhes_usuarios.get(r["id"], [])
        if det:
            st.markdown("**Detalhamento por jogo:**")
            for d in det:
                icone = "✅" if d["pontos"] > 0 else "❌"
                fase_label = "(mata-mata)" if d["fase"] == "mata-mata" else ""
                st.write(f"{icone} {d['jogo']} {fase_label} → resultado: {d['resultado']} | seu palpite: {d['palpite']} → **{d['pontos']} pts**")

st.divider()
st.caption("Atualizado em tempo real conforme resultados são inseridos pelo administrador.")
