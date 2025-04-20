from flask import Blueprint, current_app, request, jsonify

from utils.translateDict import translate_dict

translate_bp = Blueprint('translate', __name__)


@translate_bp.route('/', methods=['POST'])
def i18n_translate():
    req = request.get_json()
    data = req.get("data")
    source_lang = req.get("source_lang")
    target_lang = req.get("target_lang")
    current_app.logger.info(f"Received translation request: {req}")
    
    if not data or not source_lang or not target_lang:
        return jsonify({"error": "Missing required fields, target_lang or source_lang"}), 400

    try:
        translated = translate_dict(data, source_lang, target_lang)
        return jsonify({"translated": translated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
