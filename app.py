# app.py - Ponto de entrada do Bolão Copa do Mundo 2026
import streamlit as st
from supabase import create_client, Client
import hashlib
import os

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bolão Copa 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Supabase ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    # Busca chaves diretamente dos secrets do Streamlit
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ── Helpers ───────────────────────────────────────────────────────────────────
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def login(nome: str, senha: str):
    resp = supabase.table("usuarios").select("*").eq("nome", nome).execute()
    if resp.data:
        u = resp.data[0]
        if u["senha_hash"] == hash_senha(senha):
            return u
    return None

def cadastrar(nome: str, senha: str):
    try:
        # Verifica se o usuário já existe antes de tentar inserir
        check = supabase.table("usuarios").select("nome").eq("nome", nome).execute()
        if check.data:
            return None # Usuário já existe
        
        is_admin = nome.lower() == "admin"
        resp = supabase.table("usuarios").insert({
            "nome": nome,
            "senha_hash": hash_senha(senha),
            "is_admin": is_admin,
        }).execute()
        
        return resp.data[0] if resp.data else True
    except Exception as e:
        st.error(f"Erro no banco: {e}")
        return None

# ── Session state ─────────────────────────────────────────────────────────────
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ── Login / Cadastro ──────────────────────────────────────────────────────────
def pagina_login():
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1rem'>
            <h1>⚽ Bolão Copa do Mundo 2026</h1>
            <p style='color:#888'>Faça login ou crie sua conta para participar</p>
        </div>
        """, unsafe_allow_html=True)

        aba = st.tabs(["🔑 Entrar", "📝 Criar Conta"])

        with aba[0]:
            with st.form("form_login"):
                nome  = st.text_input("Nome de usuário")
                senha = st.text_input("Senha", type="password")
                ok    = st.form_submit_button("Entrar", use_container_width=True)
            if ok:
                if not nome or not senha:
                    st.error("Preencha nome e senha.")
                else:
                    u = login(nome.strip(), senha)
                    if u:
                        st.session_state.usuario = u
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")

        with aba[1]:
            with st.form("form_cadastro"):
                novo_nome  = st.text_input("Nome de usuário", key="reg_nome")
                nova_senha = st.text_input("Senha", type="password", key="reg_senha")
                conf_senha = st.text_input("Confirmar senha", type="password", key="reg_conf")
                ok2        = st.form_submit_button("Criar conta", use_container_width=True)
            if ok2:
                if not novo_nome or not nova_senha:
                    st.error("Preencha todos os campos.")
                elif nova_senha != conf_senha:
                    st.error("As senhas não coincidem.")
                elif len(nova_senha) < 4:
                    st.error("A senha deve ter pelo menos 4 caracteres.")
                else:
                    u = cadastrar(novo_nome.strip(), nova_senha)
                    if u:
                        st.success("Conta criada! Pode entrar na aba Entrar.")
                    else:
                        st.error("Nome de usuário já existe ou erro no banco.")

# ── Sidebar ──────────────────────────────────────────────────────────────────
def sidebar_nav():
    with st.sidebar:
        if st.session_state.usuario:
            st.markdown(f"### 👤 {st.session_state.usuario['nome']}")
            if st.session_state.usuario.get("is_admin"):
                st.success("Administrador")
            st.caption("Copa do Mundo 2026")
            st.divider()
            if st.button("🚪 Sair", use_container_width=True):
                st.session_state.usuario = None
                st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
if st.session_state.usuario is None:
    pagina_login()
else:
    sidebar_nav()
    st.markdown(f"## ⚽ Bolão Copa do Mundo 2026")
    st.info("Use o menu lateral para navegar entre as abas.")
