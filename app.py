import os
import streamlit as st 
os.makedirs("minutas_salvas", exist_ok=True)
opcao = st.sidebar.selectbox("Escolha a página", ["Consultar por NF-e", "Consultar por Carregamento", "Cadastrar Minutas"],)
if opcao == "Consultar Minuta por NF":
    st.title("Consultar por NF-e")
    nf = st.text_input("Digite o número da NF-e")
    if st.button("Buscar Minuta"): 
        if nf: 
         arquivos = os.listdir("minutas_salvas")
         minutas = [f for f in arquivos if f.endswith(f"_NF{nf}.png") or f == f"{nf}.png"]
        if minutas:
            for arq in minutas:
                caminho = os.path.join("minutas_salvas", arq)
                st.image(caminho, caption=f"Minuta referente à NF-e: {nf}")
                with open(caminho, "rb") as file:
                        st.download_button(
                            label="Baixar Minuta",
                            data=file,
                            file_name=arq,
                            mime="image/png",
                            key=f"down_{arq}"
                        )

                    # Botão de Deletar
                if st.button("Deletar Minuta", key=f"del_{arq}"):
                    os.remove(caminho)
                    st.success("Minuta apagada com sucesso!")
                    st.rerun()
        else:
             st.warning("Nenhuma minuta encontrada para esta NF-e ;-;.")
    else:
            st.error("Digite o número da NF-e.")
elif opcao == "Consultar por Carregamento":
    st.title("Consultar por Carregamento")
    num_carregamento = st.text_input("Digite o número do Carregamento:")
    if st.button("Buscar Carregamento"): 
        if num_carregamento:
            arquivos = os.listdir("minutas_salvas")
            minutas = [f for f in arquivos if f.startswith(f"C{num_carregamento}_")]
        if minutas:
            st.subheader(f"Minutas econtradas no Carregamento {num_carregamento}:")
            for arq in minutas:
                caminho = os.path.join("minutas_salvas", arq)
                st.image(caminho, caption=f"Arquivo: {arq}")
        else:
            st.warning("Nenhuma minuta encontrada para este carregamento .-.")
    else:
        st.error ("Digite o número do carregamento.")
elif opcao == "Cadastrar Minutas":
    st.title("Cadastro de Novas Minutas")
    carregamento = st.text_input("Digite o número do Carregamento:") 
    nf_cadastro = st.text_input("Digite o número da Nf-e:")
    foto = st.file_uploader("Selecione a foto da minuta assinada:", type=["png", "jpg", "jpeg"])
    if foto:
      st.image(foto, caption="Prévia da minuta selecionada", width=300)
    if st.button("Salvar Minuta"):
        if carregamento and nf_cadastro and foto:
            nome_arquivo = f"C{carregamento}_NF{nf_cadastro}.png"
            caminho_completo = os.path.join("minutas_salvas", nome_arquivo)
            with open(caminho_completo,"wb")as f:
                f.write(foto.getbuffer())
            st.success(f"Minuta salva com sucesso, fi! (NF: {nf_cadastro} | Carregamento: {carregamento})")
        else:
            st.error("Preencha todos os campos e selecione uma imagem para salvar!")