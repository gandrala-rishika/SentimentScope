import os
import logging
import asyncio
import uuid
import random
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

import pandas as pd
import io
import requests

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from playwright.sync_api import sync_playwright
from deep_translator import GoogleTranslator
from textblob import TextBlob

from ml_utils.sentiment_analyzer import get_analyzer
from pydantic import BaseModel, Field, ConfigDict

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

llm_client = None
if os.environ.get('OPENROUTER_API_KEY'):
    llm_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get('OPENROUTER_API_KEY'),
    )

executor = ThreadPoolExecutor(max_workers=4)

app = FastAPI(title="SentimentScope API", version="1.00")
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    analyzer = get_analyzer()
    logger.info("Sentiment analyzer initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize sentiment analyzer: {e}")
    analyzer = None

display_translator = GoogleTranslator(source='auto', target='en')

class TextInput(BaseModel):
    text: str

class BulkTextInput(BaseModel):
    texts: List[str]

class SentimentResult(BaseModel):
    text: str
    sentiment: str
    confidence: float
    scores: dict
    model_used: str

class BulkSentimentResult(BaseModel):
    results: List[SentimentResult]
    summary: dict
    word_frequencies: dict

class AnalysisHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    sentiment: str
    confidence: float
    scores: dict
    model_used: str
    analysis_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UrlInput(BaseModel):
    url: str

def autocorrect_text(text: str) -> str:
    try:
        blob = TextBlob(text)
        return str(blob.correct())
    except Exception as e:
        logger.warning(f"Autocorrection failed: {e}")
        return text

def format_comment_with_translation(text: str) -> str:
    if not text:
        return text
    
    if not text.isascii():
        try:
            translated = display_translator.translate(text)
            return f"{text} ({translated})"
        except Exception as e:
            logger.warning(f"Translation failed for '{text[:20]}...': {e}")
            return text
    
    return text

def get_proxy_config():
    proxy_server = os.environ.get('PROXY_SERVER')
    if not proxy_server:
        return None
    
    proxy_config = {"server": proxy_server}
    if os.environ.get('PROXY_USERNAME') and os.environ.get('PROXY_PASSWORD'):
        proxy_config["username"] = os.environ['PROXY_USERNAME']
        proxy_config["password"] = os.environ['PROXY_PASSWORD']
    
    return proxy_config

def random_delay(min_s=1.0, max_s=3.0):
    time.sleep(random.uniform(min_s, max_s))

def apply_stealth(page):
    stealth_js = """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });
    window.chrome = {
        runtime: {},
    };
    """
    page.add_init_script(stealth_js)

def scroll_and_collect(page, selector, max_scrolls=30, target_count=100):
    collected_items = set()
    last_count = 0
    stagnant_scrolls = 0
    
    for i in range(max_scrolls):
        scroll_amount = random.randint(400, 800)
        page.mouse.wheel(0, scroll_amount)
        random_delay(0.8, 1.5)
        
        try:
            elements = page.locator(selector).all_text_contents()
            current_batch = 0
            for text in elements:
                clean_text = text.strip()
                if len(clean_text) > 5:
                    collected_items.add(clean_text)
                    current_batch += 1
            
            if len(collected_items) >= target_count:
                break
            
            if len(collected_items) == last_count:
                stagnant_scrolls += 1
                if stagnant_scrolls > 5:
                    break
            else:
                stagnant_scrolls = 0
                last_count = len(collected_items)
                
        except Exception as e:
            logger.warning(f"Error locating elements during scroll: {e}")
            
    return list(collected_items)

