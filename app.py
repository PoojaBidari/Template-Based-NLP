from flask import Flask, render_template, request, jsonify
import pandas as pd
import random

app = Flask(__name__)

# Load dataset
df = pd.read_csv('data/data.csv')
symptom_cols = [col for col in df.columns if col != 'diseases']

def evaluate_fluency(text):
    """Evaluate the fluency of generated text (score out of 10)"""
    score = 0
    if text and text[0].isupper():
        score += 2
    if text and text[-1] in '.!?':
        score += 2
    words = text.split()
    if 10 <= len(words) <= 30:
        score += 2
    elif len(words) > 5:
        score += 1
    medical_keywords = ['symptom', 'doctor', 'medication', 'consult', 'diagnosis', 'treatment', 'health', 'hospital', 'prescription']
    if any(keyword in text.lower() for keyword in medical_keywords):
        score += 2
    if '...' not in text and '!!' not in text and '??' not in text:
        score += 2
    return min(10, score)

def get_recommendations(disease):
    """Get recommendations based on disease"""
    recommendations = {
        'common': "Rest, stay hydrated, and monitor your symptoms. Consult a doctor if symptoms persist.",
        'consult': "Please consult a healthcare provider for proper diagnosis and treatment.",
        'emergency': "If symptoms are severe, seek emergency medical care immediately.",
        'specialist': "You may need to see a specialist for further evaluation."
    }
    
    # Disease-specific recommendations
    disease_recs = {
        'vocal cord polyp': "🗣️ Voice rest is recommended. Avoid speaking loudly or whispering. Consult an ENT specialist.",
        'panic disorder': "🧘 Practice deep breathing exercises. Consider therapy and consult a psychiatrist.",
        'migraine': "💆 Rest in a dark, quiet room. Stay hydrated. Consult a neurologist for persistent headaches.",
        'asthma': "💨 Use prescribed inhaler. Avoid triggers. Seek immediate help if breathing worsens.",
        'diabetes': "🍎 Monitor blood sugar levels. Follow diet plan. Consult an endocrinologist.",
        'hypertension': "❤️ Reduce salt intake. Exercise regularly. Take prescribed medications.",
        'pneumonia': "🫁 Complete full course of antibiotics. Rest and stay hydrated. Follow up with doctor.",
        'gastroenteritis': "🥣 Oral rehydration solution. BRAT diet (Bananas, Rice, Applesauce, Toast).",
        'uti': "💊 Complete antibiotic course. Drink plenty of water. Avoid caffeine and alcohol.",
        'anemia': "🥩 Iron-rich foods (spinach, red meat). Vitamin C supplements. Consult physician.",
        'arthritis': "🦴 Gentle exercise. Apply heat/cold therapy. Anti-inflammatory medications.",
        'sinusitis': "👃 Nasal irrigation. Warm compresses. Decongestants as needed.",
        'bronchitis': "🫁 Rest and fluids. Use humidifier. Avoid smoke and irritants.",
        'allergic rhinitis': "🌿 Antihistamines. Avoid allergens. Nasal sprays as prescribed.",
        'gastritis': "🍚 Small frequent meals. Avoid spicy foods. Antacids for relief.",
        'insomnia': "😴 Maintain sleep schedule. Avoid screens before bed. Practice relaxation.",
        'depression': "💙 Seek therapy. Medication if prescribed. Stay connected with loved ones.",
        'anxiety': "🧘 Deep breathing. Mindfulness. Professional help if needed.",
        'covid19': "😷 Isolate immediately. Monitor oxygen levels. Seek emergency for breathing difficulty.",
        'flu': "🤒 Rest and hydration. Antiviral medications if early. Fever reducers."
    }
    
    disease_lower = disease.lower()
    for key, rec in disease_recs.items():
        if key in disease_lower:
            return rec
    
    # Default recommendations based on match confidence
    return "👨‍⚕️ " + recommendations['consult'] + " Get plenty of rest and stay hydrated."

