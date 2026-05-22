# pages/2_Palpites.py - Palpites dos jogos
import streamlit as st
from utils import (get_supabase, require_login, sidebar_autenticada,
                   palpite_aberto, tempo_restante, deadline_palpite)
from datetime import datetime, timezone
import pytz

st.set_page_config(page_title="Palpites | Bolão Copa 2026", page_icon="🎯", layout="wide")

supabase = get_supabase()
require_login()
sidebar_autenticada(supabase)

usuario = st.session_state["usuario"]

st.title("🎯 Meus Palpites")
st.caption("Prazo: até a meia-noite UTC do dia anterior a cada jogo.")

# Buscar jogos e palpites do usuário
jogos = supabase.table("jogos").select("*").order("data_jogo").order("hora_utc").execute().data
palpites_resp = supabase.table("palpites").select("*").eq("usuario_id", usuario["id"]).execute()
palpites_map = {p["jogo_id"]: p for p in (palpites_resp.data or [])}

if not jogos:
    st.info("Nenhum jogo cadastrado.")
    st.stop()

def formatar_data_br(data_jogo, hora_utc):
    dt_utc = datetime.fromisoformat(f"{data_jogo}T{hora_utc}").replace(tzinfo=timezone.utc)
    br_tz = pytz.timezone("America/Sao_Paulo")
    return dt_utc.astimezone(br_tz).strftime("%d/%m %H:%M")

# Filtro de fase
fase_sel = st.radio("Filtrar:", ["Todos", "Abertos", "Encerrados"], horizontal=True)

# Agrupar por fase/grupo
grupos = {}
for j in jogos:
    k = (j["fase"], j["grupo"])
    grupos.setdefault(k, []).append(j)

for (fase, grupo), lista in sorted(grupos.items()):
    label = "🏆 Mata-Mata" if fase == "mata-mata" else "🔵 Fase de Grupos"
    st.markdown(f"### {label} › {grupo}")

    for j in lista:
        aberto = palpite_aberto(j["data_jogo"], j["hora_utc"])
        if fase_sel == "Abertos" and not aberto:
            continue
        if fase_sel == "Encerrados" and aberto:
            continue

        palpite_atual = palpites_map.get(j["id"])
        data_br = formatar_data_br(j["data_jogo"], j["hora_utc"])
        tr = tempo_restante(j["data_jogo"], j["hora_utc"])

        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 3])
            c1.markdown(f"### 🏴 {j['time_a']}")
            c2.markdown(f"<div style='text-align:center;padding-top:8px'><b>{data_br} UTC+0</b><br><small>{tr}</small></div>",
                       unsafe_allow_html=True)
            c3.markdown(f"### 🏴 {j['time_b']}")

            if aberto:
                val_a = palpite_atual["gols_a"] if palpite_atual else 0
                val_b = palpite_atual["gols_b"] if palpite_atual else 0

                with st.form(f"palpite_{j['id']}"):
                    col1, col2, col3 = st.columns([2, 1, 2])
                    with col1:
                        ga = st.number_input(f"Gols {j['time_a']}", min_value=0, max_value=20,
                                             value=int(val_a), key=f"ga_{j['id']}")
                    with col2:
                        st.markdown("<br><div style='text-align:center;font-size:1.5rem'>×</div>",
                                   unsafe_allow_html=True)
                    with col3:
                        gb = st.number_input(f"Gols {j['time_b']}", min_value=0, max_value=20,
                                             value=int(val_b), key=f"gb_{j['id']}")

                    if palpite_atual:
                        st.caption(f"✅ Palpite atual: **{palpite_atual['gols_a']} x {palpite_atual['gols_b']}**")

                    submitted = st.form_submit_button("💾 Salvar palpite", use_container_width=True)

                if submitted:
                    # Verifica deadline novamente no momento do submit
                    if not palpite_aberto(j["data_jogo"], j["hora_utc"]):
                        st.error("⛔ Prazo encerrado!")
                    else:
                        if palpite_atual:
                            supabase.table("palpites").update({
                                "gols_a": ga, "gols_b": gb,
                                "atualizado_em": datetime.now(timezone.utc).isoformat()
                            }).eq("id", palpite_atual["id"]).execute()
                        else:
                            supabase.table("palpites").insert({
                                "usuario_id": usuario["id"],
                                "jogo_id": j["id"],
                                "gols_a": ga, "gols_b": gb,
                            }).execute()
                        st.success(f"✅ Palpite salvo: {ga} x {gb}")
                        st.rerun()
            else:
                # Palpite encerrado – mostra o palpite do usuário
                if palpite_atual:
                    st.info(f"🎯 Seu palpite: **{palpite_atual['gols_a']} x {palpite_atual['gols_b']}**")
                else:
                    st.warning("⛔ Você não fez palpite para este jogo.")

                if j["gols_a"] is not None:
                    st.success(f"📊 Resultado oficial: **{j['gols_a']} x {j['gols_b']}**")

        st.markdown("")

    st.divider()