def scrape_youtube_sync(url: str) -> dict:
    try:
        with sync_playwright() as p:
            launch_args = [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars'
            ]
            
            browser = p.chromium.launch(
                headless=True,
                args=launch_args
            )
            
            context_options = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "viewport": {'width': 1920, 'height': 1080},
                "locale": 'en-US'
            }
            
            proxy_config = get_proxy_config()
            if proxy_config:
                logger.info("Using Proxy configuration.")
                context_options["proxy"] = proxy_config

            context = browser.new_context(**context_options)
            page = context.new_page()
            
            apply_stealth(page)
            
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            clean_path = parsed_url.path
            
            url_lower = url.lower()
            is_shorts = "shorts" in url_lower
            is_instagram = "instagram.com" in url_lower or "instagr.am" in url_lower
            is_youtube = "youtube.com" in url_lower or "youtu.be" in url_lower
            is_amazon = "amazon." in url_lower
            is_flipkart = "flipkart." in url_lower

            if "youtu.be" in url_lower:
                video_id = clean_path.split("/")[-1]
                clean_url = f"https://www.youtube.com/watch?v={video_id}"
            elif is_shorts:
                clean_url = url
            else:
                clean_url = url
            
            if is_instagram:
                if "www.instagram.com" in clean_url:
                    pass
                else:
                    clean_url = clean_url.replace("instagram.com", "www.instagram.com")

            logger.info(f"Attempting to scrape URL: {clean_url}")
            
            page.goto(clean_url, wait_until="domcontentloaded", timeout=60000)
            
            try:
                reject_button = page.get_by_role("button", name="Reject all")
                if reject_button.is_visible(timeout=2000):
                    reject_button.click()
                    random_delay(1, 2)
            except:
                pass 

            random_delay(2, 4)

            comments = []
            title = page.title()
            
            if is_youtube and not is_shorts:
                logger.info("Standard YouTube Video detected.")
                selector = "#content-text"
                target_comments = 100
                comments_set = set()
                scroll_iterations = 0
                max_scroll_iterations = 60

                elements = page.query_selector_all(selector)
                for el in elements:
                    text = el.inner_text()
                    if len(text) > 5:
                        comments_set.add(text)

                while len(comments_set) < target_comments and scroll_iterations < max_scroll_iterations:
                    page.evaluate("window.scrollBy(0, 800)")
                    random_delay(0.4, 0.8) 
                    
                    elements = page.query_selector_all(selector)
                    for el in elements:
                        text = el.inner_text()
                        if len(text) > 5:
                            comments_set.add(text)
                    
                    scroll_iterations += 1
                
                comments = list(comments_set)

            elif is_shorts:
                logger.info("YouTube Shorts detected. Attempting to open comments.")
                try:
                    comments_button = page.locator("button[aria-label*='comment' i], ytd-button-renderer #button[aria-label*='comment' i]").first
                    
                    if comments_button.is_visible(timeout=5000):
                        comments_button.click()
                        logger.info("Clicked Shorts comment button. Waiting for panel...")
                        random_delay(2, 4)
                    else:
                        logger.warning("Could not find comment button, attempting to scroll anyway.")
                    
                except Exception as e:
                    logger.warning(f"Error clicking Shorts comment button: {e}")
                
                comments = scroll_and_collect(
                    page, 
                    "ytd-comment-thread-renderer #content-text, ytd-comment-view-model #content-text", 
                    max_scrolls=30,
                    target_count=100
                )

            elif is_instagram:
                logger.info("Instagram detected.")
                try:
                    dialog = page.locator("div[role='dialog']")
                    if dialog.is_visible(timeout=2000):
                        logger.info("Detected dialog/modal. Attempting to close.")
                        close_btn = dialog.locator("svg[aria-label='Close'], button[aria-label='Close']").first
                        if close_btn.is_visible(timeout=1000):
                            close_btn.click()
                            random_delay(1, 2)
                        else:
                            page.keyboard.press("Escape")
                            random_delay(1, 2)
                except Exception as e:
                    logger.info(f"Dialog handling check: {e}")
                if "login" in page.url:
                    logger.error("Redirected to login page. Cannot scrape.")
                    browser.close()
                    return {
                        "title": "Login Required",
                        "description": "Instagram redirected to login.",
                        "comments": []
                    }
                if "/p/" not in page.url and "/reel/" not in page.url and "/tv/" not in page.url:
                    logger.error(f"Redirected away from post. Current URL: {page.url}")
                    browser.close()
                    return {
                        "title": "Redirected",
                        "description": "Could not access specific post.",
                        "comments": []
                    }
                try:
                    allow_cookies_btn = page.locator("button:has-text('Allow essential cookies'), button:has-text('Accept All')")
                    if allow_cookies_btn.is_visible(timeout=2000):
                        allow_cookies_btn.click()
                        random_delay(1, 2)
                except:
                    pass

                try:
                    not_now_btn = page.get_by_role("button", name="Not now")
                    if not_now_btn.is_visible(timeout=1000):
                        not_now_btn.click()
                        random_delay(1, 2)
                except:
                    pass

                username = "Unknown User"
                try:
                    username_el = page.locator("article header a").first
                    if username_el:
                        username = username_el.inner_text()
                except:
                    pass
                
                caption_text = ""
                try:
                    caption_el = page.locator("article ul li:first-child span[dir='auto'], article h1").first
                    if caption_el:
                        caption_text = caption_el.inner_text()
                except:
                    pass
                
                title = f"{username}: {caption_text}"

                try:
                    view_comments_btn = page.locator("button:has-text('View all'), a:has-text('View all')")
                    if view_comments_btn.is_visible(timeout=3000):
                        view_comments_btn.click()
                        logger.info("Clicked 'View all' comments.")
                        random_delay(2, 3)
                except:
                    pass

                comments = scroll_and_collect(
                    page, 
                    "article ul > ul li span[dir='auto'], article ul > li span[dir='auto']", 
                    max_scrolls=30,
                    target_count=100
                )

                if not comments:
                    logger.warning("Primary selector failed, trying fallback.")
                    comments = scroll_and_collect(
                        page, 
                        "article ul > li", 
                        max_scrolls=10,
                        target_count=100
                    )

                if not comments:
                    logger.error("Still found 0 comments. Taking screenshot.")
                    try:
                        page.screenshot(path="instagram_empty_debug.png")
                        logger.info("Saved screenshot to instagram_empty_debug.png")
                    except:
                        pass

            elif is_amazon:
                logger.info("Amazon detected.")
                comments = scroll_and_collect(
                    page, 
                    ".review-text-content span", 
                    max_scrolls=20,
                    target_count=100
                )

            elif is_flipkart:
                logger.info("Flipkart detected.")
                comments = scroll_and_collect(
                    page, 
                    "div._27M-vq", 
                    max_scrolls=20,
                    target_count=100
                )
            
            logger.info(f"Scraping Complete. Total Comments: {len(comments)}")

            browser.close()

            if comments:
                final_comments = comments[:100] if len(comments) >= 100 else comments
                return {
                    "title": title.replace(" - YouTube", "").replace(" - Amazon", ""),
                    "description": "Scraped via Playwright Stealth",
                    "comments": final_comments 
                }
            else:
                return {
                    "title": title,
                    "description": "Scraped via Playwright (No comments found or Login required)",
                    "comments": [] 
                }
            
    except Exception as e:
        logger.error(f"Scraping function error: {e}")
        return None

