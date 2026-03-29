import os
import chess
import chess.engine
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Use environmental variable for Stockfish path, default to "stockfish" 
# which should be in the PATH if installed via apt-get
STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH", "stockfish")

@app.route("/api/move", methods=["POST"])
def get_move():
    data = request.json
    if not data or "fen" not in data:
        return jsonify({"error": "Missing FEN board state"}), 400
    
    fen = data["fen"]
    logger.info(f"Processing FEN: {fen}")
    
    try:
        board = chess.Board(fen)
        
        # Check if the game is already over
        if board.is_game_over():
            return jsonify({"error": "Game is already over", "status": board.result()}), 400

        # Start the Stockfish engine
        try:
            with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                # Skill Level 20 is the maximum (approx. 3500+ Elo)
                engine.configure({"Skill Level": 20})
                
                # We use a 1.0s limit or depth 20 for "Impossible" mode
                # This ensures the mobile user doesn't wait too long but gets a master-level move
                limit = chess.engine.Limit(time=1.0, depth=20)
                result = engine.play(board, limit)
                
                best_move = result.move.uci()
                logger.info(f"AI Move: {best_move}")
                
                return jsonify({
                    "bestMove": best_move,
                    "info": {
                        "depth": 20,
                        "skill": 20
                    }
                })
        except FileNotFoundError:
            return jsonify({"error": f"Stockfish engine not found at {STOCKFISH_PATH}"}), 500
            
    except ValueError:
        return jsonify({"error": "Invalid FEN board state"}), 400
    except Exception as e:
        logger.error(f"Engine Error: {str(e)}")
        return jsonify({"error": "Engine failed to calculate move"}), 500

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "Chess AI Backend",
        "engine": "Stockfish 16",
        "status": "ready"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "chess-ai-engine"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