def match_symptoms_to_disease(user_symptoms):
    """Find disease that matches the given symptoms"""
    best_match = None
    best_score = 0
    matched_symptoms = []
    
    # Limit search for better performance
    sample_df = df.sample(min(5000, len(df))) if len(df) > 5000 else df
    
    for idx, row in sample_df.iterrows():
        disease = row['diseases']
        score = 0
        disease_symptoms = []
        
        for symptom in user_symptoms:
            symptom_col = symptom.lower().replace(' ', '_')
            if symptom_col in symptom_cols:
                if row[symptom_col] == 1:
                    score += 1
                    disease_symptoms.append(symptom)
        
        if score > best_score and score > 0:
            best_score = score
            best_match = disease
            matched_symptoms = disease_symptoms
    
    return best_match, best_score, matched_symptoms

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    user_input = request.form.get('symptoms', '')
    symptoms_list = [s.strip().lower() for s in user_input.split(',') if s.strip()]
    
    if len(symptoms_list) == 0:
        return jsonify({
            'type': 'no_symptoms',
            'message': "❌ You didn't enter any symptoms. Please consult a doctor if you're feeling unwell.",
            'advice': "🛌 Rest and stay hydrated.",
            'fluency_score': 8
        })
    
    elif len(symptoms_list) == 1:
        responses = [
            f"📍 You reported: {symptoms_list[0]}\n\n✅ This appears to be a minor symptom. Take rest and over-the-counter medication if needed.\n💊 Recommendation: Paracetamol or Ibuprofen as needed.\n⏰ It should resolve within 2-3 days.\n⚠️ Consult a doctor if it persists beyond 3 days.",
            f"Symptom detected: {symptoms_list[0]}\n\n🔹 This is likely not a serious health issue.\n💊 Take appropriate medication and rest.\n🥤 Stay hydrated and monitor your condition.\n📅 Follow up with a doctor only if symptoms worsen.",
            f"✓ Symptom: {symptoms_list[0]}\n\n🟢 SEVERITY: Mild\n💊 Action: Take tablet (Paracetamol 500mg) as needed\n🛌 Rest is recommended\n📞 No immediate medical consultation needed\n✨ Should resolve with self-care"
        ]
        message = random.choice(responses)
        return jsonify({
            'type': 'minor',
            'symptom': symptoms_list[0],
            'message': message,
            'advice': "🩹 Self-care with rest and medication. Monitor symptoms for 2-3 days.",
            'fluency_score': evaluate_fluency(message)
        })
    
    else:
        disease, score, matched_symptoms = match_symptoms_to_disease(symptoms_list)
        
        if disease and score >= 1:
            disease_name = disease.replace('_', ' ').title()
            recommendations = get_recommendations(disease_name)
            
            # Highlight the disease in the message
            templates = [
                f"⚠️ MULTIPLE SYMPTOMS DETECTED: {', '.join(matched_symptoms[:5])}\n\n🏥 Based on your symptoms, you may have: <span class='disease-highlight'>{disease_name}</span>\n\n📋 Match confidence: {score}/{len(symptoms_list)} symptoms matched\n\n👨‍⚕️ RECOMMENDATION: Please consult a healthcare provider for proper diagnosis and treatment.\n🚫 Do not self-medicate.",
                f"🔴 ALERT: Multiple symptoms reported!\n\nSymptoms: {', '.join(matched_symptoms[:5])}\n\n🎯 Possible condition: <span class='disease-highlight'>{disease_name}</span>\n\n⚠️ This requires medical attention.\n📞 Please schedule an appointment with a doctor.\n💊 Do not take any medication without prescription.",
                f"🏥 MEDICAL CONSULTATION RECOMMENDED\n\nYour symptoms ({', '.join(matched_symptoms[:5])}) suggest: <span class='disease-highlight'>{disease_name}</span>\n\n📊 Symptom match: {score} out of {len(symptoms_list)}\n\n👩‍⚕️ Action Required: Visit a healthcare provider for:\n   - Proper diagnosis\n   - Prescribed medication\n   - Treatment plan\n\n🚨 If symptoms are severe, seek emergency care."
            ]
            message = random.choice(templates)
            
            return jsonify({
                'type': 'serious',
                'disease': disease_name,
                'matched_symptoms': matched_symptoms,
                'score': score,
                'total_symptoms': len(symptoms_list),
                'message': message,
                'advice': recommendations,
                'fluency_score': evaluate_fluency(message),
                'confidence': int((score / len(symptoms_list)) * 100)
            })
        else:
            message = f"⚠️ You reported {len(symptoms_list)} symptoms: {', '.join(symptoms_list)}\n\n❓ No specific disease match found in our database.\n\n👨‍⚕️ Since you have multiple symptoms, we recommend consulting a healthcare provider for proper evaluation.\n📝 Keep track of your symptoms and when they started."
            return jsonify({
                'type': 'unclear',
                'symptoms': symptoms_list,
                'message': message,
                'advice': "🏥 Medical consultation recommended. Keep a symptom diary and consult a doctor.",
                'fluency_score': evaluate_fluency(message)
            })

if __name__ == '__main__':
    app.run(debug=True)