async def fetch_content_from_url(url: str) -> dict:
    if "youtube.com" in url or "youtu.be" in url or "instagram.com" in url or "instagr.am" in url or "amazon" in url or "flipkart" in url:
        logger.info(f"Using Threaded Playwright to scrape: {url}")
        loop = asyncio.get_running_loop()
        
        try:
            result = await loop.run_in_executor(executor, scrape_youtube_sync, url)
            
            if result is not None:
                return result
        except Exception as e:
            logger.error(f"Playwright thread execution failed: {e}")

    logger.info(f"Using Mock data (free fallback) for: {url}")
    
    if "youtube.com" in url or "youtu.be" in url:
        raise HTTPException(
            status_code=503, 
            detail="Could not scrape video comments. The video might be private, age-restricted, comments are disabled, or comments are hidden."
        )
    elif "amazon" in url or "flipkart" in url:
        return {
            "title": "Wireless Noise Cancelling Headphones",
            "description": "High fidelity audio, 30h battery life.",
            "reviews": [
                "Best headphones I've ever owned.",
                "Broke after 2 weeks.",
                "Good for price, NC is okay.",
                "I am in love with these!",
                "Shipping slow.",
                "Battery life as advertised."
            ]
        }
    else:
        return {
            "title": "Viral Travel Reel",
            "description": "Exploring hidden gems.",
            "comments": [
                "Wow, stunning! 😍",
                "Where is this?",
                "Too much editing.",
                "Breathtaking.",
                "Music perfect.",
                "Overcrowded."
            ]
        }

