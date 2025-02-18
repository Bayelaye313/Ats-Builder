import base64
import io
import time
import os
import pdf2image
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import pandas as pd

# Charger la clé API
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("🚨 Clé API Google non trouvée. Vérifiez votre configuration.")
    st.stop()
genai.configure(api_key=API_KEY)

# Fonction d'analyse IA
def get_gemini_response(input_text, pdf_content, prompt):
    time.sleep(1)  # Éviter le quota API
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

# Convertir un PDF en image et encoder en base64
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]

        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()
        }
# 🎨 Interface Streamlit
st.set_page_config(page_title="BourseAI - Demande de Bourse")
st.header("📜 Formulaire de Demande de Bourse")

# 📋 Formulaire de candidature
with st.form("bourse_form"):
    nom = st.text_input("Nom et Prénom")
    email = st.text_input("Email")
    niveau_etudes = st.selectbox("Niveau d'études", ["Bac", "Licence", "Master", "Doctorat"])
    revenus_famille = st.slider("Revenus familiaux mensuels (en FCFA)", 0, 1000000, step=5000)
    motivation = st.text_area("Expliquez pourquoi vous méritez cette bourse")

    # 📂 Upload du CV uniquement
    cv_file = st.file_uploader("📂 Téléchargez votre CV (PDF)", type=["pdf"])

    submit = st.form_submit_button("📊 Soumettre la Candidature")

# 📌 Si le formulaire est soumis
if submit:
    if not (nom and email and motivation and cv_file):
        st.warning("⚠️ Veuillez remplir tous les champs et téléverser le CV.")
    else:
        st.success("✅ Candidature soumise avec succès !")

        # 📂 Convertir le CV
        cv_content = input_pdf_setup(cv_file)

        # 📝 Prompt pour l'IA
        evaluation_prompt = f"""
        Vous êtes un jury de sélection pour une bourse d'étude. Évaluez cette candidature en fonction des critères suivants :
        - Niveau d'études : {niveau_etudes}
        - Revenus familiaux : {revenus_famille} FCFA
        - Motivation : {motivation}

        Analysez le CV et attribuez une note sur 100 avec des recommandations.
        """

        # 🧠 Analyse IA
        response = get_gemini_response(motivation, [cv_content], evaluation_prompt)

        # 📊 Résultat
        st.subheader("📌 Évaluation de la Candidature")
        st.write(response)

        # 🔢 Extraire le score et stocker les résultats (Simulé pour l'instant)
        score = int(response.split("Note :")[1].split("/")[0]) if "Note :" in response else None

        if score:
            df = pd.DataFrame([[nom, email, niveau_etudes, revenus_famille, motivation, score]], 
                              columns=["Nom", "Email", "Niveau", "Revenus", "Motivation", "Score"])
            df.to_csv("candidatures.csv", mode="a", index=False, header=not os.path.exists("candidatures.csv"))
            st.success(f"🎯 Score attribué : {score}/100")

# 📊 Classement des candidatures
st.subheader("🏆 Classement des Candidats")
if os.path.exists("candidatures.csv"):
    df_candidatures = pd.read_csv("candidatures.csv")
    df_candidatures = df_candidatures.sort_values(by="Score", ascending=False)
    st.dataframe(df_candidatures)
else:
    st.info("Aucune candidature enregistrée pour l'instant.")
