# pages/7_Admin.py - Painel do Administrador
import streamlit as st
from utils import (get_supabase, require_admin, sidebar_autenticada, get_todos_times)
from datetime import datetime, timezone

st.set_page_config(page_title="Admin | Bolão Copa 2026", page_icon="🔧", layout="wide")

supabase = get_supabase()
require_admin()
sidebar_autenticada(supabase)

st.title("🔧 Painel do Administrador")

abas = st.tabs([
    "⚽ Resultados Fase de Grupos",
    "🏆 Resultado da Competição",
    "🔴 Criar Jogos Mata-Mata",
    "📝 Resultados Mata-Mata",
    "👤 Gerenciar Usuários",
])

# ══════════════════════════════════════════════════════════════════
# ABA 1 — Resultados Fase de Grupos
# ══════════════════════════════════════════════════════════════════
with abas[0]:
    st.subheader("⚽ Inserir / Editar Resultados — Fase de Grupos")
    st.caption("Salvar um resultado atualiza automaticamente o ranking.")

    jogos_grupos = supabase.table("jogos").select("*").eq("fase", "grupos")\
        .order("data_jogo").order("hora_utc").execute().data

    grupos_dict = {}
    for j in jogos_grupos:
        grupos_dict.setdefault(j["grupo"], []).append(j)

    for grupo, lista in sorted(grupos_dict.items()):
        st.markdown(f"#### {grupo}")
        for j in lista:
            with st.container(border=True):
                st.write(f"**{j['time_a']}** vs **{j['time_b']}** — {j['data_jogo']} {j['hora_utc'][:5]} UTC")
                with st.form(f"res_grupo_{j['id']}"):
                    c1, c2 = st.columns(2)
                    ga = c1.number_input(f"Gols {j['time_a']}", min_value=0, max_value=20,
                                         value=int(j["gols_a"]) if j["gols_a"] is not None else 0,
                                         key=f"rg_a_{j['id']}")
                    gb = c2.number_input(f"Gols {j['time_b']}", min_value=0, max_value=20,
                                         value=int(j["gols_b"]) if j["gols_b"] is not None else 0,
                                         key=f"rg_b_{j['id']}")
                    salvar = st.form_submit_button("💾 Salvar resultado", use_container_width=True)
                if salvar:
                    supabase.table("jogos").update({"gols_a": ga, "gols_b": gb})\
                        .eq("id", j["id"]).execute()
                    st.success(f"✅ Resultado salvo: {j['time_a']} {ga} x {gb} {j['time_b']}")
                    st.rerun()
                elif j["gols_a"] is not None:
                    st.success(f"📊 Resultado atual: {j['gols_a']} x {j['gols_b']}")

# ══════════════════════════════════════════════════════════════════
# ABA 2 — Resultado da Competição
# ══════════════════════════════════════════════════════════════════
with abas[1]:
    st.subheader("🏆 Resultado da Competição")

    times = get_todos_times(supabase)
    times_opcoes = ["— Selecione —"] + times

    resultado_resp = supabase.table("resultado_competicao").select("*").execute()
    res = resultado_resp.data[0] if resultado_resp.data else {}

    def idx(lista, val):
        try: return lista.index(val) if val in lista else 0
        except: return 0

    with st.form("form_resultado_comp"):
        c1, c2 = st.columns(2)
        campeao = c1.selectbox("🥇 Campeão", times_opcoes, index=idx(times_opcoes, res.get("campeao")))
        vice    = c2.selectbox("🥈 Vice", times_opcoes, index=idx(times_opcoes, res.get("vice")))
        artilheiro     = c1.text_input("⚽ Artilheiro", value=res.get("artilheiro") or "")
        melhor_jogador = c2.text_input("🌟 Melhor Jogador", value=res.get("melhor_jogador") or "")
        salvar = st.form_submit_button("💾 Salvar resultado da competição", use_container_width=True)

    if salvar:
        dados = {
            "campeao": campeao if campeao != "— Selecione —" else None,
            "vice": vice if vice != "— Selecione —" else None,
            "artilheiro": artilheiro.strip() or None,
            "melhor_jogador": melhor_jogador.strip() or None,
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }
        if res.get("id"):
            supabase.table("resultado_competicao").update(dados).eq("id", res["id"]).execute()
        else:
            supabase.table("resultado_competicao").insert(dados).execute()
        st.success("✅ Resultado da competição salvo!")
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# ABA 3 — Criar Jogos Mata-Mata
# ══════════════════════════════════════════════════════════════════
with abas[2]:
    st.subheader("🔴 Criar Jogos de Mata-Mata")
    st.caption("Os jogos criados aparecem automaticamente na tabela de jogos e ficam disponíveis para palpite.")

    times = get_todos_times(supabase)

    with st.form("form_mata_mata"):
        c1, c2 = st.columns(2)
        time_a = c1.selectbox("Time A", ["— Selecione —"] + times, key="mm_ta")
        time_b = c2.selectbox("Time B", ["— Selecione —"] + times, key="mm_tb")

        fases_mata = ["Oitavas de Final", "Quartas de Final", "Semifinal", "Disputa 3º Lugar", "Final"]
        fase_sel = c1.selectbox("Fase", fases_mata)
        data_jogo = c1.date_input("Data do jogo (UTC)")
        hora_utc  = c2.time_input("Hora UTC")

        criar = st.form_submit_button("➕ Criar jogo", use_container_width=True)

    if criar:
        if time_a == "— Selecione —" or time_b == "— Selecione —":
            st.error("Selecione os dois times.")
        elif time_a == time_b:
            st.error("Os times devem ser diferentes.")
        else:
            supabase.table("jogos").insert({
                "data_jogo": str(data_jogo),
                "hora_utc":  hora_utc.strftime("%H:%M"),
                "grupo":     fase_sel,
                "time_a":    time_a,
                "time_b":    time_b,
                "fase":      "mata-mata",
            }).execute()
            st.success(f"✅ Jogo criado: {time_a} x {time_b} — {fase_sel}")
            st.rerun()

    # Listar jogos mata-mata existentes
    jogos_mm = supabase.table("jogos").select("*").eq("fase","mata-mata")\
        .order("data_jogo").order("hora_utc").execute().data
    if jogos_mm:
        st.markdown("#### Jogos de Mata-Mata Cadastrados")
        for j in jogos_mm:
            res_str = f"{j['gols_a']}x{j['gols_b']}" if j["gols_a"] is not None else "Sem resultado"
            st.write(f"🔴 **{j['grupo']}** | {j['time_a']} vs {j['time_b']} | {j['data_jogo']} {j['hora_utc'][:5]} UTC | {res_str}")