def generate_llm_summary(title: str, description: str, texts: List[str]) -> str:
    if not llm_client:
        return "Summary unavailable: OpenRouter API Key not configured."
    
    try:
        combined_text = f"Title: {title}\nDescription: {description}\n\nComments/Reviews:\n" + "\n".join(texts[:20])
        
        response = llm_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:3000", 
                "X-Title": "SentimentScope", 
            },
            extra_body={},
            model="z-ai/glm-4.5-air:free",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a sentiment analysis assistant. Analyze the provided content (Title, Description, and Comments/Reviews). Provide a 4-5 line summary of what people are saying. Conclude with whether the overall sentiment is Positive or Negative."
                },
                {
                    "role": "user", 
                    "content": combined_text
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return "Error generating summary."

@api_router.get("/")
async def root():
    return {
        "message": "SentimentScope API",
        "version": "1.0.0",
        "endpoints": {
            "analyze_text": "/api/analyze/text",
            "analyze_bulk": "/api/analyze/bulk",
            "analyze_csv": "/api/analyze/csv",
            "analyze_url": "/api/analyze/url",
            "get_history": "/api/history",
            "get_stats": "/api/stats"
        }
    }

@api_router.post("/analyze/text", response_model=SentimentResult)
async def analyze_text(input_data: TextInput):
    if not analyzer:
        raise HTTPException(status_code=503, detail="Sentiment analyzer not available")
    
    try:
        corrected_text = autocorrect_text(input_data.text)
        result = analyzer.analyze(corrected_text)
        
        response = SentimentResult(
            text=input_data.text[:200],
            sentiment=result['sentiment'],
            confidence=result['confidence'],
            scores=result['scores'],
            model_used=result['model_used']
        )
        
        history_doc = AnalysisHistory(
            text=corrected_text[:500],
            sentiment=result['sentiment'],
            confidence=result['confidence'],
            scores=result['scores'],
            model_used=result['model_used'],
            analysis_type='single'
        )
        
        doc = history_doc.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.analysis_history.insert_one(doc)
        
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analyze/bulk", response_model=BulkSentimentResult)
async def analyze_bulk(input_data: BulkTextInput):
    if not analyzer:
        raise HTTPException(status_code=503, detail="Sentiment analyzer not available")
    
    if len(input_data.texts) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 texts allowed")
    
    try:
        results = []
        sentiments = []
        
        for text in input_data.texts:
            corrected_text = autocorrect_text(text)
            result = analyzer.analyze(corrected_text)
            
            results.append(SentimentResult(
                text=text[:200],
                sentiment=result['sentiment'],
                confidence=result['confidence'],
                scores=result['scores'],
                model_used=result['model_used']
            ))
            
            sentiments.append(result['sentiment'])
        
        sentiment_counts = {
            'positive': sentiments.count('Positive'), 
            'negative': sentiments.count('Negative'), 
            'neutral': 0
        }
        
        total = len(sentiments)
        sentiment_percentages = {
            k: round(v / total * 100, 2) if total > 0 else 0
            for k, v in sentiment_counts.items()
        }
        
        word_frequencies = analyzer.get_word_frequencies(input_data.texts)
        
        summary = {
            'total_analyzed': len(results),
            'sentiment_counts': sentiment_counts,
            'sentiment_percentages': sentiment_percentages
        }
        
        for result in results[:10]:
            history_doc = AnalysisHistory(
                text=result.text,
                sentiment=result.sentiment,
                confidence=result.confidence,
                scores=result.scores,
                model_used=result.model_used,
                analysis_type='bulk'
            )
            doc = history_doc.model_dump()
            doc['timestamp'] = doc['timestamp'].isoformat()
            await db.analysis_history.insert_one(doc)
        
        return BulkSentimentResult(
            results=results,
            summary=summary,
            word_frequencies=word_frequencies
        )
        
    except Exception as e:
        logger.error(f"Error analyzing bulk texts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analyze/csv")
async def analyze_csv(file: UploadFile = File(...)):
    if not analyzer:
        raise HTTPException(status_code=503, detail="Sentiment analyzer not available")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        if 'text' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="CSV must contain 'text' column"
            )
        
        if len(df) > 1000:
            df = df.head(1000)
        
        results = []
        sentiments = []
        texts = []
        
        for _, row in df.iterrows():
            text = str(row['text'])
            if not text or text == 'nan':
                continue
            
            corrected_text = autocorrect_text(text)
            result = analyzer.analyze(corrected_text)
            
            results.append({
                'text': text[:200],
                'sentiment': result['sentiment'],
                'confidence': result['confidence'],
                'scores': result['scores'],
                'model_used': result['model_used']
            })
            
            sentiments.append(result['sentiment'])
            texts.append(text)
        
        sentiment_counts = {
            'positive': sentiments.count('positive'),
            'negative': sentiments.count('negative'),
            'neutral': 0
        }
        
        total = len(sentiments)
        sentiment_percentages = {
            k: round(v / total * 100, 2) if total > 0 else 0
            for k, v in sentiment_counts.items()
        }
        
        word_frequencies = analyzer.get_word_frequencies(texts)
        
        summary = {
            'total_analyzed': len(sentiments),
            'sentiment_counts': sentiment_counts,
            'sentiment_percentages': sentiment_percentages
        }
        
        return {
            'results': results,
            'summary': summary,
            'word_frequencies': word_frequencies
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except Exception as e:
        logger.error(f"Error analyzing CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analyze/url")
async def analyze_url(input_data: UrlInput):
    if not analyzer:
        raise HTTPException(status_code=503, detail="Sentiment analyzer not available")

    try:
        content = await fetch_content_from_url(input_data.url)
        
        texts = content.get("comments") or content.get("reviews") or []
        
        if not texts:
            return {
                'results': [],
                'summary': {
                    'total_analyzed': 0,
                    'sentiment_counts': {'positive': 0, 'negative': 0, 'neutral': 0},
                    'sentiment_percentages': {'positive': 0.0, 'negative': 0.0}
                },
                'word_frequencies': {},
                'ai_summary': "No comments available to analyze.",
                'metadata': {
                    'title': content.get('title'),
                    'description': content.get('description', '')
                }
            }

        results = []
        sentiments = []
        
        for text in texts:
            corrected_text = autocorrect_text(text)
            result = analyzer.analyze(corrected_text)
            display_text = format_comment_with_translation(text)
            
            results.append({
                'text': display_text, 
                'sentiment': result['sentiment'],
                'confidence': result['confidence'],
                'scores': result['scores'],
                'model_used': result['model_used']
            })
            sentiments.append(result['sentiment'])

        sentiment_counts = {
            'positive': sentiments.count('Positive'), 
            'negative': sentiments.count('Negative'), 
            'neutral': 0
        }
        
        total = len(sentiments)
        sentiment_percentages = {
            k: round(v / total * 100, 2) if total > 0 else 0
            for k, v in sentiment_counts.items()
        }
        
        word_frequencies = analyzer.get_word_frequencies(texts)

        summary_stats = {
            'total_analyzed': len(results),
            'sentiment_counts': sentiment_counts,
            'sentiment_percentages': sentiment_percentages
        }

        ai_summary = generate_llm_summary(
            content.get('title', 'Unknown'), 
            content.get('description', ''), 
            texts
        )

        overall_sentiment = 'Mixed'
        if sentiment_counts['positive'] > sentiment_counts['negative']: overall_sentiment = 'Positive'
        elif sentiment_counts['negative'] > sentiment_counts['positive']: overall_sentiment = 'Negative'

        history_doc = AnalysisHistory(
            text=f"URL Analysis: {input_data.url}",
            sentiment=overall_sentiment,
            confidence=0.8, 
            scores=sentiment_counts,
            model_used='Transformer',
            analysis_type='url'
        )
        doc = history_doc.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.analysis_history.insert_one(doc)

        return {
            'results': results,
            'summary': summary_stats,
            'word_frequencies': word_frequencies,
            'ai_summary': ai_summary,
            'metadata': {
                'title': content.get('title'),
                'description': content.get('description', '')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/history")
async def get_history(limit: int = 50):
    try:
        history = await db.analysis_history.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {"history": history, "count": len(history)}
        
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/stats")
async def get_stats():
    try:
        all_history = await db.analysis_history.find({}, {"_id": 0}).to_list(1000)
        
        if not all_history:
            return {
                'total_analyses': 0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'by_type': {'single': 0, 'bulk': 0, 'csv': 0, 'url': 0}
            }
        
        sentiments = [h['sentiment'] for h in all_history]
        analysis_types = [h.get('analysis_type', 'single') for h in all_history]
        
        sentiment_counts = {
            'positive': sentiments.count('Positive'),
            'negative': sentiments.count('Negative'),
            'neutral': 0
        }
        
        type_counts = {
            'single': analysis_types.count('single'),
            'bulk': analysis_types.count('bulk'),
            'csv': analysis_types.count('csv'),
            'url': analysis_types.count('url')
        }
        
        return {
            'total_analyses': len(all_history),
            'sentiment_distribution': sentiment_counts,
            'by_type': type_counts
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()