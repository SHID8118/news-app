from flask import Flask, render_template, request
import requests
import os  # Import the 'os' module to access environment variables
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

# Configuration
# API_KEY = "YOUR_ACTUAL_API_KEY"  <- REMOVE THIS LINE
CATEGORIES = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
DEFAULT_COUNT = 10
API_KEY_NAME = "NEWS_API_KEY"  # Name of the environment variable for your API key

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_category = None
    selected_count = DEFAULT_COUNT
    news_data = None
    error_message = None

    if request.method == 'POST':
        selected_category = request.form.get('category')
        try:
            selected_count = min(int(request.form.get('story_count', DEFAULT_COUNT)), 20)  # Limit to 20 max
        except ValueError:
            selected_count = DEFAULT_COUNT

        if selected_category:
            news_data, error_message = fetch_news(selected_category, selected_count)

    return render_template('news.html',
                           categories=CATEGORIES,
                           news_data=news_data,
                           error_message=error_message,
                           selected_category=selected_category,
                           selected_count=selected_count)

def fetch_news(category, count):
    """
    Fetches global news from NewsAPI based on category and count.
    Returns tuple: (news_data, error_message)
    """
    base_url = "https://newsapi.org/v2/top-headlines"
    api_key = os.environ.get(API_KEY_NAME)  # Get the API key from the environment variable

    if not api_key:
        print(f"Error: Environment variable '{API_KEY_NAME}' not set.")
        return None, "API key not configured. Please check your deployment settings."

    params = {
        'category': category,
        'pageSize': count,
        'apiKey': api_key,
        'language': 'en'  # English articles only
    }

    print(f"API Request Params: {params}")  # Debugging

    try:
        response = requests.get(base_url, params=params, timeout=10)  # Added timeout
        response.raise_for_status()
        news_data = response.json()

        if news_data.get("status") == "ok":
            if news_data.get("totalResults", 0) > 0:
                # Process articles to ensure consistent structure
                processed_articles = []
                for article in news_data.get("articles", []):
                    processed_article = {
                        'title': article.get('title', 'No title available'),
                        'description': article.get('description', 'No description available'),
                        'url': article.get('url', '#'),
                        'urlToImage': article.get('urlToImage', 'https://via.placeholder.com/400x200?text=No+Image'),
                        'source': {'name': article.get('source', {}).get('name', 'Unknown source')}
                    }
                    processed_articles.append(processed_article)
                return processed_articles, None
            return None, "No articles found for this category. Try another one."
        return None, f"API Error: {news_data.get('message', 'Unknown error')}"

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        print(error_msg)
        return None, "Failed to fetch news. Please check your connection."
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return None, "An unexpected error occurred. Please try again later."

@app.errorhandler(Exception)
def handle_exception(e):
    # Handle all exceptions uniformly
    if isinstance(e, HTTPException):
        return render_template('error.html', error=str(e)), e.code
    print(f"Unexpected error: {str(e)}")
    return render_template('error.html', error="An unexpected error occurred"), 500

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nServer stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"Fatal error: {str(e)}")