from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import traceback
from ..utils.astro_calculations import calculate_doshams

dosham_bp = Blueprint('dosham', __name__)


@dosham_bp.route('/dosham', methods=['POST'])
@cross_origin()
def dosham_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON input"}), 400
        result = calculate_doshams(data)
        return jsonify(result)
    except Exception as e:
        tb = traceback.format_exc()
        print("ERROR TRACEBACK:\n", tb)  # Print to console
        return jsonify({
            "error": str(e),
            "traceback": tb
        }), 500
