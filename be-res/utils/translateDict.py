import json
import re
from deep_translator import GoogleTranslator
from flask import current_app

from utils.cacheDB import cache_translation, get_cached_translation

ignore_translate = ['id', 'price', 'total', 'amount', 'vat', 'creator', 'create_time', 'modifier', 'modify_time', 'is_active', 'log_time', 'quantity', 'image']

# Đọc từ điển món ăn từ file cấu hình JSON
def load_menu_dict(config_file='menu_config.json'):
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            menu_dict = json.load(file)
        return menu_dict
    except Exception as e:
        print(f"❌ Lỗi khi đọc file cấu hình: {e}")
        return {}

def translate_dict(text, target_lang, source_lang, config_file='menu_config.json'):
    if target_lang == source_lang:
        return text
    menu_dict = load_menu_dict(config_file)
    try:
        if isinstance(text, dict):
            result = {}
            for k, v in text.items():
                if any(re.search(r'\b' + word + r'\b', str(v), re.IGNORECASE) for word in ignore_translate):
                    result[k] = v  
                elif isinstance(v, str):  
                    cached = get_cached_translation(v, source_lang, target_lang)
                    
                    if cached:
                        current_app.logger.debug(f"data on cache: {cached}")
                        result[k] = cached
                    elif v in menu_dict and target_lang =="vi":
                        result[k] = menu_dict[v]  
                    else:
                        try:
                            result[k] = GoogleTranslator(source=source_lang, target=target_lang).translate(v)
                            cache_translation(v,source_lang,target_lang,result[k])
                        except Exception as e:
                            current_app.logger.error(f"Lỗi khi dịch văn bản: {e}")
                            result[k] = v  
                else:
                    result[k] = v  
            return result
        if isinstance(text,str):
            result = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        else:
            return text
    except Exception as e:
        current_app.logger.error(f"Lỗi khi dịch văn bản: {e}")
        return text
