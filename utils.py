# utils.py - Funções compartilhadas
import streamlit as st
from supabase import create_client, Client
import hashlib
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
    key = os.environ.get("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", ""))
    return create_client(url, key)

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def get_usuario():
    return st.session_state.get("usuario", None)

def require_login():
    """Redireciona para login se não estiver autenticado."""
    if not st.session_state.get("usuario"):
        st.warning("Faça login para acessar esta página.")
        st.stop()

def require_admin():
    """Bloqueia acesso se não for admin."""
    require_login()
    if not st.session_state["usuario"].get("is_admin"):
        st.error("Acesso restrito ao administrador.")
        st.stop()

def deadline_palpite(data_jogo: str, hora_utc: str) -> datetime:
    """Retorna o deadline: meia-noite UTC do dia anterior ao jogo."""
    dt_jogo = datetime.fromisoformat(f"{data_jogo}T{hora_utc}").replace(tzinfo=timezone.utc)
    # Final do dia anterior = início do dia do jogo (meia-noite UTC)
    dia_jogo = dt_jogo.date()
    deadline = datetime(dia_jogo.year, dia_jogo.month, dia_jogo.day,
                        0, 0, 0, tzinfo=timezone.utc)
    return deadline

def palpite_aberto(data_jogo: str, hora_utc: str) -> bool:
    """True se ainda é possível apostar."""
    return datetime.now(timezone.utc) < deadline_palpite(data_jogo, hora_utc)

def tempo_restante(data_jogo: str, hora_utc: str) -> str:
    """Formata o tempo restante até o fechamento."""
    dl = deadline_palpite(data_jogo, hora_utc)
    agora = datetime.now(timezone.utc)
    if agora >= dl:
        return "⛔ Encerrado"
    diff = dl - agora
    dias = diff.days
    horas = diff.seconds // 3600
    minutos = (diff.seconds % 3600) // 60
    if dias > 0:
        return f"⏳ Fecha em {dias}d {horas}h {minutos}m"
    elif horas > 0:
        return f"⏳ Fecha em {horas}h {minutos}m"
    else:
        return f"⚠️ Fecha em {minutos}m"

def calcular_pontos_jogo(gols_a_real, gols_b_real, gols_a_palp, gols_b_palp, is_mata_mata=False):
    """
    Regras:
    - Acertar o placar exato: 10 pts
    - Acertar vencedor/empate + gols de 1 time: 7 pts
    - Acertar vencedor/empate, nenhum gol: 5 pts  ← regra implícita
    - Errar vencedor mas acertar gols de 1 time: 2 pts
    Mata-mata: dobra os pontos.
    """
    multiplicador = 2 if is_mata_mata else 1

    resultado_real = _resultado(gols_a_real, gols_b_real)
    resultado_palp = _resultado(gols_a_palp, gols_b_palp)

    # Placar exato
    if gols_a_real == gols_a_palp and gols_b_real == gols_b_palp:
        return 10 * multiplicador

    acertou_vencedor = resultado_real == resultado_palp
    acertou_gol_a    = gols_a_real == gols_a_palp
    acertou_gol_b    = gols_b_real == gols_b_palp
    acertou_algum_gol = acertou_gol_a or acertou_gol_b

    if acertou_vencedor and acertou_algum_gol:
        return 7 * multiplicador
    if acertou_vencedor and not acertou_algum_gol:
        return 5 * multiplicador
    if not acertou_vencedor and acertou_algum_gol:
        return 2 * multiplicador
    return 0

def _resultado(gols_a, gols_b):
    if gols_a > gols_b:
        return "A"
    elif gols_b > gols_a:
        return "B"
    return "E"

def calcular_pontos_competicao(palpite: dict, resultado: dict) -> int:
    pts = 0
    if not palpite or not resultado:
        return 0
    if palpite.get("campeao") and resultado.get("campeao"):
        if palpite["campeao"] == resultado["campeao"]:
            pts += 50
    if palpite.get("vice") and resultado.get("vice"):
        if palpite["vice"] == resultado["vice"]:
            pts += 25
    if palpite.get("artilheiro") and resultado.get("artilheiro"):
        if palpite["artilheiro"] == resultado["artilheiro"]:
            pts += 25
    if palpite.get("melhor_jogador") and resultado.get("melhor_jogador"):
        if palpite["melhor_jogador"] == resultado["melhor_jogador"]:
            pts += 25
    return pts

def get_todos_times(supabase):
    """Retorna lista única de todos os times cadastrados nos jogos."""
    jogos = supabase.table("jogos").select("time_a, time_b").execute().data
    times = set()
    for j in jogos:
        times.add(j["time_a"])
        times.add(j["time_b"])
    return sorted(times)

def sidebar_autenticada(supabase):
    """Renderiza sidebar com navegação para usuário logado."""
    usuario = get_usuario()
    if not usuario:
        return
    with st.sidebar:
        st.markdown(f"### 👤 {usuario['nome']}")
        st.caption("⚽ Copa do Mundo 2026")
        st.divider()
        st.page_link("app.py",             label="🏠 Início")
        st.page_link("pages/1_Jogos.py",   label="📅 Jogos")
        st.page_link("pages/2_Palpites.py",label="🎯 Meus Palpites")
        st.page_link("pages/3_Competicao.py", label="🏆 Palpite da Competição")
        st.page_link("pages/4_Ranking.py", label="📊 Ranking")
        st.page_link("pages/5_Ver_Palpites.py", label="👁️ Ver Palpites Alheios")
        st.page_link("pages/6_Regras.py",  label="📋 Regras")
        if usuario.get("is_admin"):
            st.divider()
            st.page_link("pages/7_Admin.py", label="🔧 Administrador")
        st.divider()
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.usuario = None
            st.rerun()
