import base64
import io
import os
import pdf2image
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


# Charger les variables d'environnement
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')
    response = model.generate_content([input, pdf_content[0], prompt])
    return response.text

def analyze_matching(input, pdf_content):
    """Analyse le matching entre le CV et la description du poste"""
    prompt = f"""
    Analysez le matching entre ce CV et la description du poste suivante.
    Fournissez une analyse détaillée avec :
    1. Un score sur 100
    2. Les points forts du candidat
    3. Les points à améliorer
    4. Les mots-clés manquants
    
    Description du poste:
    {input}
    
    Format de réponse souhaité:
    Score: [X/100]
    Points forts:
    - [point 1]
    - [point 2]
    Points à améliorer:
    - [point 1]
    - [point 2]
    Mots-clés manquants:
    - [mot-clé 1]
    - [mot-clé 2]
    """
    
    response = get_gemini_response(input, pdf_content, prompt)
    return response

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        pdf_parts = [{"mime_type": "image/jpeg", "data": base64.b64encode(img_byte_arr).decode()}]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

def clean_resume_text(text):
    """ Nettoie le texte de réponse de Gemini en supprimant les annotations """
    unwanted_phrases = [
        "Okay, here's a revised resume", 
        "**Wording:**", 
        "**ATS Optimization:**", 
        "**Conciseness:**", 
        "**French to English**"
    ]
    for phrase in unwanted_phrases:
        text = text.split(phrase)[0]
    return text.strip()

def generate_pdf(resume_text):
    """ Génère un CV formaté en PDF avec reportlab """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    content = []
    content.append(Paragraph("<b>Curriculum Vitae Optimisé</b>", styles["Title"]))
    content.append(Spacer(1, 12))

    for line in resume_text.split("\n"):
        if line.strip():
            content.append(Paragraph(line, styles["Normal"]))
            content.append(Spacer(1, 6))

    doc.build(content)
    buffer.seek(0)
    return buffer

# --- Streamlit App ---
st.set_page_config(page_title="ATS Resume Expert", layout="wide")
st.title("Optimiseur de CV pour ATS")

# Ajout d'une description explicative
st.markdown("""
    ### Comment utiliser cet outil
    1. Copiez-collez la description du poste dans le champ ci-dessous
    2. Téléchargez votre CV au format PDF
    3. Choisissez l'action souhaitée (Analyse de matching ou Optimisation)
""")

# Section pour la description du poste
st.subheader("Description du Poste")
input_text = st.text_area("Collez la description du poste ici:", height=200, key="input")

# Section pour le CV
st.subheader("Votre CV")
uploaded_file = st.file_uploader("Téléchargez votre CV (PDF)...", type=["pdf"])

# Création de deux colonnes pour les boutons
col1, col2 = st.columns(2)

with col1:
    analyze_button = st.button("Analyser le Matching", type="primary")

with col2:
    optimize_button = st.button("Optimiser mon CV", type="secondary")

if analyze_button:
    if not input_text:
        st.error("Veuillez entrer une description de poste")
    elif not uploaded_file:
        st.error("Veuillez télécharger votre CV")
    else:
        with st.spinner("Analyse du matching en cours..."):
            try:
                pdf_content = input_pdf_setup(uploaded_file)
                analysis = analyze_matching(input_text, pdf_content)
                
                # Afficher les résultats de l'analyse
                st.success("Analyse terminée!")
                st.markdown("### Résultats de l'Analyse")
                st.markdown(analysis)
                
            except Exception as e:
                st.error(f"Une erreur est survenue: {str(e)}")

if optimize_button:
    if not input_text:
        st.error("Veuillez entrer une description de poste")
    elif not uploaded_file:
        st.error("Veuillez télécharger votre CV")
    else:
        with st.spinner("Optimisation de votre CV en cours..."):
            try:
                pdf_content = input_pdf_setup(uploaded_file)
                
                prompt = f"""
                Optimisez ce CV pour le poste suivant. Assurez-vous de :
                1. Mettre en avant les compétences pertinentes
                2. Utiliser les mots-clés de la description
                3. Adapter l'expérience aux exigences du poste
                4. Maintenir un format professionnel
                5. Optimiser pour les systèmes ATS
                
                Description du poste:
                {input_text}
                
                Fournissez uniquement le CV optimisé, sans explications supplémentaires.
                """
                
                response = get_gemini_response(input_text, pdf_content, prompt)
                clean_resume = clean_resume_text(response)

                pdf_buffer = generate_pdf(clean_resume)

                st.success("Votre CV a été optimisé avec succès!")
                st.subheader("Télécharger votre CV Optimisé")
                st.download_button(
                    label="📥 Télécharger le PDF",
                    data=pdf_buffer,
                    file_name="CV_Optimise.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Une erreur est survenue: {str(e)}")
