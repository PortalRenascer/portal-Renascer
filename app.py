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
            st.image(url_foto, caption=f"Minuta referente à NF-e: {item['nf']}")

            # Baixar a imagem para o botão de download
            if url_foto:
                st.markdown(f"🔍[**Abrir imagem em tamanho real (com zoom)**]({url_foto})")
                try:
                    res_img = requests.get(url_foto, timeout=5)
                    if res_img.status_code == 200:
                        st.download_button(
                            label="Baixar Minuta",
                            data=res_img.content,
                            file_name=f"C{item.get('carregamento', '')}_NF{item['nf']}.png",
                            mime="image/png",
                            key=f"down_{item['id']}"
                        )
                except Exception:
                    st.warning("Não foi possível carregar a imagem para download.")

            # Botão de Deletar no Supabase
            if st.button("Deletar Minuta", key=f"del_{item['id']}"):
                supabase.table("minutas").delete().eq("id", item["id"]).execute()
                st.success("Minuta apagada com sucesso!")
                del st.session_state["minutas_encontradas"]
                st.rerun()

    elif "minutas_encontradas" in st.session_state and not st.session_state["minutas_encontradas"]:
        st.warning("Nenhuma minuta encontrada para esta NF-e ;-;")

# --- CONSULTAR POR CARREGAMENTO ---
elif opcao == "Consultar por Carregamento":
    st.title("Consultar por Carregamento")
    num_carregamento = st.text_input("Digite o número do Carregamento:")
    
    if st.button("Buscar Carregamento"): 
        if num_carregamento:
            with st.spinner("Buscando..."):
                resposta = supabase.table("minutas").select("*").eq("carregamento", str(num_carregamento).strip()).execute()
                minutas = resposta.data

            if minutas:
                st.subheader(f"Minutas encontradas no Carregamento {num_carregamento}:")
                for item in minutas:
                    url_foto = item.get("foto_url") or item.get("url_foto")
                    st.image(url_foto, caption=f"NF-e: {item['nf']} | Carregamento: {item['carregamento']}")
            else:
                st.warning("Nenhuma minuta encontrada para este carregamento ._.")
        else:
            st.error("Digite o número do carregamento.")

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
                            "foto_url": url_foto
                        }
                        supabase.table("minutas").insert(dados).execute()
                        st.success("✅ Minuta cadastrada com sucesso! Os campos foram limpos para o próximo cadastro.")
                    else:
                        st.error("Erro ao enviar a imagem. Tente novamente.")
        else:
            st.warning("⚠️ Preencha todos os campos e selecione uma foto antes de salvar.")