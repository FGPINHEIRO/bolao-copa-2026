import streamlit as st
from supabase import create_client, Client
import hashlib
import os

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bolão Copa 2026",
    page_icon="⚽",
    layout="wide",
)

# ── Supabase ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    # Busca chaves dos secrets do Streamlit Cloud
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# ── Helpers ───────────────────────────────────────────────────────────────────
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def login(nome: str, senha: str):
    # Usando .table() direto; se der erro de caminho, é o nome da tabela
    resp = supabase.table("usuarios").select("*").eq("nome", nome).execute()
    if resp.data:
        u = resp.data[0]
        if u["senha_hash"] == hash_senha(senha):
            return u
    return None

def cadastrar(nome: str, senha: str):
    try:
        # Verifica duplicidade
        check = supabase.table("usuarios").select("nome").eq("nome", nome).execute()
        if check.data:
            return "existe"
        
        is_admin = nome.lower() == "admin"
        supabase.table("usuarios").insert({
            "nome": nome,
            "senha_hash": hash_senha(senha),
            "is_admin": is_admin,
        }).execute()
        return "sucesso"
    except Exception as e:
        return str(e)

# ── Lógica ────────────────────────────────────────────────────────────────────
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    tab1, tab2 = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
    
    with tab1:
        with st.form("login"):
            nome = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                u = login(nome.strip(), senha)
                if u:
                    st.session_state.usuario = u
                    st.rerun()
                else:
                    st.error("Dados inválidos.")
                    
    with tab2:
        with st.form("cadastro"):
            n = st.text_input("Novo Usuário")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Criar"):
                res = cadastrar(n.strip(), s)
                if res == "sucesso":
                    st.success("Conta criada! Pode entrar.")
                elif res == "existe":
                    st.error("Usuário já existe.")
                else:
                    st.error(f"Erro: {res}")
else:
    st.sidebar.write(f"Logado como: {st.session_state.usuario['nome']}")
    if st.sidebar.button("Sair"):
        st.session_state.usuario = None
        st.rerun()
    st.write("Bem-vindo ao Bolão!")
