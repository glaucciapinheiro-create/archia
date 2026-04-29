import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import requests

# --- CÂMBIO ---
@st.cache_data(ttl=3600)
def get_usd_brl():
    try:
        r = requests.get("https://economia.awesomeapi.com.br/json/last/USD-BRL", timeout=5)
        return float(r.json()["USDBRL"]["bid"])
    except: return 5.50

st.set_page_config(page_title="ArchViz 3 Pro Studio", page_icon="🏛️", layout="wide")

# --- INTERFACE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500&display=swap');
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; background-color: #0d0f14; color: #e8e4dc; }
    .stButton > button { background: linear-gradient(135deg, #c8b478 0%, #a8944e 100%) !important; color: #0d0f14 !important; font-weight: bold; width: 100%; border-radius: 4px; }
    [data-testid="stSidebar"] { background-color: #111318; border-right: 1px solid rgba(200,180,120,0.2); }
</style>
""", unsafe_allow_html=True)

# --- PROMPT DE ELITE (ÂNCORA 3 PRO) ---
def build_elite_prompt(lighting, extra, fstop):
    return f"""ÂNCORA DE PRECISÃO GEOMÉTRICA - MODELO 3 PRO
Você é um motor de renderização fotorrealista de última geração.
REFERÊNCIA: A imagem enviada é um modelo 3D técnico que deve ser respeitado em escala 1:1.

INSTRUÇÕES DE RENDERIZAÇÃO:
1. GEOMETRIA: Tranque todos os volumes. Proibido adicionar janelas, mudar telhados ou criar portas.
2. MATERIAIS: Substitua albedos (cores lisas) por materiais PBR físicos. 
   - Concreto com micro-textura e irregularidades naturais.
   - Madeira com veios definidos e reflexo satinado.
   - Vidros com reflexo Ray Traced do céu e entorno.
3. CÂMERA: Full Frame, lente 35mm, abertura {fstop}. Estilo fotografia de revista ArchDaily.
4. ATMOSFERA: {lighting}. 
5. NOTAS DO ARQUITETO: {extra}

RESULTADO: Gere uma fotografia técnica de alta resolução (4K)."""

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Configurações")
    api_key = st.text_input("Sua Gemini API Key", type="password")
    st.divider()
    luz = st.selectbox("LUZ", ["Golden Hour (Quente)", "Dia Claro (Natural)", "Nublado (Suave)", "Noite (Artificial)"])
    fstop = st.select_slider("ABERTURA (Câmera)", options=["f/1.8 (Fundo desfocado)", "f/4.0", "f/8.0 (Nítido)", "f/11"])
    st.divider()
    brl = get_usd_brl()
    st.caption(f"Custo aprox: R$ {(0.06 * brl):.2f} por render")

# --- STUDIO ---
st.title("Estúdio ArchViz - Gemini 3 Pro")
col1, col2 = st.columns(2)

with col1:
    up = st.file_uploader("Upload Print 3D", type=["png", "jpg", "jpeg"])
    if up: st.image(up, use_container_width=True)

with col2:
    obs = st.text_area("Descrição de Materiais", placeholder="Ex: Deck de madeira cumaru, paredes brancas, esquadrias pretas...")
    go = st.button("RENDERIZAR EM 4K")

if go and up and api_key:
    with st.spinner("Processando com Gemini 3 Pro..."):
        try:
            client = genai.Client(api_key=api_key)
            # USANDO O MODELO MAIS POTENTE DE 2026
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview", 
                contents=[build_elite_prompt(luz, obs, fstop), Image.open(up)],
                config=types.GenerateContentConfig(
                    temperature=0.35, # Equilíbrio entre criatividade de textura e rigor geométrico
                    response_modalities=["IMAGE"],
                )
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    rend_img = Image.open(BytesIO(part.inline_data.data))
                    st.session_state["o"] = base64.b64encode(up.getvalue()).decode()
                    st.session_state["r"] = base64.b64encode(part.inline_data.data).decode()
                    st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")
            st.info("Se aparecer 404, mude o nome do modelo para 'gemini-1.5-pro' no código do GitHub.")

# --- VISUALIZAÇÃO ---
if "r" in st.session_state:
    st.success("Render Finalizado!")
    # O código do slider que você já tem no app.py pode ser mantido aqui abaixo
    st.image(base64.b64decode(st.session_state["r"]), caption="Render 3 Pro")
