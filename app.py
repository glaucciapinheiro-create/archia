import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import requests

# ─── CÂMBIO USD → BRL ───
@st.cache_data(ttl=3600)
def get_usd_brl():
    try:
        r = requests.get("https://economia.awesomeapi.com.br/json/last/USD-BRL", timeout=5)
        return float(r.json()["USDBRL"]["bid"])
    except: return 5.50

# ─── CONFIGURAÇÃO DA PÁGINA ───
st.set_page_config(page_title="AI ArchViz Studio", page_icon="🏛️", layout="wide")

# ─── CSS CUSTOMIZADO (CORREÇÃO DE LEGIBILIDADE E LIMPEZA) ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Cormorant+Garamond:wght@300;400;600&family=Space+Grotesk:wght@300;400;500&display=swap');
    
    /* Esconder Barra do GitHub e Rodapé do Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* Fundo e Texto Global */
    html, body, [class*="css"] { 
        font-family: 'Space Grotesk', sans-serif; 
        background-color: #0d0f14; 
        color: #e8e4dc !important; /* Força o texto para off-white */
    }

    .stApp { background-color: #0d0f14; }

    /* Correção de Legibilidade em Labels e Textos */
    label, .stMarkdown, p, span, .stTextArea label, .stSelectbox label {
        color: #e8e4dc !important;
        font-weight: 400 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #111318; 
        border-right: 1px solid rgba(200,180,120,0.2); 
    }

    /* Títulos */
    h1 { 
        font-family: 'Cormorant Garamond', serif !important; 
        color: #e8e4dc !important; 
        border-bottom: 1px solid rgba(200,180,120,0.3); 
        padding-bottom: 0.5rem;
    }
    
    h2, h3 { 
        font-family: 'DM Mono', monospace !important; 
        color: #c8b478 !important; 
        letter-spacing: 0.15em !important;
    }

    /* Botão Dourado */
    .stButton > button { 
        background: linear-gradient(135deg, #c8b478 0%, #a8944e 100%) !important; 
        color: #0d0f14 !important; 
        font-family: 'DM Mono', monospace !important; 
        border-radius: 2px !important; 
        font-weight: bold !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── SEUS PROMPTS (COLE OS TEXTOS AQUI) ───

PROMPT_EXTERNO = """
[COLE AQUI SEU PROMPT DE ÁREA EXTERNA]
"""

PROMPT_INTERNO = """
[COLE AQUI SEU PROMPT DE ÁREA INTERNA]
"""

# ─── LÓGICA DE PROMPT ───
def build_final_prompt(ambiente, lighting, style, extra, fstop):
    regra_base = PROMPT_EXTERNO if ambiente == "Área Externa" else PROMPT_INTERNO
    return f"""{regra_base}
DADOS DA INTERFACE:
- Iluminação: {lighting}
- Estilo: {style}
- Lente/Abertura: {fstop}
- Notas: {extra}
Gere o render fotorrealista final respeitando a geometria 1:1."""

# ─── SIDEBAR ───
with st.sidebar:
    st.markdown("## ⬡ ACESSO")
    api_key = st.text_input("GEMINI API KEY", type="password")
    
    st.divider()
    st.markdown("## ⬡ PROJETO")
    ambiente = st.radio("TIPO DE AMBIENTE", ["Área Externa", "Área Interna"])
    
    st.divider()
    st.markdown("## ⬡ PARÂMETROS")
    lighting = st.selectbox("LUZ", ["Golden Hour", "Dia Claro", "Pôr do Sol", "Noturno"])
    style = st.selectbox("ESTILO", ["Fotorrealista", "Maquete", "Artístico"])
    fstop = st.select_slider("ABERTURA", options=["f/1.8", "f/2.8", "f/8.0"], value="f/8.0")
    
    st.divider()
    brl_rate = get_usd_brl()
    st.caption(f"Câmbio atual: R$ {brl_rate:.2f}")

# ─── CORPO DO APP ───
st.markdown("# AI ArchViz Studio")

c1, c2 = st.columns(2)
with c1:
    st.markdown("### 1. MODELO 3D")
    upload = st.file_uploader("Upload do Print", type=["png", "jpg", "jpeg"])
    if upload: st.image(upload, use_container_width=True)

with c2:
    st.markdown("### 2. DETALHES")
    notes = st.text_area("Notas de Materiais", placeholder="Ex: Piso em carvalho, paredes em concreto...", height=150)
    btn = st.button(f"GERAR RENDER {ambiente.upper()}")

if btn and upload and api_key:
    with st.spinner(f"Processando {ambiente} no Gemini 3 Pro..."):
        try:
            client = genai.Client(api_key=api_key)
            final_p = build_final_prompt(ambiente, lighting, style, notes, fstop)
            
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=[final_p, Image.open(upload)],
                config=types.GenerateContentConfig(temperature=0.4, response_modalities=["IMAGE"])
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    st.session_state["o"] = base64.b64encode(upload.getvalue()).decode()
                    st.session_state["r"] = base64.b64encode(part.inline_data.data).decode()
                    st.rerun()
        except Exception as e:
            st.error(f"Erro técnico: {e}")

# ─── EXIBIÇÃO ───
if "r" in st.session_state:
    st.divider()
    st.markdown("### RESULTADO FINAL")
    st.image(base64.b64decode(st.session_state["r"]), use_container_width=True)
