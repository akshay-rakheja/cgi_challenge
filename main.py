import sys
import json
import time
from flask import Flask, request, jsonify
from movie_api import get_movie_recommendations, cache, clear_cache
from utils import validate_genre

app = Flask(__name__)
cache.init_app(app)

@app.route('/api/movie-recommendations', methods=['GET'])
def movie_recommendations():
    genre = request.args.get('genre', '').strip()
    limit = request.args.get('limit', 5, type=int)

    if not validate_genre(genre):
        return jsonify({"error": "Invalid genre. Please enter a valid genre with only letters and spaces."}), 400

    if not 1 <= limit <= 10:
        return jsonify({"error": "Limit must be between 1 and 10."}), 400

    try:
        start_time = time.time()
        recommendations = get_movie_recommendations(genre, limit)
        end_time = time.time()
        
        response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        recommendations['metrics']['response_time_ms'] = response_time
        
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache_endpoint():
    clear_cache()
    return jsonify({"message": "Cache cleared successfully"}), 200

def cli_interface():
    while True:
        genre = input("Enter the movie genre you're interested in: ").strip()
        if validate_genre(genre):
            break
        print("Invalid genre. Please enter a valid genre with only letters and spaces.")
    
    while True:
        try:
            limit = int(input("Enter the number of movie recommendations you want (1-10): "))
            if 1 <= limit <= 10:
                break
            print("Limit must be between 1 and 10.")
        except ValueError:
            print("Please enter a valid number.")
    
    try:
        start_time = time.time()
        recommendations = get_movie_recommendations(genre, limit)
        end_time = time.time()
        
        response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        recommendations['metrics']['response_time_ms'] = response_time
        
        print(json.dumps(recommendations, indent=2))
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        cli_interface()
    else:
        app.run(host='0.0.0.0', port=5001, debug=True)
