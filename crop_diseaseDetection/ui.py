import torch
import json
import ollama
from torchvision import models, transforms
from PIL import Image
import os
import streamlit as st

# --- 1. CONFIGURATION ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "efficientnet_fixed.pth"
LABEL_PATH = "efficientnet_labels.json"

# --- 2. CUSTOM CSS FOR UX ---
def local_css():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .report-box { 
            background-color: #e8f5e9; 
            padding: 20px; 
            border-left: 5px solid #2e7d32; 
            border-radius: 5px; 
            font-family: 'Courier New', Courier, monospace;
        }
        .header-text { color: #1b5e20; font-weight: 800; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. CORE LOGIC FUNCTIONS ---
@st.cache_resource # Keeps model in RAM so UI is fast
def load_agri_model():
    with open(LABEL_PATH, 'r') as f:
        class_names = json.load(f)
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier = torch.nn.Sequential(
        torch.nn.Dropout(0.4),
        torch.nn.Linear(in_features, 512),
        torch.nn.ReLU(),
        torch.nn.Dropout(0.4),
        torch.nn.Linear(512, len(class_names))
    )
    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
    state_dict = checkpoint['model_state_dict'] if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint else checkpoint
    model.load_state_dict(state_dict)
    model.to(DEVICE).eval()
    return model, class_names

def get_diagnosis(img_path, model, class_names):
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    img = Image.open(img_path).convert('RGB')
    img_tensor = transform(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        output = model(img_tensor)
        probs = torch.nn.functional.softmax(output[0], dim=0)
        conf, index = torch.max(probs, 0)
    return class_names[index], conf.item()

def get_gemma_report(disease_label, confidence):
    parts = disease_label.split('_')
    crop_name = parts[0].capitalize()
    disease_name = " ".join(parts[1:]).capitalize()
    
    # Force Gemma to strictly follow your format
    prompt = f"""Generate an official agricultural report:
    Crop: {crop_name}
    Disease: {disease_name}
    Confidence: {confidence:.2%}.
    Provide 3 direct recovery steps. Do not include introductory text."""

    response = ollama.generate(
        model='gemma2:2b', 
        system="Output strictly in this format: Crop Name: \nDisease Name: \nConfidence Score: \nRecommendations:",
        prompt=prompt,
        options={"temperature": 0.1}
    )
    return response['response']

# --- 4. MAIN UI INTERFACE ---
def main():
    local_css()
    st.markdown("<h1 class='header-text'>🌱 AgriAssist Pro</h1>", unsafe_allow_html=True)
    st.caption("Advanced Crop Diagnostic System | TNAU Integrated")

    # Sidebar for Model Info
    st.sidebar.header("System Status")
    st.sidebar.success("EfficientNet-B0: Active")
    st.sidebar.success("Gemma-2b: Local Linked")
    
    # Load model
    model, class_names = load_agri_model()

    # Layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📸 Image Upload")
        uploaded_file = st.file_uploader("Upload leaf photo", type=['jpg', 'png', 'jpeg'])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, width="stretch")

    with col2:
        st.markdown("### 📋 Analysis")
        if uploaded_file:
            if st.button("🚀 Run Full Diagnosis"):
                # Save temp
                temp_path = "temp_run.jpg"
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")
                image.save(temp_path)
                
                with st.spinner("AI is thinking..."):
                    # Step 1: Vision
                    label, conf = get_diagnosis(temp_path, model, class_names)
                    
                    # Step 2: Show Metrics
                    st.metric("Top Prediction", label.split('_')[0].capitalize())
                    st.metric("Confidence", f"{conf:.2%}")
                    
                    # Step 3: LLM Report
                    report = get_gemma_report(label, conf)
                    
                    st.markdown("---")
                    st.markdown("### 📄 Final Expert Report")
                    st.markdown(f"<div class='report-box'>{report}</div>", unsafe_allow_html=True)
                    
                    # Download Option
                    st.download_button("💾 Save Report", report, file_name="agri_report.txt")
        else:
            st.info("Please upload a leaf image to begin diagnosis.")

if __name__ == "__main__":
    main()