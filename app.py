from flask import Flask, render_template, request, jsonify
import os
import base64
import google.generativeai as genai
import json # Import the json library

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Gemini API
# IMPORTANT: Replace 'YOUR_GEMINI_API_KEY' with your actual Gemini API key
genai.configure(api_key='AIzaSyB_RFI7WlcUZJLC1eVGjrjZyUH_wX74RVo')

# System message to guide Gemini's personality
SYSTEM_PROMPT = (
    "You are ATOM, a compassionate and emotionally intelligent AI health assistant. "
    "You speak in a calm, caring tone, using empathetic language. You provide medical diagnosis, "
    "but you guide users supportively. Always address the user with emotional understanding, positivity, "
    "and encouragement. Keep track of the conversation history provided." # Added note about history
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    prompt = request.form.get('prompt', '')
    image_file = request.files.get('image')
    history_json = request.form.get('history', '[]') # Get history JSON string

    # --- MODIFICATION START: Process History ---
    try:
        # Parse the history received from the frontend
        chat_history = json.loads(history_json)
        # Basic validation: ensure it's a list
        if not isinstance(chat_history, list):
            chat_history = []
    except json.JSONDecodeError:
        print("Warning: Could not decode chat history JSON.")
        chat_history = []
    # --- MODIFICATION END ---


    # Prepare parts for the *current* user message
    current_user_parts = []
    if prompt:
        current_user_parts.append({'text': prompt})
    # Add default text if only image is present (optional, based on model needs)
    elif image_file and not prompt:
         current_user_parts.append({'text': 'Describe this image.'})


    if image_file:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        image_file.save(image_path)
        try:
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            current_user_parts.append({
                'inline_data': {
                    'mime_type': image_file.mimetype,
                    'data': image_data
                }
            })
            # os.remove(image_path) # Optional cleanup
        except Exception as e:
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500

    # --- MODIFICATION START: Construct full contents including history ---
    # The full conversation history including the latest user message
    contents = chat_history + [{'role': 'user', 'parts': current_user_parts}]
    # --- MODIFICATION END ---


    try:
        model_name = 'gemini-2.0-flash'
        model = genai.GenerativeModel(
            model_name,
            system_instruction=SYSTEM_PROMPT
        )

        # Generate content using the full conversation history
        response = model.generate_content(contents) # Pass the combined history + current message

        if not response.parts:
             response_text = "I received your message, but I don't have a specific response for that right now. Could you try rephrasing?"
        else:
             response_text = response.text.strip()

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        error_message = str(e)
        return jsonify({'error': f'Could not get response from AI: {error_message}'}), 500

    return jsonify({'response_text': response_text})

if __name__ == '__main__':
    app.run(debug=True)