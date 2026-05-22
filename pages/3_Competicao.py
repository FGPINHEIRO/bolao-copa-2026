# pages/3_Competicao.py - Palpites da Competição
import streamlit as st
from utils import (get_supabase, require_login, sidebar_autenticada,
                   get_todos_times, palpite_aberto)
from datetime import datetime, timezone

st.set_page_config(page_title="Competição | Bolão Copa 2026", page_icon="🏆", layout="wide")

supabase = get_supabase()
require_login()
sidebar_autenticada(supabase)

usuario = st.session_state["usuario"]

st.title("🏆 Palpite da Competição")
st.caption("Palpite o campeão, vice, artilheiro e melhor jogador. Prazo: mesmo do primeiro jogo.")

# ── Verificar deadline: primeiro jogo da fase de grupos ──────────────────────
primeiro_jogo = supabase.table("jogos").select("data_jogo, hora_utc").eq("fase", "grupos")\
    .order("data_jogo").order("hora_utc").limit(1).execute().data

if not primeiro_jogo:
    st.info("Nenhum jogo cadastrado.")
    st.stop()

pj = primeiro_jogo[0]
aberto = palpite_aberto(pj["data_jogo"], pj["hora_utc"])
from utils import tempo_restante
tr = tempo_restante(pj["data_jogo"], pj["hora_utc"])

if aberto:
    st.info(f"⏳ {tr} para o prazo encerrar (primeiro jogo: {pj['data_jogo']} {pj['hora_utc'][:5]} UTC)")
else:
    st.error("⛔ Prazo encerrado para palpites da competição.")

# ── Buscar times e palpite atual do usuário ──────────────────────────────────
times = get_todos_times(supabase)
times_opcoes = ["— Selecione —"] + times

palpite_resp = supabase.table("palpites_competicao").select("*")\
    .eq("usuario_id", usuario["id"]).execute()
palpite_atual = palpite_resp.data[0] if palpite_resp.data else None

# ── Resultado oficial (para exibir se já divulgado) ──────────────────────────
resultado_resp = supabase.table("resultado_competicao").select("*").execute()
resultado = resultado_resp.data[0] if resultado_resp.data else {}

def idx(lista, val):
    try:
        return lista.index(val) if val in lista else 0
    except:
        return 0

st.divider()

# ── Formulário ───────────────────────────────────────────────────────────────
with st.form("form_competicao"):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🥇 Campeão")
        campeao = st.selectbox("Selecione o campeão", times_opcoes,
                               index=idx(times_opcoes, palpite_atual["campeao"] if palpite_atual else None))
        st.subheader("🥈 Vice-campeão")
        vice = st.selectbox("Selecione o vice", times_opcoes,
                            index=idx(times_opcoes, palpite_atual["vice"] if palpite_atual else None))

    with col2:
        st.subheader("⚽ Artilheiro")
        artilheiro = st.text_input("Nome do artilheiro",
                                   value=palpite_atual["artilheiro"] if palpite_atual and palpite_atual.get("artilheiro") else "")
        st.subheader("🌟 Melhor Jogador")
        melhor_jogador = st.text_input("Nome do melhor jogador",
                                       value=palpite_atual["melhor_jogador"] if palpite_atual and palpite_atual.get("melhor_jogador") else "")

    salvar = st.form_submit_button("💾 Salvar palpites da competição",
                                   use_container_width=True,
                                   disabled=not aberto)

if salvar:
    if campeao == "— Selecione —" or vice == "— Selecione —":
        st.error("Selecione campeão e vice.")
    elif campeao == vice:
        st.error("Campeão e vice não podem ser o mesmo time.")
    elif not artilheiro.strip() or not melhor_jogador.strip():
        st.error("Preencha artilheiro e melhor jogador.")
    else:
        dados = {
            "usuario_id": usuario["id"],
            "campeao": campeao,
            "vice": vice,
            "artilheiro": artilheiro.strip(),
            "melhor_jogador": melhor_jogador.strip(),
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }
        if palpite_atual:
            supabase.table("palpites_competicao").update(dados)\
                .eq("id", palpite_atual["id"]).execute()
        else:
            supabase.table("palpites_competicao").insert(dados).execute()
        st.success("✅ Palpites da competição salvos!")
        st.rerun()

# ── Exibir palpite atual ─────────────────────────────────────────────────────
if palpite_atual:
    st.divider()
    st.subheader("📋 Seus palpites atuais")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🥇 Campeão", palpite_atual.get("campeao") or "—")
    c2.metric("🥈 Vice", palpite_atual.get("vice") or "—")
    c3.metric("⚽ Artilheiro", palpite_atual.get("artilheiro") or "—")
    c4.metric("🌟 Melhor Jogador", palpite_atual.get("melhor_jogador") or "—")

# ── Resultado oficial ────────────────────────────────────────────────────────
if any(resultado.get(k) for k in ["campeao", "vice", "artilheiro", "melhor_jogador"]):
    st.divider()
    st.subheader("🏆 Resultado Oficial")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🥇 Campeão", resultado.get("campeao") or "—")
    c2.metric("🥈 Vice", resultado.get("vice") or "—")
    c3.metric("⚽ Artilheiro", resultado.get("artilheiro") or "—")
    c4.metric("🌟 Melhor Jogador", resultado.get("melhor_jogador") or "—")
