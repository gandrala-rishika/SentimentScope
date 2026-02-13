import pickle
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path
import logging
import re
from collections import Counter
import emoji
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

UTILS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = UTILS_DIR.parent
MODEL_DIR = BACKEND_DIR / 'models'

SENTIMENT_FLIPS = {
    'underrated': 'amazing',
    'underdog': 'winner',
    'goat': 'best',
    'banger': 'amazing song',
    'dope': 'amazing',
    'sick': 'amazing', 
    'fire': 'amazing',
    'lit': 'amazing',
    'beast': 'amazing',
    'slaps': 'amazing',
    'addicted': 'loving'
}

class SentimentAnalyzer:
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.baseline_model = None
        self.baseline_vectorizer = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.sentiment_labels = ['Negative', 'Neutral', 'Positive']
        
        self.vader_analyzer = None
        self.translator = GoogleTranslator(source='auto', target='en')
        
        self._load_models()
    
    def _load_models(self):
        transformer_path = MODEL_DIR / 'distilbert_sentiment'
        if MODEL_DIR.exists() and transformer_path.exists():
            try:
                logger.info(f"Loading transformer model from {transformer_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(str(transformer_path))
                self.model = AutoModelForSequenceClassification.from_pretrained(str(transformer_path))
                self.model = self.model.to(self.device)
                self.model.eval()
                logger.info("Transformer model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
        else:
            logger.info("Transformer model path not found. Checking Baseline or fallback.")
        
        baseline_path = MODEL_DIR / 'baseline_model.pkl'
        if MODEL_DIR.exists() and baseline_path.exists():
            try:
                logger.info(f"Loading baseline model from {baseline_path}")
                with open(baseline_path, 'rb') as f:
                    data = pickle.load(f)
                    self.baseline_vectorizer = data['vectorizer']
                    self.baseline_model = data['model']
                logger.info("Baseline model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load baseline model: {e}")

        if not self.model and not self.baseline_model:
            if VaderAnalyzer:
                self.vader_analyzer = VaderAnalyzer()
                logger.info("Local models not found or failed. Initialized VADER Sentiment Analyzer as fallback.")
            else:
                logger.error("No models available and VADER not installed. Analysis will fail.")
    
    def translate_if_needed(self, text: str) -> str:
        if not text or not text.strip():
            return text
        
        if text.isascii():
            return text
        
        try:
            return self.translator.translate(text)
        except Exception as e:
            logger.warning(f"Translation failed: {e}. Using original text.")
            return text

    def clean_text(self, text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            return ""
        
        text = text.lower()
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = emoji.demojize(text, delimiters=(' ', ' '))
        
        words = text.split()
        normalized_words = [SENTIMENT_FLIPS.get(word, word) for word in words]
        text = ' '.join(normalized_words)
        
        text = re.sub(r'[^a-zA-Z0-9\s!?.,]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze(self, text: str, use_transformer: bool = True) -> dict:
        if not text or not text.strip():
            return {
                'sentiment': 'Neutral',
                'confidence': 0.33,
                'scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33},
                'model_used': 'None'
            }
        
        translated_text = self.translate_if_needed(text)
        cleaned_text = self.clean_text(translated_text)
        
        if not cleaned_text:
            return {
                'sentiment': 'Neutral',
                'confidence': 0.33,
                'scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33},
                'model_used': 'None'
            }
        
        if use_transformer and self.model and self.tokenizer:
            try:
                return self._analyze_transformer(cleaned_text)
            except Exception as e:
                logger.warning(f"Transformer analysis failed: {e}. Falling back to baseline/VADER.")
        
        if self.baseline_model and self.baseline_vectorizer:
            try:
                return self._analyze_baseline(cleaned_text)
            except Exception as e:
                logger.warning(f"Baseline analysis failed: {e}. Falling back to VADER.")
        
        if self.vader_analyzer:
            try:
                return self._analyze_vader(cleaned_text)
            except Exception as e:
                logger.error(f"VADER analysis failed: {e}.")
        
        return {
            'sentiment': 'Neutral',
            'confidence': 0.33,
            'scores': {'negative': 0.33, 'neutral': 0.34, 'positive': 0.33},
            'model_used': 'None'
        }
    
    def _analyze_transformer(self, text: str) -> dict:
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=128,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            neg_score = probs[0][0].item()
            neu_score = probs[0][1].item()
            pos_score = probs[0][2].item()
            
            total_polarized_score = neg_score + pos_score
            
            if total_polarized_score > 0:
                if pos_score > neg_score:
                    final_sentiment_idx = 2
                    final_confidence = pos_score
                else:
                    final_sentiment_idx = 0
                    final_confidence = neg_score
            else:
                final_sentiment_idx = 0
                final_confidence = 0.5
            
        return {
            'sentiment': self.sentiment_labels[final_sentiment_idx],
            'confidence': float(final_confidence),
            'scores': {
                'negative': float(neg_score),
                'neutral': 0.0,
                'positive': float(pos_score)
            },
            'model_used': 'Transformer'
        }
    
    def _analyze_baseline(self, text: str) -> dict:
        X = self.baseline_vectorizer.transform([text])
        
        pred = self.baseline_model.predict(X)[0]
        proba = self.baseline_model.predict_proba(X)[0]
        
        neg_score = proba[0]
        neu_score = proba[1]
        pos_score = proba[2]
        
        total_polarized_score = neg_score + pos_score
        
        if total_polarized_score > 0:
            if pos_score > neg_score:
                final_sentiment_idx = 2
                final_confidence = pos_score
            else:
                final_sentiment_idx = 0
                final_confidence = neg_score
        else:
            final_sentiment_idx = 0
            final_confidence = 0.5
        
        return {
            'sentiment': self.sentiment_labels[final_sentiment_idx],
            'confidence': float(final_confidence),
            'scores': {
                'negative': float(neg_score),
                'neutral': 0.0,
                'positive': float(pos_score)
            },
            'model_used': 'Baseline'
        }

    def _analyze_vader(self, text: str) -> dict:
        scores = self.vader_analyzer.polarity_scores(text)
        neg = scores['neg']
        neu = scores['neu']
        pos = scores['pos']
        compound = scores['compound']
        
        if compound >= 0.05:
            sentiment = 'Positive'
            confidence = pos
        elif compound <= -0.05:
            sentiment = 'Negative'
            confidence = neg
        else:
            sentiment = 'Neutral'
            confidence = neu
        
        return {
            'sentiment': sentiment,
            'confidence': float(confidence),
            'scores': {
                'negative': float(neg),
                'neutral': float(neu),
                'positive': float(pos)
            },
            'model_used': 'VADER-fallback'
        }

    def get_word_frequencies(self, texts: list) -> dict:
        all_text = ' '.join([self.clean_text(t) for t in texts])
        
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        words = all_text.split()
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        word_counts = Counter(filtered_words)
        
        return dict(word_counts.most_common(50))


_analyzer = None

def get_analyzer() -> SentimentAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer