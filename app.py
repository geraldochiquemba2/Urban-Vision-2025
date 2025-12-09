import os
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from groq import Groq

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

VALID_AREAS = [
    "Maianga", "Samba", "Rangel", "Ingombota", "Viana", "Cacuaco",
    "Benguela", "Lobito", "Catumbela",
    "Huambo", "Caála",
    "Lubango", "Matala",
    "Cabinda",
    "Namibe", "Tômbwa",
    "Malanje",
    "Sumbe", "Porto Amboim",
    "N'dalatando",
    "Uíge",
    "M'banza Congo",
    "Dundo",
    "Saurimo",
    "Luena",
    "Kuito",
    "Menongue",
    "Ondjiva",
    "Caxito",
    "Luanda", "Angola"
]
MAX_MESSAGE_LENGTH = 2000
MAX_YEARS = 50

def sanitize_text(text, max_length=MAX_MESSAGE_LENGTH):
    if not isinstance(text, str):
        return ""
    text = text.strip()[:max_length]
    text = re.sub(r'[<>{}]', '', text)
    return text

def validate_number(value, min_val, max_val, default):
    try:
        num = float(value)
        if min_val <= num <= max_val:
            return num
        return default
    except (TypeError, ValueError):
        return default

def validate_area_name(area):
    area = sanitize_text(area, 50)
    if area in VALID_AREAS:
        return area
    for valid in VALID_AREAS:
        if valid.lower() == area.lower():
            return valid
    if area and len(area) > 0:
        return area
    return "Angola"

SYSTEM_PROMPT = """Você é um assistente especializado em Visão Urbana e Gestão Ambiental para Angola. 
Seu nome é "Urban Vision AI". Você tem conhecimento sobre todas as 18 províncias de Angola.

Você tem conhecimento profundo sobre:

1. **Monitoramento Ambiental**:
   - Dióxido de Carbono (CO2): níveis, impactos na saúde e no clima
   - Zonas de Calor: ilhas de calor urbanas, causas e efeitos
   - Qualidade do ar: PM2.5, SO2 e outros poluentes

2. **Previsão e Análise com IA**:
   - Crescimento das zonas de calor ao longo dos anos
   - Previsão de aumento de temperatura em áreas específicas
   - Tendências climáticas urbanas

3. **Recomendações de Melhoria**:
   - Restabelecimento de áreas verdes: tipos de plantas, quantidade necessária
   - Tempo de recuperação da vegetação
   - Estratégias de mitigação do calor urbano

4. **Planejamento Urbano e Industrial**:
   - Identificação de zonas industriais
   - Restrições para novas construções industriais
   - Zoneamento sustentável

Dados baseados em medições reais (IQAir 2024, World Bank):
Nota: Angola tem média PM2.5 de 11-13 µg/m³ nas principais cidades.

**Luanda (Capital) - PM2.5 médio: 13 µg/m³:**
- Maianga: PM2.5=14, SO2=5, Vegetação=18%, Temp média=27°C
- Samba: PM2.5=12, SO2=4, Vegetação=22%, Temp média=26°C
- Rangel: PM2.5=16, SO2=6, Vegetação=12%, Temp média=28°C (alta densidade)
- Ingombota: PM2.5=13, SO2=4, Vegetação=25%, Temp média=26°C
- Viana: PM2.5=15, SO2=6, Vegetação=15%, Temp média=27°C (zona industrial)
- Cacuaco: PM2.5=14, SO2=5, Vegetação=20%, Temp média=27°C (refinaria)

**Benguela - PM2.5 médio: 12 µg/m³:**
- Benguela: PM2.5=12, SO2=3, Vegetação=28%, Temp média=24°C
- Lobito: PM2.5=13, SO2=4, Vegetação=24%, Temp média=25°C
- Catumbela: PM2.5=14, SO2=5, Vegetação=30%, Temp média=25°C

**Huambo (Planalto Central) - PM2.5 médio: 13 µg/m³:**
- Huambo: PM2.5=13, SO2=3, Vegetação=35%, Temp média=19°C (altitude 1700m)
- Caála: PM2.5=11, SO2=2, Vegetação=42%, Temp média=18°C

**Huíla - PM2.5 médio: 12 µg/m³:**
- Lubango: PM2.5=12, SO2=3, Vegetação=38%, Temp média=18°C (altitude 1760m)
- Matala: PM2.5=11, SO2=2, Vegetação=32%, Temp média=22°C

**Cabinda:** PM2.5=14, SO2=7, Vegetação=85%, Temp média=26°C (floresta tropical + petróleo)

**Namibe (Deserto):**
- Namibe: PM2.5=8, SO2=2, Vegetação=5%, Temp média=21°C
- Tômbwa: PM2.5=7, SO2=1, Vegetação=3%, Temp média=20°C

**Outras Capitais Provinciais:**
- Malanje: PM2.5=11, SO2=3, Vegetação=55%, Temp média=24°C
- Uíge: PM2.5=10, SO2=2, Vegetação=70%, Temp média=23°C
- M'banza Congo: PM2.5=9, SO2=2, Vegetação=65%, Temp média=24°C
- Dundo: PM2.5=13, SO2=5, Vegetação=60%, Temp média=25°C (mineração diamantes)
- Saurimo: PM2.5=12, SO2=4, Vegetação=58%, Temp média=24°C
- Luena: PM2.5=11, SO2=2, Vegetação=72%, Temp média=22°C (Moxico)
- Kuito: PM2.5=12, SO2=2, Vegetação=45%, Temp média=20°C
- Menongue: PM2.5=9, SO2=1, Vegetação=40%, Temp média=23°C (savana)
- Ondjiva: PM2.5=10, SO2=2, Vegetação=20%, Temp média=26°C (semiárido)

Responda sempre em português de forma clara e útil. Quando fizer previsões ou recomendações, 
seja específico e baseie-se em dados científicos sobre urbanismo sustentável."""

