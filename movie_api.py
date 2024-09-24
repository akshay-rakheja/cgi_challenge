import requests
from typing import List, Dict, Any
from utils import format_runtime, calculate_relative_rating, retry_with_backoff
from flask_caching import Cache

BASE_URL = "https://us-central1-creator-studio-workflows.cloudfunctions.net"
HEADERS = {'Authorization': 'xyz'}

# Initialize cache
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})


@retry_with_backoff
@cache.cached(timeout=300, key_prefix='popular_movies')
def get_popular_movies() -> List[Dict[str, Any]]:
    try:
        url = f"{BASE_URL}/movies"
        headers = {"Content-Type": "application/json", **HEADERS}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('movies', [])
    except requests.Timeout:
        raise Exception("Request timed out. Please try again later.")
    except requests.ConnectionError:
        raise Exception(
            "Unable to connect to the server. Please check your internet connection."
        )
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch popular movies: {str(e)}")


@retry_with_backoff
@cache.memoize(timeout=300)
def get_movie_details(movie_id: str) -> Dict[str, Any]:
    try:
        url = f"{BASE_URL}/movieDetails"
        payload = {"movie_id": movie_id}
        headers = {"Content-Type": "application/json", **HEADERS}
        response = requests.post(url,
                                 json=payload,
                                 headers=headers,
                                 timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        else:
            raise Exception(f"Failed to fetch movie details: {str(e)}")
    except requests.Timeout:
        return None
    except requests.ConnectionError:
        return None
    except requests.RequestException as e:
        return None


def get_movie_recommendations(genre: str, limit: int) -> Dict[str, Any]:
    popular_movies = get_popular_movies()
    filtered_movies = [
        movie for movie in popular_movies
        if genre.lower() == movie.get('genre', '').lower()
    ]

    if not filtered_movies:
        filtered_movies = [ movie for movie in popular_movies if genre.lower() == movie.get('genre', '').lower()]

        if not filtered_movies:
            raise Exception(
                f"No movies found for genre: {genre}")

    recommendations = []
    total_runtime = 0

    for movie in filtered_movies:
        movie_details = get_movie_details(movie['id'])
        if movie_details:
            rating = movie_details.get('rating', 0)
            runtime = movie_details.get('run_time_minutes', 0)
            recommendations.append({
                "title": movie.get('title', ''),
                "genre": genre.lower(),
                "rating": rating,
                "relative_rating": 0,
                "run_time": format_runtime(runtime)
            })
            total_runtime += runtime

    if not recommendations:
        raise Exception(f"No movie details found for genre: {genre}")

    avg_rating = sum(movie['rating'] for movie in recommendations) / len(
        recommendations) if recommendations else 0

    for movie in recommendations:
        movie['relative_rating'] = calculate_relative_rating(
            movie['rating'], avg_rating)

    recommendations.sort(key=lambda x: x['relative_rating'], reverse=True)

    return {
        "metrics": {
            "total_run_time_minutes": total_runtime
        },
        "results": recommendations[:limit]
    }


def clear_cache():
    cache.clear()
