import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
from datetime import datetime
import requests

# ─── CÂMBIO USD → BRL ───
@st.cache_data(ttl=3600)
def get_usd_brl() -> float:
    try:
        r = requests.get("https://economia.awesomeapi.com.br/json/last/USD-BRL", timeout=5)
        return float(r.json()["USDBRL"]["bid"])
    except: return 5.50

st.set_page_config(page_title="AI ArchViz Studio", page_icon="🏛️", layout="wide")

# ─── ESTILO VISUAL ORIGINAL (DARK & GOLD) ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Cormorant+Garamond:wght@300;400;600&family=Space+Grotesk:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stApp { background-color: #0d0f14; color: #e8e4dc; }
[data-testid="stSidebar"] { background-color: #111318; border-right: 1px solid rgba(200,180,120,0.2); }
h1 { font-family: 'Cormorant Garamond', serif !important; color: #e8e4dc !important; border-bottom: 1px solid rgba(200,180,120,0.3); }
.stButton > button { background: linear-gradient(135deg, #c8b478 0%, #a8944e 100%) !important; color: #0d0f14 !important; font-family: 'DM Mono', monospace !important; border-radius: 2px !important; }
</style>
""", unsafe_allow_html=True)

# ─── SLIDER DE COMPARAÇÃO ───
def compare_slider_html(b64_before: str, b64_after: str, height: int = 500) -> str:
    return f"""
    <!DOCTYPE html><html><head><style>
    body {{ background: #0d0f14; margin: 0; display: flex; justify-content: center; }}
    .wrap {{ position: relative; width: 100%; height: {height}px; overflow: hidden; cursor: col-resize; border: 1px solid rgba(200,180,120,0.3); }}
    .img {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; }}
    .before {{ z-index: 2; clip-path: inset(0 50% 0 0); }}
    .divider {{ position: absolute; top: 0; bottom: 0; left: 50%; width: 2px; background: #c8b478; z-index: 10; }}
    </style></head><body>
    <div class="wrap" onmousemove="move(event)" ontouchmove="move(event.touches[0])">
        <img class="img" src="data:image/png;base64,{b64_after}">
        <img id="bf" class="img before" src="data:image/png;base64,{b64_before}">
        <div id="dv" class="divider"></div>
    </div>
    <script>
    function move(e) {{
        let r = e.currentTarget.getBoundingClientRect();
        let p = ((e.clientX - r.left) / r.width) * 100;
        document.getElementById('dv').style.left = p + '%';
        document.getElementById('bf').style.clipPath = 'inset(0 ' + (100 - p) + '% 0 0)';
    }}
    </script></body></html>
    """

# ─── PROMPT AJUSTADO (PRECISÃO + TEXTURA) ───
def build_prompt(lighting, style, extra, fstop):
    return f"""ÂNCORA ABSOLUTA: GEOMETRIA 1:1.
Transforme o modelo 3D em fotografia profissional.
REGRAS:
1. GEOMETRIA: Mantenha paredes e volumes imóveis.
2. TEXTURAS PBR: Substitua cores lisas por materiais REAIS (concreto, madeira carvalho, vidro reflexivo).
3. CÂMERA: Sony A7R V, {fstop}.
4. LUZ: {lighting}. Estilo {style}.
NOTAS: {extra}"""

# ─── SIDEBAR ───
with st.sidebar:
    st.markdown("## ⬡ API")
    api_key = st.text_input("GEMINI API KEY", type="password")
    st.divider()
    st.markdown("## ⬡ PARÂMETROS")
    lighting = st.selectbox("ILUMINAÇÃO", ["Golden Hour", "Dia Claro", "Pôr do Sol", "Noturno"])
    style = st.selectbox("ESTILO", ["Fotorrealista", "Artístico", "Maquete"])
    fstop = st.select_slider("ABERTURA", options=["f/1.8", "f/2.8", "f/8.0"], value="f/8.0")
    st.divider()
    usd_brl = get_usd_brl()
    st.caption(f"Câmbio: R$ {usd_brl:.2f} | Custo: R$ {(0.06 * usd_brl):.2f}")

# ─── MAIN ───
st.markdown("# AI ArchViz Studio")
tab_studio, tab_gallery = st.tabs([" STUDIO ", " GALERIA "])

with tab_studio:
    c1, c2 = st.columns(2)
    with c1:
        upload = st.file_uploader("Upload Print 3D", type=["png", "jpg", "jpeg"])
        if upload: st.image(upload, use_container_width=True)
    with c2:
        notes = st.text_area("Materiais e Notas", placeholder="Ex: Deck de madeira, concreto aparente...")
        btn = st.button("⬡ GERAR RENDER 3 PRO")

    if btn and upload and api_key:
        with st.spinner("Renderizando com Gemini 3 Pro..."):
            try:
                client = genai.Client(api_key=api_key)
                # TENTA O 3 PRO, SE DER 404 ELE AVISA
                response = client.models.generate_content(
                    model="gemini-3-pro-image-preview",
                    contents=[build_prompt(lighting, style, notes, fstop), Image.open(upload)],
                    config=types.GenerateContentConfig(temperature=0.4, response_modalities=["IMAGE"])
                )
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        img_data = part.inline_data.data
                        st.session_state["o"] = base64.b64encode(upload.getvalue()).decode()
                        st.session_state["r"] = base64.b64encode(img_data).decode()
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}. Se for 404, mude para 'gemini-1.5-pro' no código.")

    if "r" in st.session_state:
        st.divider()
        html = compare_slider_html(st.session_state["o"], st.session_state["r"])
        components.html(html, height=550)
