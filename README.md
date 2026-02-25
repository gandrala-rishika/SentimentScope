## What is SentimentScope?

SentimentScope is an advanced AI-powered web application designed to analyze public sentiment from social media comments and e-commerce product reviews. By leveraging state-of-the-art Machine Learning models and Large Language Models (LLMs), it provides deep insights into user opinions, automating the process of understanding feedback on platforms like YouTube, Amazon, and Flipkart.

## Key Features

🤖 **AI-Powered Sentiment Analysis**
- Utilizes a tiered fallback system: DistilBERT Transformer → Baseline ML Model → VADER.
- Analyzes text with high accuracy, handling slang and emoji translations.
- Supports single text, bulk text, and CSV file uploads.

📹 **Social Media Integration**
- Analyze comments from **YouTube** (Standard Videos & Shorts).
- Stealth scraping capabilities using Playwright to bypass detection.
- Automatic translation of non-English comments.

🛍️ **E-Commerce Review Analysis**
- Fetch and analyze product reviews directly from **Amazon** and **Flipkart** URLs.
- Extract meaningful insights from customer feedback to understand product reception.

🧠 **LLM Summaries**
- Generates human-like summaries of analyzed content using OpenRouter (GLM-4).
- Get a quick overview of "what people are saying" without reading every comment.

📊 **Interactive Dashboard**
- Visualize sentiment distribution with dynamic Pie Charts and Bar Graphs.
- Track analysis history and statistics.
- Word frequency analysis to identify trending topics.

## Tech Stack

**Backend:**
- **FastAPI** (High-performance Python web framework)
- **PyTorch & Transformers** (Hugging Face for Deep Learning models)
- **Playwright** (Browser automation for web scraping)
- **MongoDB** (Motor for async database operations)
- **OpenRouter API** (LLM integration for summaries)

**Frontend:**
- **React** (UI components)
- **Recharts** (Data visualization)
- **Tailwind CSS** (Utility-first styling)
- **Shadcn UI** (Component library)
- **Axios** (API requests)

## Quick Start Guide

### Prerequisites
- Python 3.9+
- Node.js & npm/yarn
- MongoDB (local or cloud instance)
- OpenRouter API Key (for AI summaries)

### Installation Steps

1. **Clone the repository**

2. **Set up virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # On Linux: source venv/bin/activate
```

3. **Install backend dependencies**
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

4. **Run backend server**
```bash
uvicorn server:app --reload
```

5. **Open a new terminal and install frontend dependencies**
```bash
cd frontend
yarn install
```

6. **Start frontend application**
```bash
yarn start
```

## API Endpoints

**Analysis:**
- `POST /api/analyze/text` - Analyze a single text string
- `POST /api/analyze/bulk` - Analyze multiple texts (up to 100)
- `POST /api/analyze/url` - Scrape and analyze comments/reviews from a URL

**Data & History:**
- `GET /api/history` - Retrieve recent analysis history
- `GET /api/stats` - Get aggregate statistics for the dashboard

**Root:**
- `GET /api/` - API information and available endpoints

## Configuration Details

**Model Setup:**
- The application looks for a local DistilBERT model in `backend/models/distilbert_sentiment`.
- If not found, it attempts to load a Baseline model from `backend/models/baseline_model.pkl`.
- If neither is found, it falls back to VADER sentiment analysis.

**Supported Platforms for URL Analysis:**
- **Video:** YouTube (Videos, Shorts)
- **Shopping:** Amazon, Flipkart

## Model Training

For training the model, we used the following resources:

**Training Notebook:**
- [SentimentScope Training Notebook](https://www.kaggle.com/code/eswarvutukuri/sentimentscope)

**Datasets Used:**
- [Amazon Reviews](https://www.kaggle.com/datasets/bittlingmayer/amazonreviews)
- [Sentiment Analysis on Financial Tweets](https://www.kaggle.com/datasets/vivekrathi055/sentiment-analysis-on-financial-tweets)
- [Sentiment140](https://www.kaggle.com/datasets/kazanova/sentiment140)

**Post-Training Setup:**
Once the model is trained, you will obtain a `baseline_model.pkl` file and a `distilbert_sentiment` folder. To use them in the application:
1. Download these artifacts.
2. Create a folder named `models` inside the `backend` directory.
3. Place both the `baseline_model.pkl` file and the `distilbert_sentiment` folder into `backend/models/`.

## License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

© 2026 Gandrala Rishika, Mallampati Rupanjali, Eswar Vutukuri

## Acknowledgments

Thanks to Hugging Face for the Transformers library, OpenRouter for accessible LLM APIs, MongoDB for storing data, the Playwright team for robust browser automation, and the creators of Recharts for visualization components.