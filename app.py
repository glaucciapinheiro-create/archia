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

# ─── CSS (DARK THEME + LETRAS CLARAS + LIMPEZA) ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Cormorant+Garamond:wght@300;400;600&family=Space+Grotesk:wght@300;400;500&display=swap');
    
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    html, body, [class*="css"] { 
        font-family: 'Space Grotesk', sans-serif; 
        background-color: #0d0f14; 
        color: #e8e4dc !important; 
    }

    /* Força texto claro em todos os lugares */
    label, p, span, h1, h2, h3, .stMarkdown { color: #e8e4dc !important; }
    
    [data-testid="stSidebar"] { 
        background-color: #111318; 
        border-right: 1px solid rgba(200,180,120,0.2); 
    }

    h1 { font-family: 'Cormorant Garamond', serif !important; border-bottom: 1px solid rgba(200,180,120,0.3); }
    h2, h3 { font-family: 'DM Mono', monospace !important; color: #c8b478 !important; letter-spacing: 0.15em !important; }

    .stButton > button { 
        background: linear-gradient(135deg, #c8b478 0%, #a8944e 100%) !important; 
        color: #0d0f14 !important; font-family: 'DM Mono', monospace !important; font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── COMPONENTE DO SLIDER (O RETORNO) ───
def compare_slider_html(b64_before: str, b64_after: str, height: int = 550) -> str:
    return f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #0d0f14; display: flex; justify-content: center; overflow: hidden; }}
.wrap {{ position: relative; width: 100%; height: {height}px; cursor: col-resize; border: 1px solid rgba(200,180,120,0.3); border-radius: 4px; }}
.img {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; background: #111318; }}
.before {{ z-index: 2; clip-path: inset(0 50% 0 0); }}
.divider {{ position: absolute; top: 0; bottom: 0; left: 50%; width: 2px; background: #c8b478; z-index: 10; }}
.handle {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 44px; height: 44px; border-radius: 50%; background: #c8b478; border: 3px solid #0d0f14; z-index: 11; display: flex; align-items: center; justify-content: center; }}
</style></head><body>
<div class="wrap" id="c" onmousemove="m(event)" ontouchmove="m(event.touches[0])">
    <img class="img" src="data:image/png;base64,{b64_after}">
    <img id="b" class="img before" src="data:image/png;base64,{b64_before}">
    <div id="d" class="divider"><div class="handle">⬡</div></div>
</div>
<script>
function m(e) {{
    let r = document.getElementById('c').getBoundingClientRect();
    let p = Math.max(0, Math.min(100, ((e.clientX - r.left) / r.width) * 100));
    document.getElementById('d').style.left = p + '%';
    document.getElementById('b').style.clipPath = 'inset(0 ' + (100 - p) + '% 0 0)';
}}
</script></body></html>"""

# ─── SEUS PROMPTS ───
PROMPT_EXTERNO = """[COLE SEU PROMPT EXTERNO AQUI]"""
PROMPT_INTERNO = """[COLE SEU PROMPT INTERNO AQUI]"""

def build_prompt(ambiente, lighting, style, extra, fstop):
    regra = PROMPT_EXTERNO if ambiente == "Área Externa" else PROMPT_INTERNO
    return f"{regra}\n\nPARAM: Luz={lighting}, Estilo={style}, Notas={extra}, Câmera={fstop}"

# ─── INTERFACE ───
with st.sidebar:
    st.markdown("## ⬡ CONFIG")
    api_key = st.text_input("API KEY", type="password")
    st.divider()
    ambiente = st.radio("AMBIENTE", ["Área Externa", "Área Interna"])
    lighting = st.selectbox("LUZ", ["Golden Hour", "Dia Claro", "Pôr do Sol", "Noturno"])
    fstop = st.select_slider("ABERTURA", options=["f/1.8", "f/2.8", "f/8.0"], value="f/8.0")
    st.divider()
    rate = get_usd_brl()
    st.caption(f"Custo/Render: R$ {(0.06 * rate):.2f}")

st.markdown("# AI ArchViz Studio")
c1, c2 = st.columns(2)
with c1:
    up = st.file_uploader("Upload do Print", type=["png", "jpg", "jpeg"])
    if up: st.image(up, use_container_width=True)
with c2:
    notes = st.text_area("Notas", placeholder="Descreva os materiais...", height=150)
    btn = st.button(f"GERAR RENDER {ambiente.upper()}")

if btn and up and api_key:
    with st.spinner(f"Renderizando {ambiente}..."):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=[build_prompt(ambiente, lighting, "Fotorrealista", notes, fstop), Image.open(up)],
                config=types.GenerateContentConfig(temperature=0.4, response_modalities=["IMAGE"])
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    st.session_state["o"] = base64.b64encode(up.getvalue()).decode()
                    st.session_state["r"] = base64.b64encode(part.inline_data.data).decode()
                    st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

# ─── EXIBIÇÃO DO SLIDER ───
if "r" in st.session_state:
    st.divider()
    st.markdown("### COMPARAÇÃO ANTES / DEPOIS")
    html = compare_slider_html(st.session_state["o"], st.session_state["r"])
    components.html(html, height=600)
