import os
import sys
import json
import logging
import pickle
from datetime import datetime
from pathlib import Path

import numpy as np
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from gensim.models import Word2Vec
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import tensorflow as tf
from tensorflow.keras.models import load_model
from dotenv import load_dotenv

# Setup paths
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

# Load environment variables
load_dotenv(BASE_DIR / '.env')

# CONFIGURATION

class Config:
    # Bot settings
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Load from .env file

    # Model settings
    MODEL_PATH = BASE_DIR / "models" / "yoga_lstm_best.h5"
    LABEL_ENCODER_PATH = BASE_DIR / "data" / "features" / "label_encoder.pickle"
    WORD2VEC_PATH = BASE_DIR / "data" / "features" / "word2vec.model"
    FEATURE_INFO_PATH = BASE_DIR / "data" / "features" / "feature_extraction_info.json"
    INTENTS_PATH = BASE_DIR / "data" / "intents_diy_full.json"

    # Prediction settings
    CONFIDENCE_THRESHOLD = 0.5  
    TOP_N_SUGGESTIONS = 3
    SHOW_CONFIDENCE = False 

    # Logging settings
    LOG_DIR = BASE_DIR / "logs"
    PREDICTIONS_LOG = LOG_DIR / "predictions.jsonl"
    CONVERSATIONS_LOG = LOG_DIR / "conversations.jsonl"

# SETUP LOGGING

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create log directories
Config.LOG_DIR.mkdir(exist_ok=True)

# YOGA CHATBOT MODEL

class YOGAChatbot:
    def __init__(self):
        """Initialize YOGA Chatbot dengan LSTM model"""
        logger.info("Loading YOGA Chatbot...")

        # Load model
        logger.info(f"Loading model from {Config.MODEL_PATH}")
        self.model = load_model(str(Config.MODEL_PATH))
        logger.info(f"Model loaded from {Config.MODEL_PATH}")

        # Load label encoder
        with open(Config.LABEL_ENCODER_PATH, 'rb') as f:
            self.label_encoder = pickle.load(f)
        logger.info(f"Loaded label encoder: {len(self.label_encoder.classes_)} classes")

        # Load Word2Vec model
        self.w2v_model = Word2Vec.load(str(Config.WORD2VEC_PATH))
        logger.info("Loaded Word2Vec model")

        # Load feature info
        with open(Config.FEATURE_INFO_PATH, 'r', encoding='utf-8') as f:
            self.feature_info = json.load(f)
        self.max_length = self.feature_info['max_length']
        self.vector_size = self.feature_info['vector_size']

        logger.info(f"Max length: {self.max_length}, Vector size: {self.vector_size}")

        # Load intents and responses
        with open(Config.INTENTS_PATH, 'r', encoding='utf-8') as f:
            intents_data = json.load(f)

        # Create response mapping
        self.responses = {}
        for intent in intents_data['intents']:
            self.responses[intent['tag']] = intent['responses']

        logger.info(f"Loaded {len(self.responses)} intent responses")

        # Initialize preprocessing tools
        self.stemmer = StemmerFactory().create_stemmer()
        self.stopword_remover = StopWordRemoverFactory().create_stop_word_remover()

        logger.info("YOGA Chatbot ready!")

    def preprocess_text(self, text):
        """Preprocess user input text"""
        import re
        # Lowercase
        text = text.lower()
        # Remove special characters (same as Complete notebook)
        text = re.sub(r'[^a-z\s]', '', text)
        # Remove extra spaces
        text = ' '.join(text.split())
        # Remove stopwords
        text = self.stopword_remover.remove(text)
        # Stem
        text = self.stemmer.stem(text)
        # Tokenize
        tokens = text.split()
        return tokens

    def get_sequence_vector(self, tokens):
        """Convert tokens to sequence vector"""
        seq_vectors = []
        for word in tokens[:self.max_length]:
            if word in self.w2v_model.wv:
                seq_vectors.append(self.w2v_model.wv[word])
            else:
                seq_vectors.append(np.zeros(self.vector_size))

        # Pad
        while len(seq_vectors) < self.max_length:
            seq_vectors.append(np.zeros(self.vector_size))

        return np.array(seq_vectors)

    def predict(self, text):
        """
        Predict intent from user text

        Returns:
            dict with keys:
                - intent: predicted intent
                - confidence: confidence score
                - top_3: list of (intent, confidence) tuples
                - needs_clarification: bool
        """
        # Preprocess
        tokens = self.preprocess_text(text)

        # Get sequence vector
        seq_vec = self.get_sequence_vector(tokens)
        seq_vec = seq_vec.reshape(1, self.max_length, self.vector_size)

        # Predict
        pred_prob = self.model.predict(seq_vec, verbose=0)[0]
        pred_class = np.argmax(pred_prob)
        confidence = float(pred_prob[pred_class])

        # Get intent label
        intent = self.label_encoder.classes_[pred_class]

        # Get top 3 predictions
        top_3_idx = np.argsort(pred_prob)[-Config.TOP_N_SUGGESTIONS:][::-1]
        top_3 = [(self.label_encoder.classes_[i], float(pred_prob[i])) for i in top_3_idx]

        # Check if needs clarification
        needs_clarification = confidence < Config.CONFIDENCE_THRESHOLD

        return {
            'intent': intent,
            'confidence': confidence,
            'top_3': top_3,
            'needs_clarification': needs_clarification
        }

    def get_response(self, intent):
        """Get response for intent"""
        if intent in self.responses:
            responses = self.responses[intent]
            # Return first response (or random in future)
            return responses[0] if responses else "Maaf, saya belum punya jawaban untuk itu."
        return "Maaf, saya belum punya jawaban untuk itu."

    def get_response_preview(self, intent, max_length=60):
        """Get short preview of response for display"""
        response = self.get_response(intent)
        if len(response) > max_length:
            return response[:max_length] + "..."
        return response

