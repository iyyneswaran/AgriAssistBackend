"""
Fallback Remedies — Static rule-based remedy data for all 33 disease classes.
Used when Sarvam AI API is unavailable.
"""

FALLBACK_REMEDIES: dict[str, dict] = {
    # ─── Cotton Diseases ───
    "cotton_alternaria_leaf_spot": {
        "explanation": "Alternaria leaf spot is a fungal disease causing brown, circular spots on cotton leaves. It thrives in warm, humid conditions and can lead to significant defoliation.",
        "treatment_steps": [
            "Apply Mancozeb (2.5 g/L) or Copper oxychloride (3 g/L) as foliar spray.",
            "Remove and destroy severely infected leaves to reduce inoculum.",
            "Spray fungicide at 10-day intervals during humid weather.",
            "Ensure proper plant spacing for air circulation."
        ],
        "preventive_measures": [
            "Use resistant cotton varieties where available.",
            "Practice crop rotation with non-host crops.",
            "Avoid overhead irrigation; prefer drip irrigation.",
            "Maintain field hygiene by removing crop debris after harvest."
        ],
    },
    "cotton_aphids": {
        "explanation": "Aphids are small sap-sucking insects that cluster on the undersides of cotton leaves, causing leaf curling, yellowing, and honeydew secretion that promotes sooty mold growth.",
        "treatment_steps": [
            "Spray Imidacloprid (0.3 mL/L) or Thiamethoxam (0.2 g/L) targeting leaf undersides.",
            "Apply Neem oil (5 mL/L) as an organic alternative for mild infestations.",
            "Use yellow sticky traps to monitor and reduce adult aphid populations.",
            "Release natural predators like ladybugs and lacewings."
        ],
        "preventive_measures": [
            "Monitor fields weekly during the vegetative stage.",
            "Avoid excessive nitrogen fertilization which promotes soft growth.",
            "Maintain beneficial insect habitat around fields.",
            "Remove weeds that serve as alternate hosts."
        ],
    },
    "cotton_army_worm": {
        "explanation": "Army worms are caterpillars that feed voraciously on cotton leaves and bolls, often causing severe defoliation when present in large numbers. They typically attack in the late vegetative and reproductive stages.",
        "treatment_steps": [
            "Apply Chlorantraniliprole (0.3 mL/L) or Emamectin benzoate (0.4 g/L).",
            "Use Bacillus thuringiensis (Bt) sprays for organic management.",
            "Spray in the evening when caterpillars are most active.",
            "Handpick and destroy egg masses and early-instar larvae."
        ],
        "preventive_measures": [
            "Install pheromone traps for early detection of moth activity.",
            "Practice intercropping with trap crops like maize.",
            "Encourage natural enemies such as Trichogramma parasitoids.",
            "Deep plough after harvest to destroy pupae in soil."
        ],
    },
    "cotton_bacterial_blight": {
        "explanation": "Bacterial blight (Xanthomonas citri pv. malvacearum) causes angular, water-soaked lesions on leaves that later turn brown. It can also attack bolls, reducing fiber quality.",
        "treatment_steps": [
            "Spray Streptocycline (1 g/10L) + Copper oxychloride (3 g/L).",
            "Remove and burn infected plant parts immediately.",
            "Avoid working in wet fields to prevent spreading bacteria.",
            "Apply sprays at early symptom appearance for best results."
        ],
        "preventive_measures": [
            "Use certified disease-free seeds from resistant varieties.",
            "Treat seeds with Carboxin or Thiram before sowing.",
            "Avoid overhead irrigation; use furrow or drip methods.",
            "Follow a 2-3 year crop rotation with non-host crops."
        ],
    },
    "cotton_curl_virus": {
        "explanation": "Cotton leaf curl virus (CLCuV) is transmitted by whiteflies, causing upward curling of leaves, thickened veins, and stunted growth. Severely infected plants produce very few bolls.",
        "treatment_steps": [
            "Control whitefly vectors with Spiromesifen (1 mL/L) or Pyriproxyfen (1.5 mL/L).",
            "Remove and destroy infected plants to prevent further spread.",
            "Apply Neem-based insecticides as supplementary whitefly control.",
            "Install yellow sticky traps around field borders."
        ],
        "preventive_measures": [
            "Plant CLCuV-resistant cotton varieties (e.g., Bt cotton hybrids).",
            "Avoid late sowing which coincides with peak whitefly populations.",
            "Maintain weed-free fields; weeds harbor whiteflies.",
            "Do not grow alternate host crops near cotton fields."
        ],
    },
    "cotton_fusarium_wilt": {
        "explanation": "Fusarium wilt is a soil-borne fungal disease that blocks water-conducting vessels, causing wilting, yellowing, and eventual death of cotton plants. Browning of vascular tissue is a key diagnostic sign.",
        "treatment_steps": [
            "Apply Trichoderma viride (5 g/kg seed) as seed treatment.",
            "Drench soil with Carbendazim (1 g/L) around affected plants.",
            "Uproot and destroy severely wilted plants to reduce soil inoculum.",
            "Apply bio-agents like Pseudomonas fluorescens to the root zone."
        ],
        "preventive_measures": [
            "Use wilt-resistant cotton varieties.",
            "Practice crop rotation with cereals for at least 3 years.",
            "Apply well-decomposed organic matter to improve soil microbial balance.",
            "Avoid waterlogging; ensure proper field drainage."
        ],
    },
    "cotton_healthy": {
        "explanation": "Your cotton crop appears healthy! No disease symptoms were detected in the image. Continue maintaining good agricultural practices.",
        "treatment_steps": [
            "No treatment needed — crop appears healthy.",
            "Continue regular monitoring every 7-10 days.",
            "Maintain balanced fertilization schedule.",
            "Ensure proper irrigation management."
        ],
        "preventive_measures": [
            "Scout fields regularly for early signs of pests or diseases.",
            "Maintain proper plant spacing for air circulation.",
            "Apply preventive fungicide sprays before monsoon season.",
            "Keep field borders clean of weeds and alternate hosts."
        ],
    },
    "cotton_powdery_mildew": {
        "explanation": "Powdery mildew appears as white, powdery fungal growth on leaf surfaces. It reduces photosynthesis and, if severe, can cause premature leaf drop and reduced yield.",
        "treatment_steps": [
            "Spray Sulphur WP (3 g/L) or Karathane (1 mL/L) at first sign.",
            "Apply systemic fungicide like Hexaconazole (2 mL/L) for severe cases.",
            "Repeat sprays at 10-15 day intervals if conditions persist.",
            "Avoid excessive nitrogen fertilization."
        ],
        "preventive_measures": [
            "Use resistant varieties where available.",
            "Ensure adequate plant spacing for ventilation.",
            "Avoid late-season nitrogen applications.",
            "Remove volunteer cotton plants that may harbor the fungus."
        ],
    },
    "cotton_target_spot": {
        "explanation": "Target spot (Corynespora cassiicola) forms concentric ring spots on cotton leaves. In severe cases, it causes extensive defoliation, especially in humid conditions.",
        "treatment_steps": [
            "Apply Azoxystrobin (1 mL/L) or Tebuconazole (1.5 mL/L).",
            "Begin spraying at the first appearance of lesions.",
            "Ensure thorough coverage of both upper and lower leaf surfaces.",
            "Re-apply at 7-10 day intervals during rainy weather."
        ],
        "preventive_measures": [
            "Rotate with non-host crops for at least 1 year.",
            "Destroy crop residues after harvest.",
            "Avoid excessive irrigation that keeps foliage wet.",
            "Use balanced fertilization to promote strong plant health."
        ],
    },
    "cotton_verticillium_wilt": {
        "explanation": "Verticillium wilt causes yellowing and browning of leaf margins, often on one side of the plant. Infected plants show vascular browning when stems are cut open.",
        "treatment_steps": [
            "Apply Trichoderma-based biocontrol agents to the root zone.",
            "Drench with Carbendazim (1 g/L) at early symptom stage.",
            "Remove severe cases to reduce soil inoculum buildup.",
            "Apply organic soil amendments to suppress the pathogen."
        ],
        "preventive_measures": [
            "Use Verticillium-tolerant cotton varieties.",
            "Avoid fields with a history of Verticillium wilt.",
            "Practice long-term crop rotation with cereals.",
            "Improve soil drainage and avoid waterlogging."
        ],
    },

    # ─── Paddy Diseases ───
    "paddy_bacterial_leaf_blight": {
        "explanation": "Bacterial leaf blight (Xanthomonas oryzae) causes water-soaked lesions that expand into yellow-white streaks from leaf tips. It is one of the most destructive rice diseases.",
        "treatment_steps": [
            "Spray Streptocycline (1 g/10L) + Copper hydroxide (2 g/L).",
            "Drain excess water from fields to reduce bacterial spread.",
            "Apply sprays during early morning or late evening.",
            "Remove severely infected tillers from the field."
        ],
        "preventive_measures": [
            "Use BLB-resistant rice varieties.",
            "Avoid excessive nitrogen fertilization.",
            "Ensure balanced NPK nutrition.",
            "Maintain proper water management; avoid continuous flooding."
        ],
    },
    "paddy_bacterial_leaf_streak": {
        "explanation": "Bacterial leaf streak shows narrow, brown streaks between leaf veins. Unlike BLB, the lesions follow veins and are typically thinner. It is caused by Xanthomonas oryzae pv. oryzicola.",
        "treatment_steps": [
            "Spray Copper oxychloride (3 g/L) at early symptom stage.",
            "Apply Streptocycline (1 g/10L) mixed with copper fungicide.",
            "Reduce field water level during active infection.",
            "Avoid spreading the infection through field tools."
        ],
        "preventive_measures": [
            "Plant tolerant varieties.",
            "Avoid excess nitrogen application.",
            "Use balanced fertilization with adequate potassium.",
            "Practice crop rotation and field sanitation."
        ],
    },
    "paddy_bacterial_panicle_blight": {
        "explanation": "Bacterial panicle blight (Burkholderia glumae) causes grain discoloration, sterility, and rotting of panicles. It is most severe in high-temperature, high-humidity conditions.",
        "treatment_steps": [
            "Apply Copper-based bactericides at the booting stage.",
            "Reduce nitrogen application to moderate levels.",
            "Drain fields temporarily to reduce humidity around panicles.",
            "Remove severely infected panicles to prevent spread."
        ],
        "preventive_measures": [
            "Use clean, certified seed from healthy fields.",
            "Treat seeds with hot water (60°C for 10 minutes).",
            "Avoid late planting that exposes panicles to peak summer heat.",
            "Maintain balanced fertilization."
        ],
    },
    "paddy_blast": {
        "explanation": "Rice blast (Magnaporthe oryzae) is a devastating fungal disease causing diamond-shaped lesions on leaves and neck rot in panicles. It can cause 100% yield loss in severe cases.",
        "treatment_steps": [
            "Spray Tricyclazole (0.6 g/L) or Isoprothiolane (1.5 mL/L) immediately.",
            "Apply at both the tillering and panicle emergence stages.",
            "Ensure complete canopy coverage during spraying.",
            "Repeat application after 10 days if the disease persists."
        ],
        "preventive_measures": [
            "Use blast-resistant rice varieties suitable for your region.",
            "Avoid excessive nitrogen; split applications are preferred.",
            "Maintain shallow water in paddies rather than deep flooding.",
            "Remove rice stubble and crop debris after harvest."
        ],
    },
    "paddy_brown_spot": {
        "explanation": "Brown spot (Bipolaris oryzae) causes oval, brown lesions with yellow halos on rice leaves. It is associated with nutrient-deficient soils, particularly low potassium.",
        "treatment_steps": [
            "Spray Mancozeb (2.5 g/L) or Propiconazole (1 mL/L).",
            "Apply potassium fertilizer (Muriate of Potash) to correct deficiency.",
            "Spray at the early lesion appearance stage.",
            "Apply zinc sulfate (5 kg/acre) if zinc deficiency is present."
        ],
        "preventive_measures": [
            "Ensure balanced NPK nutrition with adequate potassium.",
            "Use disease-free certified seeds.",
            "Treat seeds with Thiram or Carbendazim (2 g/kg).",
            "Maintain proper water management in paddies."
        ],
    },
    "paddy_dead_heart": {
        "explanation": "Dead heart is caused by stem borers (Scirpophaga incertulas). The central shoot dies and can be easily pulled out, showing a characteristic withered appearance during the vegetative stage.",
        "treatment_steps": [
            "Apply Cartap hydrochloride granules (1 kg a.i./ha) in paddy water.",
            "Spray Chlorantraniliprole (0.3 mL/L) targeting the stem base.",
            "Clip and destroy egg masses found on leaf tips.",
            "Release Trichogramma japonicum egg parasitoids at 50,000/acre."
        ],
        "preventive_measures": [
            "Install pheromone traps (5/acre) for yellow stem borer monitoring.",
            "Avoid close planting; maintain recommended spacing.",
            "Harvest at ground level and destroy stubbles.",
            "Practice synchronous planting in the community."
        ],
    },
    "paddy_downy_mildew": {
        "explanation": "Downy mildew causes whitish-yellow streaks on leaves with a downy fungal growth visible on the underside. Infected plants are stunted and may not produce panicles.",
        "treatment_steps": [
            "Spray Metalaxyl (2 g/L) or Fosetyl-aluminium at first symptoms.",
            "Remove and destroy infected plants from nursery beds.",
            "Ensure good drainage in nursery and main fields.",
            "Apply sprays in the morning when dew is still present."
        ],
        "preventive_measures": [
            "Use resistant varieties if available in your region.",
            "Treat seeds with Metalaxyl-based fungicide.",
            "Avoid poorly drained nursery areas.",
            "Maintain proper spacing in seedbed and main field."
        ],
    },
    "paddy_healthy": {
        "explanation": "Your paddy crop appears healthy! No visible disease symptoms were found. Keep up the good work with regular field monitoring.",
        "treatment_steps": [
            "No treatment needed — crop appears healthy.",
            "Continue scheduled fertilizer applications.",
            "Monitor water levels and adjust irrigation as needed.",
            "Scout for pests at regular intervals."
        ],
        "preventive_measures": [
            "Maintain balanced NPK fertilization.",
            "Practice integrated pest management (IPM).",
            "Keep field bunds clean to reduce pest habitats.",
            "Follow recommended spacing and seed rates."
        ],
    },
    "paddy_hispa": {
        "explanation": "Rice hispa (Dicladispa armigera) adults scrape leaf surfaces while larvae mine inside leaves, leaving white streaks. Severe infestations give fields a whitish, scorched appearance.",
        "treatment_steps": [
            "Spray Chlorpyrifos (2 mL/L) or Quinalphos (2 mL/L) on affected areas.",
            "Clip and destroy leaf tips containing eggs and larvae.",
            "Avoid blanket spraying; target only infested patches.",
            "Drain water from fields temporarily to expose pests."
        ],
        "preventive_measures": [
            "Avoid excessive nitrogen which attracts hispa.",
            "Maintain clean bunds and remove grassy weeds.",
            "Encourage natural predators like spiders and wasps.",
            "Practice community-level synchronous planting."
        ],
    },
    "paddy_leaf_scald": {
        "explanation": "Leaf scald shows alternating light and dark zones on leaf tips, giving a scalded appearance. It is caused by Microdochium oryzae and is common in cool, wet conditions.",
        "treatment_steps": [
            "Apply Propiconazole (1 mL/L) or Carbendazim (1 g/L).",
            "Ensure adequate potassium fertilization.",
            "Remove heavily infected leaves from the field.",
            "Spray at early symptom stage for best results."
        ],
        "preventive_measures": [
            "Use resistant or moderately resistant varieties.",
            "Avoid excessive nitrogen application.",
            "Ensure proper field drainage.",
            "Remove crop residue after harvest."
        ],
    },
    "paddy_narrow_brown_spot": {
        "explanation": "Narrow brown spot (Cercospora janseana) produces narrow, linear brown lesions on leaves. It is more common in mature crops and nutrient-stressed conditions.",
        "treatment_steps": [
            "Spray Mancozeb (2.5 g/L) or Carbendazim (1 g/L).",
            "Correct potassium deficiency with MOP application.",
            "Apply foliar micronutrient spray if deficiency is suspected.",
            "Repeat sprays at 10-day intervals during wet weather."
        ],
        "preventive_measures": [
            "Maintain balanced soil nutrition with regular soil testing.",
            "Use clean, certified seed material.",
            "Practice crop rotation where possible.",
            "Ensure proper water management."
        ],
    },
    "paddy_tungro": {
        "explanation": "Rice tungro virus is transmitted by green leafhoppers. Infected plants show yellow-orange discoloration, stunted growth, and reduced tillering. Two viruses (RTBV and RTSV) are involved.",
        "treatment_steps": [
            "Control green leafhoppers with Imidacloprid (0.3 mL/L).",
            "Remove and destroy infected hills from the field immediately.",
            "Use light traps to monitor and reduce leafhopper populations.",
            "Apply insecticide sprays targeting field borders first."
        ],
        "preventive_measures": [
            "Plant tungro-resistant rice varieties (e.g., IR36, IR64).",
            "Practice synchronous planting in the community.",
            "Avoid staggered planting that creates a green bridge for the virus.",
            "Monitor nurseries carefully before transplanting."
        ],
    },

    # ─── Tomato Diseases ───
    "tomato_bacterial_spot": {
        "explanation": "Bacterial spot (Xanthomonas vesicatoria) causes small, dark, water-soaked spots on leaves and fruits. Lesions become raised and scab-like on fruits, reducing marketability.",
        "treatment_steps": [
            "Spray Copper hydroxide (2 g/L) mixed with Mancozeb (2.5 g/L).",
            "Remove and destroy severely infected plant parts.",
            "Avoid overhead irrigation to reduce splash dispersal.",
            "Apply sprays every 7-10 days during rain periods."
        ],
        "preventive_measures": [
            "Use certified disease-free seeds and transplants.",
            "Practice crop rotation (2-3 years away from solanaceous crops).",
            "Avoid working in wet fields to prevent bacterial spread.",
            "Sanitize stakes, cages, and tools between seasons."
        ],
    },
    "tomato_early_blight": {
        "explanation": "Early blight (Alternaria solani) produces dark brown spots with concentric rings (target spots) on older leaves first. It can also infect stems and fruits, reducing yield significantly.",
        "treatment_steps": [
            "Apply Mancozeb (2.5 g/L) or Chlorothalonil (2 g/L) as foliar spray.",
            "Use systemic fungicides like Azoxystrobin (1 mL/L) for severe cases.",
            "Remove lower infected leaves to slow disease spread.",
            "Spray at 7-10 day intervals during wet, warm weather."
        ],
        "preventive_measures": [
            "Mulch around plants to prevent soil splash onto lower leaves.",
            "Stake or cage plants to improve air circulation.",
            "Water at the base; avoid wetting foliage.",
            "Practice 2-year rotation away from tomato and potato."
        ],
    },
    "tomato_healthy": {
        "explanation": "Your tomato crop appears healthy! No disease symptoms were detected. Excellent job maintaining your crop health.",
        "treatment_steps": [
            "No treatment needed — crop appears healthy.",
            "Continue regular monitoring for pests and diseases.",
            "Maintain balanced fertilization (NPK + micronutrients).",
            "Ensure consistent watering schedule."
        ],
        "preventive_measures": [
            "Prune lower branches for air circulation.",
            "Apply preventive fungicide before rainy season.",
            "Monitor for common pests like whitefly and fruit borer.",
            "Maintain field hygiene and weed control."
        ],
    },
    "tomato_late_blight": {
        "explanation": "Late blight (Phytophthora infestans) causes large, irregular, water-soaked patches on leaves and stems. A white mold appears on the underside. This disease can destroy a crop within days in cool, wet weather.",
        "treatment_steps": [
            "Spray Metalaxyl + Mancozeb (2.5 g/L) immediately at first sign.",
            "Apply Cymoxanil-based fungicides for curative action.",
            "Remove and destroy all infected plant material.",
            "Spray every 5-7 days during active disease conditions."
        ],
        "preventive_measures": [
            "Use late blight-resistant tomato varieties.",
            "Avoid overhead irrigation and evening watering.",
            "Ensure proper plant spacing for air flow.",
            "Destroy volunteer tomato and potato plants nearby."
        ],
    },
    "tomato_leaf_mold": {
        "explanation": "Leaf mold (Passalora fulva) shows pale green to yellow spots on upper leaf surfaces with olive-green moldy growth underneath. It is common in greenhouse and high-humidity conditions.",
        "treatment_steps": [
            "Spray Mancozeb (2.5 g/L) or Chlorothalonil (2 g/L).",
            "Improve ventilation in greenhouses; open vents and use fans.",
            "Remove severely infected lower leaves.",
            "Reduce irrigation frequency to lower humidity."
        ],
        "preventive_measures": [
            "Grow resistant tomato varieties.",
            "Maintain greenhouse humidity below 85%.",
            "Ensure proper plant spacing.",
            "Disinfect greenhouse structures between crops."
        ],
    },
    "tomato_septoria_leaf_spot": {
        "explanation": "Septoria leaf spot produces numerous small, round spots with dark borders and gray centers on lower leaves. Tiny black dots (pycnidia) are visible within spots under magnification.",
        "treatment_steps": [
            "Spray Mancozeb (2.5 g/L) or Copper-based fungicide.",
            "Remove infected lower leaves to reduce spore production.",
            "Apply fungicide before symptoms spread to upper canopy.",
            "Continue spraying at 7-10 day intervals in wet weather."
        ],
        "preventive_measures": [
            "Mulch heavily to prevent rain splash from soil.",
            "Water at the base of plants only.",
            "Rotate crops; do not plant tomatoes after tomatoes.",
            "Clean up all plant debris at the end of the season."
        ],
    },
    "tomato_spider_mites": {
        "explanation": "Spider mites (Tetranychus urticae) cause tiny yellow stippling on leaves, followed by bronzing and webbing. They thrive in hot, dry conditions and can rapidly devastate crops.",
        "treatment_steps": [
            "Spray Abamectin (0.5 mL/L) or Spiromesifen (0.8 mL/L).",
            "Apply strong water jets to dislodge mites from leaf undersides.",
            "Release predatory mites (Phytoseiulus persimilis) for biocontrol.",
            "Alternate between chemical classes to prevent resistance."
        ],
        "preventive_measures": [
            "Maintain adequate irrigation; drought stress favors mites.",
            "Avoid broad-spectrum insecticides that kill mite predators.",
            "Monitor with a hand lens; check leaf undersides weekly.",
            "Increase humidity around plants when possible."
        ],
    },
    "tomato_target_spot": {
        "explanation": "Target spot (Corynespora cassiicola) produces brown spots with concentric rings on both leaves and fruit. It is particularly aggressive in warm, humid conditions.",
        "treatment_steps": [
            "Spray Azoxystrobin (1 mL/L) + Difenoconazole (0.5 mL/L).",
            "Remove heavily infected leaves and fallen debris.",
            "Maintain spray program during flowering and fruit set.",
            "Apply at 7-day intervals under high disease pressure."
        ],
        "preventive_measures": [
            "Use tolerant tomato hybrids where available.",
            "Avoid excessive canopy density; prune as needed.",
            "Practice clean cultivation with minimal crop debris.",
            "Rotate with non-host crops like cereals."
        ],
    },
    "tomato_tomato_mosaic_virus": {
        "explanation": "Tomato mosaic virus (ToMV) causes light and dark green mottled patterns on leaves, leaf distortion, and stunted growth. It spreads easily through contaminated tools, hands, and seed.",
        "treatment_steps": [
            "There is no chemical cure for viral diseases.",
            "Remove and destroy infected plants immediately to prevent spread.",
            "Wash hands with soap and disinfect tools with 10% bleach solution.",
            "Control aphid vectors with Imidacloprid if present."
        ],
        "preventive_measures": [
            "Use TMV-resistant tomato varieties (marked 'T' or 'ToMV' on label).",
            "Disinfect all tools and equipment before entering the field.",
            "Avoid tobacco products near tomato plants (TMV can survive in tobacco).",
            "Use virus-free certified seeds and transplants."
        ],
    },
    "tomato_tomato_yellow_leaf_curl_virus": {
        "explanation": "TYLCV causes severe upward curling, yellowing, and stunting of tomato plants. It is transmitted by whiteflies (Bemisia tabaci) and can cause near-total yield loss.",
        "treatment_steps": [
            "Control whiteflies aggressively with Pyriproxyfen (1.5 mL/L) or Spiromesifen.",
            "Remove and destroy infected plants — there is no cure.",
            "Install 40-mesh insect-proof nets in nurseries.",
            "Apply reflective silver mulch to repel whiteflies."
        ],
        "preventive_measures": [
            "Plant TYLCV-resistant tomato varieties.",
            "Use insect-proof net houses for seedling production.",
            "Avoid planting tomatoes near infested fields.",
            "Maintain a host-free period between tomato crops."
        ],
    },
}


def get_fallback_remedy(disease_label: str) -> dict:
    """
    Returns a fallback remedy dict for the given disease label.
    If not found, returns a generic response.
    """
    remedy = FALLBACK_REMEDIES.get(disease_label)
    if remedy:
        return {
            "explanation": remedy["explanation"],
            "treatment_steps": remedy["treatment_steps"],
            "preventive_measures": remedy["preventive_measures"],
            "sensor_advice": None,
            "source": "fallback",
        }

    # Generic fallback
    return {
        "explanation": f"A condition has been detected in your crop. Please consult a local agricultural extension officer for detailed guidance.",
        "treatment_steps": [
            "Monitor the crop closely for any changes.",
            "Take clear photos and consult your nearest Krishi Vigyan Kendra (KVK).",
            "Avoid applying any chemicals without expert advice.",
        ],
        "preventive_measures": [
            "Practice crop rotation to break disease cycles.",
            "Use disease-free, certified seeds.",
            "Maintain proper field hygiene.",
        ],
        "sensor_advice": None,
        "source": "fallback",
    }