# ══════════════════════════════════════════════════════════════════
# ABA 4 — Resultados Mata-Mata
# ══════════════════════════════════════════════════════════════════
with abas[3]:
    st.subheader("📝 Inserir Resultados — Mata-Mata")

    jogos_mm = supabase.table("jogos").select("*").eq("fase","mata-mata")\
        .order("data_jogo").order("hora_utc").execute().data

    if not jogos_mm:
        st.info("Nenhum jogo de mata-mata cadastrado ainda.")
    else:
        for j in jogos_mm:
            with st.container(border=True):
                st.write(f"**{j['grupo']}** — **{j['time_a']}** vs **{j['time_b']}** — {j['data_jogo']} {j['hora_utc'][:5]} UTC")
                with st.form(f"res_mm_{j['id']}"):
                    c1, c2 = st.columns(2)
                    ga = c1.number_input(f"Gols {j['time_a']}", min_value=0, max_value=20,
                                         value=int(j["gols_a"]) if j["gols_a"] is not None else 0,
                                         key=f"mm_a_{j['id']}")
                    gb = c2.number_input(f"Gols {j['time_b']}", min_value=0, max_value=20,
                                         value=int(j["gols_b"]) if j["gols_b"] is not None else 0,
                                         key=f"mm_b_{j['id']}")
                    salvar = st.form_submit_button("💾 Salvar resultado", use_container_width=True)
                if salvar:
                    supabase.table("jogos").update({"gols_a": ga, "gols_b": gb})\
                        .eq("id", j["id"]).execute()
                    st.success(f"✅ {j['time_a']} {ga} x {gb} {j['time_b']}")
                    st.rerun()
                elif j["gols_a"] is not None:
                    st.success(f"📊 Resultado atual: {j['gols_a']} x {j['gols_b']}")

# ══════════════════════════════════════════════════════════════════
# ABA 5 — Gerenciar Usuários
# ══════════════════════════════════════════════════════════════════
with abas[4]:
    st.subheader("👤 Usuários Cadastrados")

    usuarios = supabase.table("usuarios").select("id, nome, is_admin, criado_em")\
        .order("criado_em").execute().data

    for u in usuarios:
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        c1.write(f"{'🔧' if u['is_admin'] else '👤'} {u['nome']}")
        c2.write("Admin" if u["is_admin"] else "Jogador")
        c3.write(u["criado_em"][:10] if u["criado_em"] else "—")
        if not u["is_admin"] and u["nome"] != "admin":
            if c4.button("🗑️ Remover", key=f"del_{u['id']}"):
                supabase.table("usuarios").delete().eq("id", u["id"]).execute()
                st.rerun()
        else:
            c4.write("—")

    st.divider()
    st.subheader("➕ Criar usuário admin adicional")
    with st.form("form_novo_admin"):
        novo_nome  = st.text_input("Nome")
        nova_senha = st.text_input("Senha", type="password")
        is_adm     = st.checkbox("É administrador?")
        criar_u    = st.form_submit_button("Criar usuário")
    if criar_u:
        from utils import hash_senha
        if not novo_nome or not nova_senha:
            st.error("Preencha todos os campos.")
        else:
            try:
                supabase.table("usuarios").insert({
                    "nome": novo_nome.strip(),
                    "senha_hash": hash_senha(nova_senha),
                    "is_admin": is_adm,
                }).execute()
                st.success(f"✅ Usuário '{novo_nome}' criado.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