# LOGGING UTILITIES

class PredictionLogger:
    """Log all predictions for monitoring and retraining"""

    @staticmethod
    def log_prediction(user_id, username, user_message, prediction_result):
        """Log prediction to JSONL file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'username': username,
            'user_message': user_message,
            'predicted_intent': prediction_result['intent'],
            'confidence': prediction_result['confidence'],
            'top_3': prediction_result['top_3'],
            'needs_clarification': prediction_result['needs_clarification']
        }

        with open(Config.PREDICTIONS_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    @staticmethod
    def log_conversation(user_id, username, message, response, intent):
        """Log full conversation for analysis"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'username': username,
            'user_message': message,
            'bot_response': response,
            'intent': intent
        }

        with open(Config.CONVERSATIONS_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

# INITIALIZE CHATBOT

chatbot = YOGAChatbot()

# TELEGRAM BOT HANDLERS

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    welcome_message = f"""
Halo {user.first_name}! Selamat datang di YOGA! 👋

*YOGA (YOgyakarta Guide Assistant)*
Chatbot rekomendasi wisata Yogyakarta berbasis AI! 🏛️

*Saya bisa membantu:*
✨ Rekomendasi wisata terbaik di Yogyakarta
📍 Wisata berdasarkan Provinsi DIY
🏙️ Wisata per Kabupaten (Sleman, Bantul, Gunungkidul, Kulonprogo)
🗺️ Wisata per Kecamatan (92 kecamatan)
⏰ Info jam buka & rating tempat wisata

*Contoh pertanyaan:*
- "Rekomendasi wisata di Jogja"
- "Tempat wisata di Sleman"
- "Wisata di kecamatan Prambanan"
- "Dimana tempat bagus buat liburan di Bantul?"

Ayo mulai! Ketik pertanyaan Anda 🚀
"""
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = """
*Bantuan YOGA Chatbot* 📚

*Perintah tersedia:*
/start - Mulai percakapan
/help - Tampilkan bantuan ini

*Cara menggunakan:*
Ketik pertanyaan tentang wisata Yogyakarta!

*Contoh pertanyaan:*
🌟 "Rekomendasi wisata di Jogja"
🏙️ "Tempat wisata di Sleman"
🏛️ "Wisata di Bantul"
🗺️ "Wisata kecamatan Prambanan"
🏖️ "Tempat liburan di Gunungkidul"
🎯 "Destinasi wisata Kulonprogo"

*Tips:*
✅ Sebutkan nama wilayah (Kabupaten/Kecamatan)
✅ Gunakan kata "wisata", "rekomendasi", "tempat"
✅ Tanya spesifik untuk hasil lebih akurat

Selamat berwisata! 🚀
"""
    await update.message.reply_text(
        help_message,
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    user = update.effective_user
    user_message = update.message.text

    logger.info(f"User {user.username} ({user.id}): {user_message}")

    # Predict intent
    prediction = chatbot.predict(user_message)

    # Log prediction
    PredictionLogger.log_prediction(
        user.id,
        user.username,
        user_message,
        prediction
    )

    # Check if needs clarification
    if prediction['needs_clarification']:
        # Low confidence - show general help
        help_message = """
Maaf, saya kurang memahami pertanyaan Anda. 🤔

Saya bisa membantu rekomendasi wisata di:
📍 *Provinsi DIY* - wisata umum Yogyakarta
🏙️ *Kabupaten* - Sleman, Bantul, Gunungkidul, Kulonprogo
🗺️ *Kecamatan* - 92 kecamatan di Yogyakarta

*Contoh pertanyaan yang benar:*
✅ "Rekomendasi wisata di Jogja"
✅ "Tempat wisata di Sleman"
✅ "Wisata di kecamatan Prambanan"
✅ "Dimana tempat bagus di Bantul?"

Atau ketik /help untuk panduan lengkap! 📚
"""
        await update.message.reply_text(help_message)

        # Store for later
        context.user_data['last_prediction'] = prediction
        context.user_data['last_message'] = user_message

    else:
        # High confidence - give response
        intent = prediction['intent']
        response = chatbot.get_response(intent)

        # Send response without feedback buttons
        sent_message = await update.message.reply_text(response)

        # Log conversation
        PredictionLogger.log_conversation(
            user.id,
            user.username,
            user_message,
            response,
            intent
        )

        # Store for later use
        context.user_data['last_message_id'] = sent_message.message_id
        context.user_data['last_prediction'] = prediction
        context.user_data['last_message'] = user_message

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.message:
        await update.message.reply_text(
            "Maaf, terjadi kesalahan. Silakan coba lagi atau hubungi admin."
        )

# MAIN

def main():
    """Start the bot"""
    logger.info("Starting YOGA Telegram Bot...")

    # Check if token is set
    if not Config.BOT_TOKEN:
        logger.error("ERROR: TELEGRAM_BOT_TOKEN not found in .env file")
        logger.error("Please create .env file and add:")
        logger.error("TELEGRAM_BOT_TOKEN=your_token_here")
        return

    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start bot
    logger.info("YOGA Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