def get_groq_client():
    if not GROQ_API_KEY:
        return None
    return Groq(api_key=GROQ_API_KEY)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/chat', methods=['POST'])
def chat():
    client = get_groq_client()
    if not client:
        return jsonify({"error": "API do Groq não configurada. Adicione a variável GROQ_API_KEY."}), 500
    
    data = request.json or {}
    user_message = sanitize_text(data.get('message', ''))
    
    if not user_message:
        return jsonify({"error": "Mensagem não pode estar vazia."}), 400
    
    history = data.get('history', [])
    if not isinstance(history, list):
        history = []
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-10:]:
        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
            sanitized_content = sanitize_text(msg["content"])
            if msg["role"] in ["user", "assistant"] and sanitized_content:
                messages.append({"role": msg["role"], "content": sanitized_content})
    messages.append({"role": "user", "content": user_message})
    
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024
        )
        response = chat_completion.choices[0].message.content
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": "Erro ao processar sua solicitação. Tente novamente."}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_area():
    client = get_groq_client()
    if not client:
        return jsonify({"error": "API do Groq não configurada."}), 500
    
    data = request.json or {}
    area_name = validate_area_name(data.get('area', 'Luanda'))
    pm25 = validate_number(data.get('pm25'), 0, 500, 20)
    so2 = validate_number(data.get('so2'), 0, 100, 5)
    vegetation = validate_number(data.get('vegetation'), 0, 100, 30)
    
    analysis_prompt = f"""Analise os dados ambientais da área {area_name}:
- PM2.5: {pm25} μg/m³
- SO2: {so2} ppm
- Vegetação: {vegetation}%

Forneça:
1. Avaliação da qualidade do ar
2. Previsão de crescimento de zona de calor nos próximos 5-10 anos
3. Recomendações específicas de plantas para restabelecimento verde
4. Estimativa de tempo para recuperação ambiental
5. Se é adequado para novas indústrias ou não

Seja específico e científico nas recomendações."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": analysis_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1500
        )
        response = chat_completion.choices[0].message.content
        return jsonify({"analysis": response})
    except Exception as e:
        return jsonify({"error": "Erro ao analisar a área. Tente novamente."}), 500

@app.route('/api/predict', methods=['POST'])
def predict_future():
    client = get_groq_client()
    if not client:
        return jsonify({"error": "API do Groq não configurada."}), 500
    
    data = request.json or {}
    area_name = validate_area_name(data.get('area', 'Luanda'))
    years = int(validate_number(data.get('years'), 1, MAX_YEARS, 10))
    current_temp = validate_number(data.get('current_temp'), -20, 60, 28)
    vegetation = validate_number(data.get('vegetation'), 0, 100, 30)
    
    prediction_prompt = f"""Para a área {area_name} com temperatura atual média de {current_temp}°C e {vegetation}% de vegetação:

Faça previsões para os próximos {years} anos:
1. Aumento esperado de temperatura
2. Expansão das zonas de calor
3. Impacto na qualidade de vida
4. Cenário com intervenção verde vs sem intervenção

Forneça números e percentuais específicos baseados em tendências urbanas."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prediction_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1200
        )
        response = chat_completion.choices[0].message.content
        return jsonify({"prediction": response})
    except Exception as e:
        return jsonify({"error": "Erro ao gerar previsão. Tente novamente."}), 500

@app.route('/api/recommend', methods=['POST'])
def recommend_restoration():
    client = get_groq_client()
    if not client:
        return jsonify({"error": "API do Groq não configurada."}), 500
    
    data = request.json or {}
    area_name = validate_area_name(data.get('area', 'Luanda'))
    area_size = validate_number(data.get('area_size'), 1, 1000000, 1000)
    current_vegetation = validate_number(data.get('vegetation'), 0, 100, 30)
    target_vegetation = validate_number(data.get('target'), 0, 100, 60)
    
    recommend_prompt = f"""Para a área {area_name} com {area_size}m² e vegetação atual de {current_vegetation}%, 
queremos atingir {target_vegetation}% de cobertura verde.

Forneça um plano detalhado:
1. Quantidade de árvores e plantas necessárias (números específicos)
2. Tipos de espécies recomendadas para o clima de Luanda (tropical)
3. Cronograma de plantio
4. Tempo estimado para atingir a meta
5. Benefícios esperados (redução de temperatura, melhoria do ar)
6. Custos aproximados de implementação"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": recommend_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1500
        )
        response = chat_completion.choices[0].message.content
        return jsonify({"recommendation": response})
    except Exception as e:
        return jsonify({"error": "Erro ao gerar recomendações. Tente novamente."}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "groq_configured": GROQ_API_KEY is not None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
