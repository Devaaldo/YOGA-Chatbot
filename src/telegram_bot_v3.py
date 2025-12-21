import os
import re
import json
import pickle
import random
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# CONFIGURATION

# Telegram Bot Token (load from environment variable)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')

# Model paths
MODEL_DIR = '../models'
FEATURE_DIR = '../data/features'

GREETING_DETECTOR_PATH = os.path.join(MODEL_DIR, 'greeting_detector.pkl')
MAIN_CLASSIFIER_PATH = os.path.join(MODEL_DIR, 'svm_model.pkl')
TFIDF_GREETING_PATH = os.path.join(FEATURE_DIR, 'tfidf_greeting.pickle')
TFIDF_MAIN_PATH = os.path.join(FEATURE_DIR, 'tfidf_vectorizer.pickle')
LABEL_ENCODER_PATH = os.path.join(FEATURE_DIR, 'label_encoder.pickle')

# Hybrid pipeline config
CONFIDENCE_THRESHOLD = 0.7
WORD_COUNT_THRESHOLD = 3

# LOAD INTENTS DATA

INTENTS_PATH = os.path.join('../data', 'intents_diy_full.json')

# Load intents for responses
with open(INTENTS_PATH, 'r', encoding='utf-8') as f:
    intents_data = json.load(f)

# Create intent -> responses mapping
intent_responses = {}
for intent in intents_data['intents']:
    tag = intent['tag']
    responses = intent.get('responses', [])
    intent_responses[tag] = responses

print("=" * 80)
print("LOADING YOGA CHATBOT")
print("=" * 80)
print(f"✓ Loaded intents: {len(intent_responses)} intents")

# LOAD MODELS

# Load Binary GreetingDetector
with open(GREETING_DETECTOR_PATH, 'rb') as f:
    greeting_detector = pickle.load(f)
print(f"✓ Loaded: {GREETING_DETECTOR_PATH}")

# Load Main SVM Classifier
with open(MAIN_CLASSIFIER_PATH, 'rb') as f:
    main_classifier = pickle.load(f)
print(f"✓ Loaded: {MAIN_CLASSIFIER_PATH}")

# Load TF-IDF vectorizers
with open(TFIDF_GREETING_PATH, 'rb') as f:
    tfidf_greeting = pickle.load(f)
print(f"✓ Loaded: {TFIDF_GREETING_PATH}")

with open(TFIDF_MAIN_PATH, 'rb') as f:
    tfidf_main = pickle.load(f)
print(f"✓ Loaded: {TFIDF_MAIN_PATH}")

# Load label encoder
with open(LABEL_ENCODER_PATH, 'rb') as f:
    label_encoder = pickle.load(f)
print(f"✓ Loaded: {LABEL_ENCODER_PATH}")

print(f"\nTotal classes: {len(label_encoder.classes_)}")

# Load stemmer
stemmer_factory = StemmerFactory()
stemmer = stemmer_factory.create_stemmer()
print("✓ Loaded: Sastrawi Stemmer")

# Define greeting classes
GREETING_INTENTS = ['goodbye', 'greeting', 'pagi', 'siang', 'sore', 'malam']
GREETING_INDICES = [i for i, cls in enumerate(label_encoder.classes_) if cls in GREETING_INTENTS]

print(f"\nGreeting intents: {GREETING_INTENTS}")
print("=" * 80)
print()

# PREPROCESSING

