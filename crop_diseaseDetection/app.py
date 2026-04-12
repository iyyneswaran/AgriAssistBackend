import torch
import json
import ollama
from torchvision import models, transforms
from PIL import Image
import os
import streamlit as st

# --- 1. CONFIGURATION & MODELS ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "efficientnet_fixed.pth"
LABEL_PATH = "efficientnet_labels.json"

# --- 2. MODEL LOADING LOGIC ---
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

# --- 3. COMPUTER VISION INFERENCE ---
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

# --- 4. GEMMA 2B STRICT FORMATTING ---
def get_gemma_report(disease_label, confidence):
    parts = disease_label.split('_')
    crop_name = parts[0].capitalize()
    disease_name = " ".join(parts[1:]).capitalize()
    
    response = ollama.generate(
        model='gemma2:2b', 
        system="Output strictly: 3 bullet points for Recommendations. Do not include introductory text, crop names, or confidence scores in the output.",
        prompt=f"Report treatment recommendations for {crop_name} with {disease_name} at {confidence:.2%} confidence.",
        options={
            "temperature": 0.1,
            "num_predict": 100,  # ⚡ SPEED FIX: Stop model from long generation
            "num_thread": 8,     # ⚡ SPEED FIX: Uses more CPU cores for faster 'thinking'
            "top_k": 10          # ⚡ SPEED FIX: Limits vocabulary search
        }
    )
    return response['response']


# --- 5. STREAMLIT UI/UX ---
def main():
    st.set_page_config(page_title="AgriAssist Pro", page_icon="🌱", layout="centered")
    
    # Apply CSS for Dark Theme and Glassmorphism
    st.markdown("""
        <style>
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }
        /* Make button full-width and bright green */
        .stButton > button {
            width: 100%;
            background-color: #00e676 !important;
            color: #000000 !important;
            font-size: 20px !important;
            font-weight: 800 !important;
            border-radius: 8px !important;
            border: none;
            padding: 12px;
        }
        .stButton > button:hover {
            background-color: #00c853 !important;
            color: #000000 !important;
        }
        .glass-card {
            background: rgba(30, 30, 30, 0.4);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-radius: 12px;
            border: 1px solid #00e676;
            padding: 15px;
            margin-top: 20px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #e0e0e0;
        }
        .glass-card h1, .glass-card h2, .glass-card h3 {
            margin-top: 0;
            padding-bottom: 5px;
        }
        .header-text { color: #a5d6a7; font-weight: bold; text-align: center; }
        .sub-text { text-align: center; margin-bottom: 30px; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='header-text'>🌱 AgriAssist Pro Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='sub-text'>Real-time Agricultural Diagnostic System</h3>", unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("⚙️ System Health")
    st.sidebar.success("🟢 EfficientNet-B0: Online")
    st.sidebar.success("🟢 Gemma-2b: Online")
    
    # Session State for Model
    if 'model' not in st.session_state:
        with st.spinner("Loading AI Engine..."):
            st.session_state.model, st.session_state.labels = load_agri_model()

    st.markdown("### 📸 Image Upload")
    uploaded_file = st.file_uploader("Select Leaf Image", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Current Input", width="stretch")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Run Diagnosis"):
            # Save temp for processing
            temp_path = "temp_input.jpg"
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            image.save(temp_path)
            
            with st.spinner("Running deep learning diagnostics..."):
                # Run Vision
                raw_label, conf = get_diagnosis(temp_path, st.session_state.model, st.session_state.labels)
                
                parts = raw_label.split('_')
                crop_name = parts[0].capitalize()
                disease_name = " ".join(parts[1:]).capitalize()
                
                # Run LLM
                recommendations = get_gemma_report(raw_label, conf)
                
                # Format to HTML lists if markdown dashes or asterisks are used
                recs_html = recommendations.replace('\n- ', '<br>• ').replace('\n* ', '<br>• ')
                if recs_html.startswith('- '): recs_html = '• ' + recs_html[2:]
                elif recs_html.startswith('* '): recs_html = '• ' + recs_html[2:]
                
                st.success("Analysis Complete")
                
                # FINAL OUTPUT DISPLAY with Glassmorphism
                card_html = f"""
                <div class='glass-card'>
                    <h1 style='color: #ffffff;'>🌾 Crop: {crop_name}</h1>
                    <h2 style='color: #ff5252;'>🦠 Disease: {disease_name}</h2>
                    <h2 style='color: #4caf50;'>🎯 Confidence: {conf:.2%}</h2>
                    <hr style='border-top: 1px solid rgba(255,255,255,0.2); border-bottom: none;'>
                    <h3 style='color: #ffffff;'>Recommendations:</h3>
                    <div style='font-size: 1.1em; line-height: 1.6;'>
                        {recs_html.replace(chr(10), '<br>')}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()