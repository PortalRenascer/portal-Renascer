import os
import streamlit as st
import requests
from supabase import create_client, Client

st.set_page_config(
    page_title="Portal Renascer",
    page_icon="logo.png",
    layout="wide"
)
st.markdown("""
    <style>
    @media (max-width: 768px) {
        [data-testid="stSidebar"] img {
            max-width: 100px !important;
            margin: 0 auto;
        }
    }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("logo.png"):
    col1, col2, col3 = st.sidebar.columns([1, 2, 1])
    with col2:
        st.image("logo.png", use_container_width=True)
else:
    st.sidebar.title("Portal Renascer")

# Conexão com Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

opcao = st.sidebar.selectbox("Escolha a página", ["Consultar por NF-e", "Consultar por Carregamento", "Cadastrar Minutas"])

# --- CONSULTAR POR NF-E ---
if opcao == "Consultar por NF-e":
    st.title("Consultar por NF-e")
    nf = st.text_input("Digite o número da NF-e")
    
    if st.button("Buscar Minuta"): 
        if nf: 
            with st.spinner("Buscando..."):
                resposta = supabase.table("minutas").select("*").eq("nf", str(nf).strip()).execute()
                st.session_state["minutas_encontradas"] = resposta.data
        else:
            st.error("Digite o número da NF-e.")

    if "minutas_encontradas" in st.session_state and st.session_state["minutas_encontradas"]:
        minutas = st.session_state["minutas_encontradas"]
        
        for item in minutas:
            url_foto = item.get("foto_url") or item.get("url_foto")
            minuta_id = item["id"]

            st.caption(f"Minuta referente à NF-e: {item['nf']}")
            
            # Componente interativo de visualização com Zoom e Rotação
            html_visualizador = f"""
            <div style="border: 1px solid #444; padding: 10px; border-radius: 8px; background: #1e1e1e; text-align: center;">
                <div style="margin-bottom: 10px;">
                    <button onclick="girar_{minuta_id}()" style="padding: 6px 12px; margin-right: 5px; cursor: pointer;">🔄 Girar 90°</button>
                    <button onclick="zoomIn_{minuta_id}()" style="padding: 6px 12px; margin-right: 5px; cursor: pointer;">🔍 + Zoom</button>
                    <button onclick="zoomOut_{minuta_id}()" style="padding: 6px 12px; margin-right: 5px; cursor: pointer;">🔍 - Zoom</button>
                    <button onclick="reset_{minuta_id}()" style="padding: 6px 12px; cursor: pointer;">↩️ Resetar</button>
                </div>
                <div style="overflow: auto; max-height: 700px; display: flex; justify-content: center; align-items: center; background: #0e0e0e; border-radius: 5px;">
                    <img id="img_{minuta_id}" src="{url_foto}" style="max-width: 100%; transition: transform 0.2s ease; transform-origin: center center;">
                </div>
            </div>

            <script>
                let angulo_{minuta_id} = 0;
                let escala_{minuta_id} = 1;

                function atualizar_{minuta_id}() {{
                    let img = document.getElementById('img_{minuta_id}');
                    img.style.transform = 'rotate(' + angulo_{minuta_id} + 'deg) scale(' + escala_{minuta_id} + ')';
                }}

                function girar_{minuta_id}() {{
                    angulo_{minuta_id} = (angulo_{minuta_id} + 90) % 360;
                    atualizar_{minuta_id}();
                }}

                function zoomIn_{minuta_id}() {{
                    escala_{minuta_id} += 0.25;
                    atualizar_{minuta_id}();
                }}

                function zoomOut_{minuta_id}() {{
                    if (escala_{minuta_id} > 0.5) {{
                        escala_{minuta_id} -= 0.25;
                        atualizar_{minuta_id}();
                    }}
                }}

                function reset_{minuta_id}() {{
                    angulo_{minuta_id} = 0;
                    escala_{minuta_id} = 1;
                    atualizar_{minuta_id}();
                }}
            </script>
            """
            
            st.components.v1.html(html_visualizador, height=750, scrolling=True)

            # Botão para baixar a imagem
            if url_foto:
                try:
                    res_img = requests.get(url_foto, timeout=5)
                    if res_img.status_code == 200:
                        st.download_button(
                            label="Baixar Minuta Original",
                            data=res_img.content,
                            file_name=f"C{item.get('carregamento', '')}_NF{item['nf']}.png",
                            mime="image/png",
                            key=f"down_{minuta_id}"
                        )
                except Exception:
                    st.warning("Não foi possível carregar a imagem para download.")

            # Botão de Deletar
            if st.button("Deletar Minuta", key=f"del_{minuta_id}"):
                supabase.table("minutas").delete().eq("id", minuta_id).execute()
                st.success("Minuta apagada com sucesso!")
                del st.session_state["minutas_encontradas"]
                st.rerun()

# --- CADASTRAR MINUTAS ---
elif opcao == "Cadastrar Minutas":
    st.title("Cadastro de Novas Minutas")

    # Formulário com limpeza automática ao enviar
    with st.form(key="form_minuta", clear_on_submit=True):
        carregamento = st.text_input("Digite o número do Carregamento:")
        nf_cadastro = st.text_input("Digite o número da Nf-e:")
        foto = st.file_uploader("Selecione a foto da minuta assinada:", type=["png", "jpg", "jpeg"])
        
        botao_salvar = st.form_submit_button("Salvar Minuta")

    if botao_salvar:
        if carregamento and nf_cadastro and foto:
            nf_limpa = str(nf_cadastro).strip()

            # Checa no Supabase se a NF-e já foi cadastrada antes
            checa_existente = supabase.table("minutas").select("nf").eq("nf", nf_limpa).execute()

            if checa_existente.data:
                st.error(f"⚠️ A NF-e **{nf_limpa}** já está cadastrada no sistema! Cadastro duplicado cancelado.")
            else:
                with st.spinner("Salvando minuta na nuvem..."):
                    payload = {
                        "key": st.secrets["IMGBB_API_KEY"],
                        "expiration": 0
                    }
                    files = {"image": foto.getvalue()}
                    res = requests.post("https://api.imgbb.com/1/upload", data=payload, files=files)
                    
                    if res.status_code == 200:
                        dados_resposta = res.json()["data"]
                        url_foto = dados_resposta.get("display_url", dados_resposta.get("url"))

                        dados = {
                            "carregamento": str(carregamento).strip(),
                            "nf": nf_limpa,
                            "url_foto": url_foto
                        }

                        try:
                            supabase.table("minutas").insert(dados).execute()
                            st.success("✅ Minuta cadastrada com sucesso!")
                        except Exception as e:
                            st.error(f"Erro do Supabase: {e}")
                    else:
                        st.error("Erro ao enviar a imagem. Tente novamente.")
        else:
            st.warning("⚠️ Preencha todos os campos e selecione uma foto antes de salvar.")