def preprocess_text(text):
    """
    Preprocess user input text

    Args:
        text: Raw input text

    Returns:
        Preprocessed text (lowercased, cleaned, stemmed)
    """
    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)

    # Remove mentions and hashtags
    text = re.sub(r'@\w+|#\w+', '', text)

    # Remove punctuation except spaces
    text = re.sub(r'[^\w\s]', '', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Stemming
    text = stemmer.stem(text)

    return text

# HYBRID PREDICTION PIPELINE

def predict_intent_hybrid(text):
    """
    Hybrid 3-Stage Prediction Pipeline

    Stage 0: Rule-based filter
    - If word count > 3 → Skip to MainClassifier

    Stage 1: Binary GreetingDetector
    - Classify: greeting vs non-greeting
    - Get probability/confidence

    Stage 2: Conditional Classification
    - If GREETING (confidence >= threshold):
      → Get decision scores from MainClassifier
      → Only pick from 6 greeting classes
    - If NON-GREETING (confidence < threshold):
      → Use MainClassifier normally

    Args:
        text: Preprocessed input text

    Returns:
        predicted_intent: Intent class name (string)
    """
    # Stage 0: Rule-based filter
    word_count = len(text.split())

    if word_count > WORD_COUNT_THRESHOLD:
        # Long text → likely location query → Skip to MainClassifier
        X_main = tfidf_main.transform([text]).toarray()
        pred_idx = main_classifier.predict(X_main)[0]
        return label_encoder.classes_[pred_idx]

    # Stage 1: Binary GreetingDetector
    X_greeting = tfidf_greeting.transform([text]).toarray()
    greeting_proba = greeting_detector.predict_proba(X_greeting)[0]

    # greeting_proba[1] = probability of being a greeting
    confidence = greeting_proba[1]

    # Stage 2: Conditional Classification
    X_main = tfidf_main.transform([text]).toarray()

    if confidence >= CONFIDENCE_THRESHOLD:
        # GREETING detected → Only pick from 6 greeting classes
        all_scores = main_classifier.decision_function(X_main)[0]

        # Only consider greeting classes
        greeting_scores = [(idx, all_scores[idx]) for idx in GREETING_INDICES]
        pred_idx = max(greeting_scores, key=lambda x: x[1])[0]

        return label_encoder.classes_[pred_idx]
    else:
        # NON-GREETING → Use MainClassifier normally
        pred_idx = main_classifier.predict(X_main)[0]
        return label_encoder.classes_[pred_idx]

# RESPONSE GENERATOR

def generate_response(intent):
    """
    Generate response based on predicted intent using responses from intents JSON

    Args:
        intent: Predicted intent class name

    Returns:
        Response message (string)
    """
    # Get responses from intents data
    if intent in intent_responses and intent_responses[intent]:
        # Pick random response from available responses
        response = random.choice(intent_responses[intent])

        # Check if response is empty or only contains emoji header
        if not response or response.strip() == '📍' or response.strip() == '':
            # Fallback message for empty responses
            location_name = intent.replace('_', ' ').replace('kecamatan ', '').replace('kabupaten ', '').title()
            return (
                f"📍 Maaf, saat ini belum ada data wisata untuk {location_name}.\n\n"
                "Coba tanya lokasi lain di Yogyakarta seperti:\n"
                "• Kabupaten Bantul\n"
                "• Kabupaten Sleman\n"
                "• Kabupaten Gunungkidul\n"
                "• Kabupaten Kulonprogo\n"
                "• Kota Yogyakarta"
            )

        return response

    # Fallback if intent not found in responses
    intent_display = intent.replace('_', ' ').title()
    return f"📍 Intent terdeteksi: *{intent_display}*\n\nTerima kasih atas pertanyaan Anda tentang wisata Yogyakarta!"

# TELEGRAM BOT HANDLERS

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = (
        "👋 *Halo! Selamat datang di YOGA Chatbot!*\n\n"
        "🤖 *YOGA* (Yogyakarta Guide Assistant)\n"
        "Chatbot pemandu wisata Yogyakarta.\n\n"
        "📍 *Fitur:*\n"
        "• Deteksi intent greeting (pagi/siang/sore/malam)\n"
        "• Rekomendasi wisata berdasarkan lokasi kecamatan/kabupaten di Daerah Istimewa Yogyakarta\n"
        "💬 *Cara Pakai:*\n"
        "Ketik pertanyaan Anda, contoh:\n"
        "• _Selamat pagi_\n"
        "• _Wisata di Bantul_\n"
        "• _Tempat hits di Sleman_\n"
        "• _Pantai di Gunungkidul_\n\n"
        "📌 Ketik /help untuk bantuan lebih lanjut."
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = (
        "ℹ️ *YOGA Chatbot - Bantuan*\n\n"
        "🤖 *Tentang YOGA:*\n"
        "YOGA (YOgyakarta Guide Assistant) adalah chatbot AI yang membantu Anda "
        "menemukan informasi wisata di Yogyakarta.\n\n"
        "💬 *Perintah:*\n"
        "/start - Mulai percakapan\n"
        "/help - Tampilkan bantuan\n"
        "/about - Info tentang bot\n\n"
        "📝 *Contoh Pertanyaan:*\n"
        "• Greeting: _selamat pagi, halo, hai_\n"
        "• Lokasi: _wisata bantul, tempat di sleman_\n"
        "• Spesifik: _pantai gunungkidul, candi prambanan_\n\n"
        "🔧 *Teknologi:*\n"
        "• Hybrid 3-Stage Pipeline\n"
        "• Binary GreetingDetector (SVM)\n"
        "• 88-class MainClassifier (SVM)\n"
        "• TF-IDF Feature Extraction\n"
    )
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    about_message = (
        "ℹ️ *YOGA Chatbot*\n\n"
        "🤖 *Yogyakarta Guide Assistant*\n"
        "🏗️ *Architecture:*\n"
        "• Stage 0: Rule-based Filter (word count)\n"
        "• Stage 1: Binary GreetingDetector\n"
        "• Stage 2: Conditional MainClassifier\n\n"
        "📊 *Model Stats:*\n"
        f"• Total Intent Classes: {len(label_encoder.classes_)}\n"
        f"• Greeting Intents: {len(GREETING_INTENTS)}\n"
        "• Algorithm: Support Vector Machine (SVM)\n"
        "• Features: TF-IDF (dual vectorizers)\n\n"
        "👨‍💻 *Developers: Muhammad Akbar Pradana, Maulidiyah Hasanah, Ridho Fathuriza Susilo, Adhitya Yahya Lestaluhu*\n"
        "YOGA Team\n"
    )
    await update.message.reply_text(about_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    user_message = update.message.text
    user_id = update.message.from_user.id

    # Preprocess
    processed_text = preprocess_text(user_message)

    # Predict intent using hybrid pipeline
    predicted_intent = predict_intent_hybrid(processed_text)

    # Generate response
    response = generate_response(predicted_intent)

    # Log
    print(f"[User {user_id}] {user_message}")
    print(f"[Processed] {processed_text}")
    print(f"[Intent] {predicted_intent}")
    print(f"[Response] {response[:50]}...")
    print()

    # Send response
    await update.message.reply_text(response, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    print(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "Maaf, terjadi kesalahan. Silakan coba lagi atau hubungi admin."
        )

# MAIN

def main():
    """Run the Telegram bot"""
    print("=" * 80)
    print("STARTING YOGA CHATBOT")
    print("=" * 80)
    print()

    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('about', about_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Start bot
    print("✓ Bot is running...")
    print("✓ Press Ctrl+C to stop")
    print()

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
