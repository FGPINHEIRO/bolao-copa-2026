import streamlit as st
from supabase import create_client, Client
import hashlib

# ── Configuração ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Bolão Copa 2026", layout="wide")

@st.cache_resource
def get_supabase():
    # Certifique-se de que SUPABASE_URL e SUPABASE_KEY estão nos Secrets
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

# ── Funções de Banco ────────────────────────────────────────────────────────
def login(nome, senha):
    try:
        # Usamos .table("usuarios") direto
        resp = supabase.table("usuarios").select("*").eq("nome", nome).execute()
        if resp.data:
            u = resp.data[0]
            if u["senha_hash"] == hash_senha(senha):
                return u
        return None
    except Exception as e:
        st.error(f"Erro de Banco: {str(e)}")
        return None

def cadastrar(nome, senha):
    try:
        dados = {"nome": nome, "senha_hash": hash_senha(senha), "is_admin": (nome.lower() == "admin")}
        supabase.table("usuarios").insert(dados).execute()
        return "sucesso"
    except Exception as e:
        return str(e)

# ── UI ──────────────────────────────────────────────────────────────────────
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if not st.session_state.usuario:
    aba1, aba2 = st.tabs(["Entrar", "Criar Conta"])
    with aba1:
        with st.form("l"):
            n = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                u = login(n, s)
                if u:
                    st.session_state.usuario = u
                    st.rerun()
                else:
                    st.error("Falha no login.")
    with aba2:
        with st.form("c"):
            n = st.text_input("Novo Usuário")
            s = st.text_input("Nova Senha", type="password")
            if st.form_submit_button("Cadastrar"):
                res = cadastrar(n, s)
                if res == "sucesso":
                    st.success("Conta criada!")
                else:
                    st.error(f"Erro: {res}")
else:
    st.write(f"Bem-vindo, {st.session_state.usuario['nome']}!")
    if st.button("Sair"):
        st.session_state.usuario = None
        st.rerun()
