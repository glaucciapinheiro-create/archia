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
@st.cache_data(ttl=3600)  # Atualiza a cada 1 hora
def get_usd_brl() -> float:
    try:
        # API gratuita do Banco Central do Brasil (sem autenticação)
        r = requests.get(
            "https://economia.awesomeapi.com.br/json/last/USD-BRL",
            timeout=5
        )
        data = r.json()
        return float(data["USDBRL"]["bid"])
    except Exception:
        return 5.00  # fallback se a API estiver fora

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
    background-image:
        linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
    background-size: 40px 40px;
    color: #e8e4dc;
}
[data-testid="stSidebar"] {
    background-color: #111318;
    border-right: 1px solid rgba(200,180,120,0.2);
}
h1 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 300 !important;
    font-size: 2.8rem !important;
    letter-spacing: 0.05em !important;
    color: #e8e4dc !important;
    border-bottom: 1px solid rgba(200,180,120,0.3);
    padding-bottom: 0.5rem;
}
h2, h3 {
    font-family: 'DM Mono', monospace !important;
    color: #c8b478 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    font-weight: 400 !important;
}
.subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: rgba(200,180,120,0.6);
    letter-spacing: 0.3em;
    text-transform: uppercase;
    margin-bottom: 2.5rem;
}
.stTextInput input, .stTextArea textarea {
    background-color: #1a1d24 !important;
    border: 1px solid rgba(200,180,120,0.25) !important;
    border-radius: 2px !important;
    color: #e8e4dc !important;
    font-family: 'DM Mono', monospace !important;
}
.stSelectbox > div > div {
    background-color: #1a1d24 !important;
    border: 1px solid rgba(200,180,120,0.25) !important;
    border-radius: 2px !important;
    color: #e8e4dc !important;
}
.stButton > button {
    background: linear-gradient(135deg, #c8b478 0%, #a8944e 100%) !important;
    color: #0d0f14 !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 2rem !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(200,180,120,0.3) !important;
}
.render-meta {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: rgba(200,180,120,0.6);
    letter-spacing: 0.1em;
    margin-top: 0.5rem;
}
.status-badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 0.2rem 0.6rem;
    border-radius: 2px;
    background: rgba(200,180,120,0.15);
    color: #c8b478;
    border: 1px solid rgba(200,180,120,0.3);
    margin-bottom: 1rem;
}
hr { border-color: rgba(200,180,120,0.15) !important; margin: 2rem 0 !important; }
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(200,180,120,0.2) !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: rgba(232,228,220,0.5) !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.6rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
    color: #c8b478 !important;
    border-bottom: 2px solid #c8b478 !important;
}
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0d0f14; }
::-webkit-scrollbar-thumb { background: rgba(200,180,120,0.3); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


# ─── COMPARE SLIDER COMPONENT ───
def compare_slider_html(b64_before: str, b64_after: str, height: int = 500) -> str:
    """
    Retorna HTML completo do slider antes/depois.
    b64_before = modelo 3D (esquerda)
    b64_after  = render IA (direita)
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #0d0f14;
    display: flex;
    flex-direction: column;
    align-items: center;
    font-family: 'DM Mono', monospace;
    padding: 0;
    overflow: hidden;
  }}

  .compare-wrap {{
    position: relative;
    width: 100%;
    height: {height}px;
    overflow: hidden;
    cursor: col-resize;
    user-select: none;
    -webkit-user-select: none;
    border: 1px solid rgba(200,180,120,0.2);
    border-radius: 4px;
  }}

  .compare-wrap img {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    object-fit: contain;
    background: #111318;
    display: block;
    pointer-events: none;
  }}

  .img-after  {{ z-index: 1; }}
  .img-before {{ z-index: 2; clip-path: inset(0 50% 0 0); }}

  .divider {{
    position: absolute;
    top: 0; bottom: 0;
    left: 50%;
    width: 2px;
    background: #c8b478;
    z-index: 10;
    transform: translateX(-50%);
  }}

  .handle {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #c8b478;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 20px rgba(0,0,0,0.6);
    z-index: 11;
    cursor: col-resize;
    animation: pulse 2s ease-in-out 0.5s 3;
  }}

  @keyframes pulse {{
    0%, 100% {{ box-shadow: 0 2px 20px rgba(0,0,0,0.6), 0 0 0 0 rgba(200,180,120,0.5); }}
    50%       {{ box-shadow: 0 2px 20px rgba(0,0,0,0.6), 0 0 0 10px rgba(200,180,120,0); }}
  }}

  .label {{
    position: absolute;
    bottom: 14px;
    z-index: 12;
    font-size: 9px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 2px;
    pointer-events: none;
    font-family: monospace;
  }}
  .label-before {{
    left: 14px;
    background: rgba(13,15,20,0.8);
    color: rgba(232,228,220,0.9);
    border: 1px solid rgba(200,180,120,0.3);
  }}
  .label-after {{
    right: 14px;
    background: rgba(200,180,120,0.15);
    color: #c8b478;
    border: 1px solid rgba(200,180,120,0.5);
  }}

  .hint {{
    margin-top: 10px;
    font-size: 9px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(200,180,120,0.35);
    font-family: monospace;
    text-align: center;
  }}
</style>
</head>
<body>

<div class="compare-wrap" id="compare">
  <img class="img-after"  src="data:image/png;base64,{b64_after}"  alt="Render IA" />
  <img class="img-before" id="imgBefore" src="data:image/png;base64,{b64_before}" alt="Modelo 3D" />

  <div class="divider" id="divider">
    <div class="handle" id="handle">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
           stroke="#0d0f14" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="15 18 9 12 15 6"></polyline>
        <polyline points="9 18 3 12 9 6" transform="translate(12,0)"></polyline>
      </svg>
    </div>
  </div>

  <span class="label label-before">◀ Modelo 3D</span>
  <span class="label label-after">Render IA ▶</span>
</div>

<p class="hint">← arraste o divisor para comparar →</p>

<script>
  const wrap    = document.getElementById('compare');
  const divider = document.getElementById('divider');
  const handle  = document.getElementById('handle');
  const before  = document.getElementById('imgBefore');
  let dragging  = false;

  function setPos(clientX) {{
    const rect = wrap.getBoundingClientRect();
    let pct = (clientX - rect.left) / rect.width;
    pct = Math.min(Math.max(pct, 0.02), 0.98);
    const p = (pct * 100).toFixed(2);
    divider.style.left = p + '%';
    before.style.clipPath = `inset(0 ${{(100 - pct * 100).toFixed(2)}}% 0 0)`;
  }}

  wrap.addEventListener('mousedown',  e => {{ dragging = true; setPos(e.clientX); }});
  window.addEventListener('mousemove',e => {{ if (dragging) setPos(e.clientX); }});
  window.addEventListener('mouseup',  () => {{ dragging = false; }});
  wrap.addEventListener('click',      e => setPos(e.clientX));

  wrap.addEventListener('touchstart', e => {{ dragging = true; setPos(e.touches[0].clientX); }}, {{passive:true}});
  window.addEventListener('touchmove',e => {{ if (dragging) setPos(e.touches[0].clientX); }}, {{passive:true}});
  window.addEventListener('touchend', () => {{ dragging = false; }});
</script>
</body>
</html>
"""


# ─── HELPERS ───
def image_to_b64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def img_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def save_gallery(original, rendered, meta):
    if "gallery" not in st.session_state:
        st.session_state.gallery = []
    st.session_state.gallery.insert(0, {
        "original": image_to_b64(original),
        "rendered": image_to_b64(rendered),
        "meta": meta,
        "ts": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })


# ─── SYSTEM PROMPT ───
def build_prompt(lighting: str, style: str, extra: str) -> str:
    lighting_map = {
        "Golden Hour": "Sol rasante 10-15° acima do horizonte, temperatura 3200K, sombras longas e douradas, céu alaranjado.",
        "Dia Claro":   "Sol alto difuso, temperatura 6500K, HDRI céu nublado claro, sombras suaves.",
        "Pôr do Sol":  "Céu laranja-violeta, reflexos quentes em superfícies envidraçadas, temperatura 2800K.",
        "Overcast":    "Cobertura total de nuvens, luz difusa omnidirecional, temperatura 7000K, sem sombras duras.",
        "Estúdio":     "Três pontos de luz neutros (key, fill, rim), temperatura 5500K, ambiente controlado.",
    }
    style_map = {
        "Fotorrealista": "Ray tracing completo com Global Illumination, reflexos PBR fisicamente corretos, máxima fidelidade fotográfica.",
        "Artístico":     "Aquarela arquitetônica digital com traços suaves e paleta controlada, mantendo a geometria original.",
        "Linha+Render":  "Wireframe técnico integrado à renderização fotorrealista, estilo Zaha Hadid Office.",
    }
    return f"""ÂNCORA ABSOLUTA — MODO ARCHVIZ FOTORREALISTA

Você é um motor de render profissional. A imagem fornecida é o modelo 3D de referência.

MISSÃO: Transformar este modelo 3D em um render fotorrealista de arquitetura com FIDELIDADE GEOMÉTRICA ABSOLUTA.

REGRAS INVIOLÁVEIS:
1. GEOMETRIA: Reproduza EXATAMENTE proporções, ângulos e formas do modelo.
   PROIBIDO: adicionar janelas, portas, vegetação ou elementos ausentes no modelo.
   PROIBIDO: remover ou reposicionar elementos existentes.

2. MATERIAIS (PBR): Mantenha as cores originais como albedo base.
   PROIBIDO texturizar superfícies lisas no modelo.

3. CÂMERA: Ângulo IDÊNTICO ao da referência. Full frame 35mm, f/8, ISO 100, Tilt-shift vertical.

4. ILUMINAÇÃO: {lighting_map.get(lighting, lighting)}

5. ESTILO: {style_map.get(style, style)}

6. ZERO ALUCINAÇÃO: Superfícies ambíguas → concreto aparente ou gesso branco neutro.

{f"NOTAS DO PROJECTO: {extra}" if extra.strip() else ""}

Gere o render fotorrealista final da imagem de arquitetura fornecida."""


# ─── SIDEBAR ───
with st.sidebar:
    st.markdown("## ⬡ API")
    api_key = st.text_input("GEMINI API KEY", type="password", placeholder="AIza...",
                            help="Obtenha em aistudio.google.com")

    if api_key:
        st.markdown('<div class="status-badge">✓ API KEY CONFIGURADA</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge" style="color:rgba(232,100,80,0.8);border-color:rgba(232,100,80,0.3);">✗ AGUARDANDO API KEY</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("## ⬡ Parâmetros")

    lighting = st.selectbox("ILUMINAÇÃO", ["Golden Hour", "Dia Claro", "Pôr do Sol", "Overcast", "Estúdio"])
    style    = st.selectbox("ESTILO", ["Fotorrealista", "Artístico", "Linha+Render"])
    ratio    = st.selectbox("PROPORÇÃO", ["16:9", "4:3", "1:1", "3:2", "9:16"])

    st.divider()
    usd_brl = get_usd_brl()
    custo_usd = 0.039
    custo_brl = custo_usd * usd_brl

    st.markdown(f"""
    <div class="render-meta">
    Modelo: <strong style="color:#c8b478">gemini-2.5-flash-image</strong><br><br>
    Custo por render:<br>
    <strong style="color:#c8b478;font-size:1.1em;">$ {custo_usd:.3f} USD</strong><br>
    <strong style="color:#c8b478;font-size:1.1em;">R$ {custo_brl:.2f}</strong><br><br>
    <span style="color:rgba(200,180,120,0.4);font-size:0.85em;">
    Câmbio: 1 USD = R$ {usd_brl:.2f}<br>
    Atualizado a cada hora
    </span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.caption("AI ArchViz Studio · v2.1 · BYOK")


# ─── HEADER ───
st.markdown("# AI ArchViz Studio")
st.markdown('<div class="subtitle">Render fotorrealista via Gemini 2.5 Flash Image</div>', unsafe_allow_html=True)

tab_studio, tab_gallery, tab_guide = st.tabs(["  STUDIO  ", "  GALERIA  ", "  GUIA  "])


# ─── STUDIO ───
with tab_studio:
    c_left, c_right = st.columns([1, 1], gap="large")

    with c_left:
        st.markdown("### Upload do Modelo 3D")
        upload = st.file_uploader("Print do SketchUp / Blender / Revit",
                                  type=["png", "jpg", "jpeg", "webp"],
                                  label_visibility="collapsed")
        if upload:
            orig = Image.open(upload)
            st.image(orig, caption=upload.name, use_container_width=True)
            st.markdown(f'<div class="render-meta">📐 {orig.width}×{orig.height}px</div>', unsafe_allow_html=True)

    with c_right:
        st.markdown("### Notas do Projecto")
        notes = st.text_area("Notas", placeholder="Ex: Fachada em tijolo aparente. Edifício residencial.",
                             height=100, label_visibility="collapsed")
        st.markdown("<br>", unsafe_allow_html=True)
        btn = st.button("⬡ GERAR RENDER", disabled=not (upload and api_key))

        if not api_key:
            st.info("Configure sua API Key na barra lateral.")
        elif not upload:
            st.info("Faça upload de um print 3D para continuar.")

    # ─── GERAÇÃO ───
    if btn and upload and api_key:
        prompt = build_prompt(lighting, style, notes)
        orig   = Image.open(upload)

        with st.spinner("Gerando render... aguarde (~10-30 segundos)"):
            try:
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[prompt, orig],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio=ratio),
                    ),
                )

                rendered = None
                for part in response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        rendered = Image.open(BytesIO(part.inline_data.data))
                        break

                if rendered:
                    # Guardar na session para o slider persistir
                    st.session_state["last_original"] = image_to_b64(orig)
                    st.session_state["last_rendered"]  = image_to_b64(rendered)
                    save_gallery(orig, rendered, {"lighting": lighting, "style": style, "ratio": ratio})
                else:
                    st.warning("A API respondeu mas sem imagem. Tente novamente.")

            except Exception as e:
                st.error(f"Erro: {e}")
                st.info("Verifique se a API Key tem créditos e se o modelo `gemini-2.5-flash-image` está disponível em aistudio.google.com")

    # ─── SLIDER COMPARAÇÃO (persiste mesmo após rerun) ───
    if st.session_state.get("last_original") and st.session_state.get("last_rendered"):
        st.success("✓ Render gerado com sucesso!")
        st.divider()
        st.markdown("### Comparação — Antes / Depois")
        st.markdown('<div class="render-meta">Arraste o divisor dourado para comparar o modelo 3D com o render IA</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        html_code = compare_slider_html(
            b64_before=st.session_state["last_original"],
            b64_after=st.session_state["last_rendered"],
            height=520,
        )
        components.html(html_code, height=560, scrolling=False)

        # Download
        rendered_dl = Image.open(BytesIO(base64.b64decode(st.session_state["last_rendered"])))
        st.download_button(
            "↓ BAIXAR RENDER (PNG)",
            data=img_bytes(rendered_dl),
            file_name=f"archviz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png",
        )


# ─── GALERIA ───
with tab_gallery:
    ct, cc = st.columns([4, 1])
    with ct:
        st.markdown("### Histórico")
        n = len(st.session_state.get("gallery", []))
        st.markdown(f'<div class="render-meta">{n} render(s) nesta sessão</div>', unsafe_allow_html=True)
    with cc:
        if st.button("LIMPAR") and st.session_state.get("gallery"):
            st.session_state.gallery = []
            st.rerun()

    gallery = st.session_state.get("gallery", [])

    if not gallery:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:rgba(200,180,120,0.3);">
            <div style="font-family:'Cormorant Garamond',serif;font-size:1.5rem;">Nenhum render ainda</div>
            <div style="font-family:'DM Mono',monospace;font-size:0.7rem;letter-spacing:0.2em;text-transform:uppercase;margin-top:0.5rem;">
                Gere seu primeiro render no Studio
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, item in enumerate(gallery):
            m = item["meta"]
            st.markdown(f'<div class="render-meta">◆ Render #{len(gallery)-i:03d} · {item["ts"]} · 💡 {m["lighting"]} · 🎨 {m["style"]}</div>', unsafe_allow_html=True)

            # Slider de comparação para cada item da galeria
            html_code = compare_slider_html(
                b64_before=item["original"],
                b64_after=item["rendered"],
                height=400,
            )
            components.html(html_code, height=440, scrolling=False)

            rnd = Image.open(BytesIO(base64.b64decode(item["rendered"])))
            st.download_button(
                f"↓ BAIXAR RENDER #{len(gallery)-i:03d}",
                data=img_bytes(rnd),
                file_name=f"archviz_{i+1:03d}.png",
                mime="image/png",
                key=f"dl_{i}",
            )
            st.divider()


# ─── GUIA ───
with tab_guide:
    st.markdown("### Como Usar")
    st.markdown("""
**1. Obter a API Key**
Acesse [aistudio.google.com](https://aistudio.google.com) → Get API Key → carregue créditos em Billing.

**2. Preparar o Print 3D**
Exporte direto do SketchUp, Blender ou Revit. PNG sem compressão, mínimo 1280px.

**3. Configurar e Gerar**
Escolha iluminação, estilo e proporção → clique em Gerar Render → aguarde ~10-30 segundos.

**4. Comparar**
Use o **controle deslizante dourado** para comparar o modelo 3D original com o render gerado.

**5. Baixar**
A imagem gerada é um render fotorrealista real, pronto para apresentações e portfólio.
    """)
    st.divider()
    st.markdown("### Custos Estimados (2026)")
    usd_brl_guide = get_usd_brl()
    custo_render_brl = 0.039 * usd_brl_guide
    renders_por_60 = int(60 / custo_render_brl)
    st.markdown(f"""
| Modelo | USD | BRL (hoje) |
|--------|-----|-----------|
| `gemini-2.5-flash-image` | $0.039 | R$ {custo_render_brl:.2f} |

Câmbio atual: **1 USD = R$ {usd_brl_guide:.2f}** · R$ 60,00/mês ≈ **{renders_por_60} renders**.
    """)
    st.divider()
    st.markdown("### Iluminações")
    st.markdown("""
- **Golden Hour** → Residencial, luz quente e dramática
- **Dia Claro** → Comercial, foco em detalhes construtivos
- **Pôr do Sol** → Impacto visual máximo para marketing
- **Overcast** → Brutalismo, concreto aparente, arquitetura nórdica
- **Estúdio** → Interiores e museus
    """)
