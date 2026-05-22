# pages/6_Regras.py - Regras do Bolão
import streamlit as st
from utils import get_supabase, require_login, sidebar_autenticada

st.set_page_config(page_title="Regras | Bolão Copa 2026", page_icon="📋", layout="wide")

supabase = get_supabase()
require_login()
sidebar_autenticada(supabase)

st.title("📋 Regras do Bolão")

st.markdown("""
## ⚽ Copa do Mundo 2026 — Bolão Oficial

---

## 🎯 Regras para Palpites

### Prazo para palpites de jogos
- O prazo para realizar ou alterar o palpite de cada jogo é até **meia-noite UTC do dia anterior** à partida.
- Após este horário, o palpite fica bloqueado e não pode mais ser alterado.
- Você pode **alterar seu palpite quantas vezes quiser** antes do prazo.
- O site exibe um contador mostrando **quanto tempo falta** para o prazo encerrar.

### Prazo para palpites da competição
- Os palpites de **campeão, vice, artilheiro e melhor jogador** têm o mesmo prazo do **primeiro jogo** da fase de grupos.
- Após esse prazo, nenhuma alteração será aceita.

### Palpites obrigatórios
- Não é obrigatório palpitar em todos os jogos — apenas os jogos palpitados entram na pontuação.

---

## 🏆 Sistema de Pontuação

### Palpites de Jogos

| Situação | Pontos (Grupos) | Pontos (Mata-Mata) |
|----------|:--------------:|:------------------:|
| ✅ Acertar o **placar exato** | **10 pts** | **20 pts** |
| 🎯 Acertar o **vencedor/empate** + gols de **1 time** | **7 pts** | **14 pts** |
| 🔵 Acertar o **vencedor/empate**, mas nenhum gol | **5 pts** | **10 pts** |
| 🟡 Errar vencedor, mas acertar gols de **1 time** | **2 pts** | **4 pts** |
| ❌ Errar tudo | **0 pts** | **0 pts** |

> 🔴 **Jogos de mata-mata valem o dobro de pontos.**

### Palpites da Competição

| Acerto | Pontos |
|--------|:------:|
| 🥇 Campeão | **50 pts** |
| 🥈 Vice-campeão | **25 pts** |
| ⚽ Artilheiro | **25 pts** |
| 🌟 Melhor Jogador | **25 pts** |

---

## 👁️ Ver Palpites Alheios

- Os palpites de todos os participantes ficam **visíveis** na aba "Ver Palpites Alheios" após o prazo de cada jogo.
- Os palpites da competição ficam visíveis após o prazo do primeiro jogo.

---

## 📊 Ranking

- O ranking é calculado **automaticamente** com base nos resultados inseridos pelo administrador.
- Em caso de empate de pontos, o critério de desempate é o número de **placares exatos** acertados.
- O ranking é atualizado em **tempo real**.

---

## 🔧 Administrador

- Apenas o usuário **admin** pode inserir resultados, criar jogos de mata-mata e definir os vencedores da competição.
- Resultados inseridos aparecem **imediatamente** na tabela de jogos e no ranking.

---

*Dúvidas? Fale com o organizador do bolão.*
""")
