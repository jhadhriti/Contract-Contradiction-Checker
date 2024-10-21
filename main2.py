import gradio as gr
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from Bhashini_APIs import api_test_transliteration, api_test_translation, api_test_asr
import nltk
import time
# Importing functions from contractdocreader.py
from Main_Operations.docread import docread


# Load models
semantic_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

nli_model_alt = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"

# Load NLI models for each language
nli_models = {
    "en": pipeline("text-classification", model=nli_model_alt),
    "hi": pipeline("text-classification", model=nli_model_alt),
    "mr": pipeline("text-classification", model=nli_model_alt),
    "gu": pipeline("text-classification", model=nli_model_alt),
    "pa": pipeline("text-classification", model=nli_model_alt),
    "bn": pipeline("text-classification", model=nli_model_alt),
}



# Initialize Bhashini API (mock for demonstration)
def bhashini_api_mock(text, source_lang, target_lang):
    # Mock function to represent translation, ASR, transliteration
    return text  # In actual implementation, connect to Bhashini API

# Welcome messages and audio files (mock paths)
welcome_messages = {
    "en": ("Welcome!", "welcome_audios/welcome.wav"),
    "hi": ("स्वागत है!", "welcome_audios/swagat.wav"),
    "mr": ("स्वागत आहे!", "welcome_audios/swagat_mr.wav"),
    "gu": ("સ્વાગત છે!", "welcome_audios/Swagat_chhe.wav"),
    "pa": ("ਸੁਆਗਤ ਹੈ!", "welcome_audios/welcome_pn.wav"),
    "bn": ("স্বাগতম!", "welcome_audios/welcome_bn.wav"),
}

# Function to handle language selection
def select_language(language):
    message, audio_path = welcome_messages[language]
    return message, audio_path

# Function to get embeddings
def get_embeddings(texts):
    return semantic_model.encode(texts, convert_to_tensor=True)

# Function to perform semantic search
def semantic_search(query, documents, threshold=0.4):
    query_embedding = get_embeddings([query])
    doc_embeddings = get_embeddings(documents)
    similarities = util.pytorch_cos_sim(query_embedding, doc_embeddings)[0]
    relevant_indices = [i for i in range(len(similarities)) if similarities[i] >= threshold]
    return [(documents[i], similarities[i].item()) for i in relevant_indices]

# Function to process the document
def process_document(language, topic, problem, document, document_lang):
    # Read and translate the document
    document_text = docread(document)
    ocr_text = bhashini_api_mock(document_text, document_lang, language)  # Translate to user's language

    # Semantic search
    matched_paragraphs = semantic_search(topic, [ocr_text])
    results = []

    nli_model = nli_models[language]  # Select the appropriate NLI model

    for para, similarity in matched_paragraphs:
        sentences = nltk.sent_tokenize(para)
        for sentence in sentences:
            try:
                # Ensure the input is correctly formatted
                inputs = f"{sentence} {problem}"
                print(f"Inputs to NLI model: {inputs}")  # Debugging line
                result = nli_model(inputs)[0]
                results.append((sentence, result))
            except Exception as e:
                print(f"Error processing sentence: {sentence}, Error: {e}")

    # Final output
    thank_you_message = bhashini_api_mock("Thank you!", "en", language)
    return results, thank_you_message

# Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("## Welcome! Please wait while we load...")
    
    with gr.Tabs():
        with gr.TabItem("Step 1: Welcome"):
            language = gr.Radio(["en", "hi", "mr", "gu", "pa", "bn"], label="Select your language")
            welcome_output = gr.Textbox()
            welcome_audio = gr.Audio()
            gr.Button("Submit").click(select_language, inputs=language, outputs=[welcome_output, welcome_audio])

        with gr.TabItem("Service 1: Transliteration (Only from english available so far)"):
            srclanguage = gr.Radio(["en"], label="Select source language")
            language = gr.Radio(["en", "hi", "mr", "gu", "pa", "bn"], label="Select target language")
            textbox = gr.Textbox()
            transOutput = gr.Textbox()
            gr.Button("Submit").click(api_test_transliteration.transliteration, inputs=[textbox, srclanguage, language], outputs=transOutput)

        with gr.TabItem("Service 2: Translation (Only from english available so far)"):
            srclanguage = gr.Radio(["en"], label="Select source language")
            language = gr.Radio(["en", "hi", "mr", "gu", "pa", "bn"], label="Select target language")
            textbox = gr.Textbox()
            transOutput = gr.Textbox()
            gr.Button("Submit").click(api_test_translation.translate, inputs=[textbox, srclanguage, language], outputs=transOutput)

        with gr.TabItem("Service 3: ASR"):
            language = gr.Radio(["en", "hi", "mr", "gu", "pa", "bn"], label="Select target language")
            audio = gr.Audio(type="filepath", label="Upload Audio")
            text = gr.Textbox(label="Output")
            gr.Button("Submit").click(api_test_asr.asr, inputs=[audio, language], outputs=text)

        with gr.TabItem("Step 2: Input Language and Details"):
            user_language = gr.Radio(["en", "hi", "mr", "gu", "pa", "bn"], label="Preferred Language")
            user_topic = gr.Textbox(label="Topic of Concern")
            user_problem = gr.Textbox(label="Detailed Problem Description")
        
        with gr.TabItem("Step 3: Upload Document"):
            document = gr.File(label="Upload your legal document")
            document_lang = gr.Dropdown(["English", "Hindi", "Marathi", "Gujarati", "Punjabi", "Bengali"], label="Document Language")
            results_output = gr.Dataframe(headers=["Sentence", "NLI Result"])  # To display results of semantic search
            thank_you_message = gr.Textbox(label="Thank You Message")
            gr.Button("Submit").click(process_document, inputs=[user_language, user_topic, user_problem, document, document_lang], outputs=[results_output, thank_you_message])

demo.launch()