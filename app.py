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
    # Allow client to specify time and depth for "Advanced" analysis
    time_limit = float(data.get("time", 1.0))
    depth_limit = int(data.get("depth", 20))
    
    logger.info(f"Processing FEN: {fen} (Time: {time_limit}s, Depth: {depth_limit})")
    
    try:
        board = chess.Board(fen)
        
        if board.is_game_over():
            return jsonify({"error": "Game is already over", "status": board.result()}), 400

        try:
            with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
                # Max skill level for Grandmaster play
                engine.configure({"Skill Level": 20})
                
                # Use engine.analyse to get move + evaluation
                limit = chess.engine.Limit(time=time_limit, depth=depth_limit)
                info = engine.analyse(board, limit)
                
                best_move = info.get("pv")[0].uci() if info.get("pv") else None
                score = info.get("score").white() # Score from white's perspective
                
                # Format score for frontend (+1.5, -2.0, or M3)
                score_val = 0
                is_mate = False
                if score.is_mate():
                    score_val = score.mate()
                    is_mate = True
                else:
                    score_val = score.score() / 100.0 # Convert centipawns to pawns
                
                return jsonify({
                    "bestMove": best_move,
                    "evaluation": {
                        "score": score_val,
                        "isMate": is_mate,
                        "depth": info.get("depth"),
                        "nodes": info.get("nodes"),
                        "pv": [m.uci() for m in info.get("pv")[:5]] if info.get("pv") else []
                    }
                })
        except FileNotFoundError:
            return jsonify({"error": f"Stockfish engine not found at {STOCKFISH_PATH}"}), 500
            
    except ValueError:
        return jsonify({"error": "Invalid FEN board state"}), 400
    except Exception as e:
        logger.error(f"Engine Error: {str(e)}")
        return jsonify({"error": f"Engine failed: {str(e)}"}), 500

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
