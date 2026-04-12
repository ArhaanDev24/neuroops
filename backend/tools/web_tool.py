import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def search_web(query: str) -> str:
    """
    Simulates a web search by scraping DuckDuckGo HTML results.
    Note: In production, use a dedicated Search API (Serper, Bing, etc.).
    This is a lightweight implementation for demonstration.
    """
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return "Failed to fetch search results."
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Extract links and snippets
        for link in soup.find_all('a', class_='result__a'):
            title = link.get_text(strip=True)
            href = link.get('href')
            results.append(f"Title: {title}\nLink: {href}")
            
        return "\n\n".join(results[:5]) if results else "No results found."
        
    except Exception as e:
        return f"Web search error: {str(e)}"