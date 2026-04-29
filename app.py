import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
from datetime import datetime
import requests

# ─── CÂMBIO USD → BRL (API Banco Central / fallback) ───
@st.cache_data(ttl=3600)
def get_usd_brl() -> float:
    try:
        r = requests.get("https://economia.awesomeapi.com.br/json/last/USD-BRL", timeout=5)
        data = r.json()
        return float(data["USDBRL"]["bid"])
    except Exception:
        return 5.00

def fmt_brl(usd_value: float, rate: float) -> str:
    brl = usd_value * rate
    return f"R$ {brl:.2f}"

st.set_page_config(
    page_title="AI ArchViz Studio",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Cormorant+Garamond:wght@300;400;600&family=Space+Grotesk:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stApp {
    background-color: #0d0f14;
    background-image: linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
    background-size: 40px 40px;
    color: #e8e4dc;
}
[data-testid="stSidebar"] { background-color: #111318; border-right: 1px solid rgba(200,180,120,0.2); }
h1 { font-family: 'Cormorant Garamond', serif !important; font-weight: 300 !important; font-size: 2.8rem !important; color: #e8e4dc !important; border-bottom: 1px solid rgba(200,180,120,0.3); padding-bottom: 0.5rem; }
h2, h3 { font-family: 'DM Mono', monospace !important; color: #c8b478 !important; font-size: 0.8rem !important; letter-spacing: 0.2em !important; text-transform: uppercase !important; }
.stButton > button { background: linear-gradient(135deg, #c8b478 0%, #a8944e 100%) !important; color: #0d0f14 !important; border-radius: 2px !important; font-family: 'DM Mono', monospace !important; width: 100% !important; }
.render-meta { font-family: 'DM Mono', monospace; font-size: 0.7rem; color: rgba(200,180,120,0.6); }
</style>
""", unsafe_allow_html=True)

# ─── COMPARE SLIDER COMPONENT ───
def compare_slider_html(b64_before: str, b64_after: str, height: int = 500) -> str:
    return f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #0d0f14; display: flex; flex-direction: column; align-items: center; font-family: 'DM Mono', monospace; overflow: hidden; }}
.compare-wrap {{ position: relative; width: 100%; height: {height}px; overflow: hidden; cursor: col-resize; border: 1px solid rgba(200,180,120,0.2); border-radius: 4px; }}
.compare-wrap img {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; background: #111318; pointer-events: none; }}
.img-after {{ z-index: 1; }} .img-before {{ z-index: 2; clip-path: inset(0 50% 0 0); }}
.divider {{ position: absolute; top: 0; bottom: 0; left: 50%; width: 2px; background: #c8b478; z-index: 10; transform: translateX(-50%); }}
.handle {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 40px; height: 40px; border-radius: 50%; background: #c8b478; display: flex; align-items: center; justify-content: center; z-index: 11; }}
.label {{ position: absolute; bottom: 10px; z-index: 12; font-size: 10px; padding: 4px 8px; background: rgba(0,0,0,0.7); color: #fff; }}
.label-before {{ left: 10px; }} .label-after {{ right: 10px; color: #c8b478; }}
</style></head><body>
<div class="compare-wrap" id="compare">
    <img class="img-after" src="data:image/png;base64,{b64_after}" />
    <img id="imgBefore" class="img-before" src="data:image/png;base64,{b64_before}" />
    <div class="divider" id="divider"><div class="handle"><></div></div>
    <span class="label label-before">MODELO 3D</span><span class="label label-after">RENDER IA</span>
</div>
<script>
    const wrap = document.getElementById('compare'); const divider = document.getElementById('divider'); const before = document.getElementById('imgBefore');
    function setPos(x) {{
        let rect = wrap.getBoundingClientRect(); let pct = (x - rect.left) / rect.width;
        pct = Math.min(Math.max(pct, 0), 1);
        divider.style.left = (pct * 100) + '%';
        before.style.clipPath = `inset(0 ${{(100 - pct * 100)}}% 0 0)`;
    }}
    wrap.addEventListener('mousemove', e => {{ if(e.buttons==1) setPos(e.clientX); }});
    wrap.addEventListener('touchstart', e => setPos(e.touches[0].clientX));
</script></body></html>"""

# ─── HELPERS ───
def image_to_b64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def img_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ─── SYSTEM PROMPT (CORRIGIDO) ───
def build_prompt(lighting: str, style: str, extra: str, fstop: str) -> str:
    return f"""ÂNCORA ABSOLUTA — MODO ARCHVIZ FOTORREALISTA PROFISSIONAL

Você é um motor de renderização de elite. A imagem fornecida é a sua GEOMETRIA DE REFERÊNCIA.

TAREFA: Transformar o modelo 3D em uma fotografia de arquitetura realista.

REGRAS CRÍTICAS:
1. GEOMETRIA (LOCK): Mantenha 100% da posição de paredes, janelas e volumes. Não invente aberturas.
2. MATERIAIS PBR (REALISMO): Substitua as cores chapadas do modelo por texturas fotorrealistas. 
   - Se a superfície é cinza -> converta em concreto aparente real com granulação.
   - Se é branco -> converta em gesso ou alvenaria com leve textura de pintura.
   - Se é amadeirado -> aplique veios de madeira real com brilho (glossiness) correto.
   - Vidros devem ter reflexos reais do ambiente.
3. CÂMERA: Sony A7R V, lente 35mm. Abertura em {fstop} para profundidade de campo profissional.
4. ILUMINAÇÃO: {lighting}. Aplique luz fisicamente correta com Global Illumination.
5. ESTILO: {style}. Foque em realismo de revista de arquitetura de luxo.

NOTAS DO PROJETO: {extra}

Gere o render final baseado nestas instruções rígidas."""

# ─── SIDEBAR ───
with st.sidebar:
    st.markdown("## ⬡ API")
    api_key = st.text_input("GEMINI API KEY", type="password")
    
    st.divider()
    st.markdown("## ⬡ Parâmetros")
    lighting = st.selectbox("ILUMINAÇÃO", ["Golden Hour", "Dia Claro", "Pôr do Sol", "Overcast", "Estúdio"])
    style    = st.selectbox("ESTILO", ["Fotorrealista", "Artístico", "Linha+Render"])
    ratio    = st.selectbox("PROPORÇÃO", ["16:9", "4:3", "1:1", "3:2", "9:16"])
    fstop    = st.select_slider("ABERTURA (f-stop)", options=["f/1.8", "f/2.8", "f/4.0", "f/5.6", "f/8.0", "f/11"], value="f/8.0")

    st.divider()
    usd_brl = get_usd_brl()
    st.markdown(f"**Custo por render:** R$ {0.039 * usd_brl:.2f}")

# ─── STUDIO ───
st.markdown("# AI ArchViz Studio")
tab_studio, tab_gallery = st.tabs(["STUDIO", "GALERIA"])

with tab_studio:
    c_left, c_right = st.columns(2)
    with c_left:
        upload = st.file_uploader("Upload do Print 3D", type=["png", "jpg", "jpeg"])
        if upload:
            orig = Image.open(upload)
            st.image(orig, caption="Original", use_container_width=True)

    with c_right:
        notes = st.text_area("Notas do Projeto", placeholder="Ex: Piso em madeira carvalho, paredes em concreto...")
        btn = st.button("⬡ GERAR RENDER", disabled=not (upload and api_key))

    if btn:
        with st.spinner("Renderizando com texturas PBR..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt = build_prompt(lighting, style, notes, fstop)
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp", # Usando a versão mais atualizada para geração
                    contents=[prompt, Image.open(upload)],
                    config=types.GenerateContentConfig(
                        temperature=0.4, # Aumentado para dar "coragem" à IA nas texturas
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio=ratio),
                    ),
                )
                
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        rendered = Image.open(BytesIO(part.inline_data.data))
                        st.session_state["last_orig"] = image_to_b64(Image.open(upload))
                        st.session_state["last_rend"] = image_to_b64(rendered)
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    if "last_rend" in st.session_state:
        st.divider()
        html_code = compare_slider_html(st.session_state["last_orig"], st.session_state["last_rend"])
        components.html(html_code, height=550)
        st.download_button("BAIXAR RENDER", data=base64.b64decode(st.session_state["last_rend"]), file_name="render.png")
