import streamlit as st
import requests
from supabase import create_client, Client

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
                minutas = resposta.data

            if minutas:
                for item in minutas:
                    st.image(item["url_foto"], caption=f"Minuta referente à NF-e: {nf}")
                    
                    # Baixar a imagem da internet para permitir download
                    img_bytes = requests.get(item["url_foto"]).content
                    st.download_button(
                        label="Baixar Minuta",
                        data=img_bytes,
                        file_name=f"C{item['carregamento']}_NF{item['nf']}.png",
                        mime="image/png",
                        key=f"down_{item['id']}"
                    )

                    # Botão de Deletar no Supabase
                    if st.button("Deletar Minuta", key=f"del_{item['id']}"):
                        supabase.table("minutas").delete().eq("id", item["id"]).execute()
                        st.success("Minuta apagada com sucesso!")
                        st.rerun()
            else:
                st.warning("Nenhuma minuta encontrada para esta NF-e ;-;.")
        else:
            st.error("Digite o número da NF-e.")

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
                st.subheader(f"Minutas econtradas no Carregamento {num_carregamento}:")
                for item in minutas:
                    st.image(item["url_foto"], caption=f"NF-e: {item['nf']} | Carregamento: {item['carregamento']}")
            else:
                st.warning("Nenhuma minuta encontrada para este carregamento ._.")
        else:
            st.error("Digite o número do carregamento.")

# --- CADASTRAR MINUTAS ---
elif opcao == "Cadastrar Minutas":
    st.title("Cadastro de Novas Minutas")
    carregamento = st.text_input("Digite o número do Carregamento:") 
    nf_cadastro = st.text_input("Digite o número da Nf-e:")
    foto = st.file_uploader("Selecione a foto da minuta assinada:", type=["png", "jpg", "jpeg"])

    if foto:
        st.image(foto, caption="Prévia da minuta selecionada", width=300)

    if st.button("Salvar Minuta"):
        if carregamento and nf_cadastro and foto:
            with st.spinner("Salving minuta na nuvem..."):
                # 1. Envia foto para o ImgBB
                payload = {"key": st.secrets["IMGBB_API_KEY"]}
                files = {"image": foto.getvalue()}
                res = requests.post("https://api.imgbb.com/1/upload", data=payload, files=files)

                if res.status_code == 200:
                    url_foto = res.json()["data"]["url"]

                    # 2. Salva registro no Supabase
                    dados = {
                        "carregamento": str(carregamento).strip(),
                        "nf": str(nf_cadastro).strip(),
                        "url_foto": url_foto
                    }
                    supabase.table("minutas").insert(dados).execute()

                    st.success(f"Minuta salva com sucesso, fi! (NF: {nf_cadastro} | Carregamento: {carregamento})")
                else:
                    st.error("Erro ao subir a foto. Verifique a chave do ImgBB.")
        else:
            st.error("Preencha todos os campos e selecione uma imagem para salvar!")