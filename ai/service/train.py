import os
import joblib
import re
import numpy as np
from hazm import Normalizer, word_tokenize, stopwords_list
from rapidfuzz import fuzz

# ------------------------------------------------------------------
normalizer = Normalizer()
stopwords = set(stopwords_list())

def ultra_normalize(text: str) -> str:
    if not text:
        return ""
    t = str(text)
    t = t.replace("\u200c", "")
    t = t.replace("ي", "ی").replace("ك", "ک").replace("ئ", "ی")
    t = t.replace("\r", "").replace("\n", "").replace("\t", "")
    t = normalizer.normalize(t)
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'[^\w\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return t

def preprocess_text(text: str) -> str:
    t = ultra_normalize(text)
    tokens = word_tokenize(t)
    tokens = [tok for tok in tokens if tok not in stopwords and len(tok) > 1 and not tok.isdigit()]
    return " ".join(tokens)

# ------------------------------------------------------------------
MODEL_DIR = os.path.join("media", "models")
vectorizer = joblib.load(os.path.join(MODEL_DIR, "organizational_vectorizer.joblib"))

models = {}
encoders = {}
for col in ["Category", "Grouh", "Sarfasl", "contorol"]:
    model_path = os.path.join(MODEL_DIR, f"organizational_{col}_model.joblib")
    enc_path = os.path.join(MODEL_DIR, f"organizational_{col}_encoder.joblib")
    if os.path.exists(model_path) and os.path.exists(enc_path):
        models[col] = joblib.load(model_path)
        encoders[col] = joblib.load(enc_path)

# ------------------------------------------------------------------
def predict_batch(input_json: dict):
    data_rows = input_json.get("data", [])
    mapping = input_json.get("mapping", {})
    results = []

    grouhs_map = {ultra_normalize(g["Name"]): g["ID"] for g in mapping.get("grouhs", [])}
    sarfasls_map = {ultra_normalize(s["Name"]): s["ID"] for s in mapping.get("sarfasls", [])}
    categories_map = {}
    for c in mapping.get("categories", []):
        name = str(c.get("Name", "")).strip()
        if name.isdigit():
            categories_map[name] = c["ID"]
        else:
            categories_map[ultra_normalize(name)] = c["ID"]

    for row in data_rows:
        input_id = row.get("ID")
        title = row.get("Name", "")
        clean_title = preprocess_text(title)

        if len(clean_title) < 2:
            results.append({"input_id": input_id, "similarity": 0, "Category": 0, "Grouh": 0, "Sarfasl": 0, "Control": 0})
            continue

        X = vectorizer.transform([clean_title])
        out = {"input_id": input_id, "similarity": 1.0, "Category": 0, "Grouh": 0, "Sarfasl": 0, "Control": 0}

        # Category
        if "Category" in models:
            try:
                pred = encoders["Category"].inverse_transform(models["Category"].predict(X))[0]
                pred_str = str(pred).strip()
                if pred_str in categories_map:
                    out["Category"] = categories_map[pred_str]
            except:
                pass

        # Grouh — حالا با مدل قوی‌تر (Logistic) و تمیزکاری کامل
        if "Grouh" in models:
            try:
                pred_idx = models["Grouh"].predict(X)[0]
                raw_pred = encoders["Grouh"].inverse_transform([pred_idx])[0]
                key = ultra_normalize(raw_pred)
                if key in grouhs_map:
                    out["Grouh"] = grouhs_map[key]
            except:
                pass

        # Sarfasl
        if "Sarfasl" in models:
            try:
                pred_idx = models["Sarfasl"].predict(X)[0]
                raw_pred = encoders["Sarfasl"].inverse_transform([pred_idx])[0]
                key = ultra_normalize(raw_pred)
                if key in sarfasls_map:
                    out["Sarfasl"] = sarfasls_map[key]
            except:
                pass

        # Control
        if "contorol" in models:
            try:
                pred = encoders["contorol"].inverse_transform(models["contorol"].predict(X))[0]
                out["Control"] = int(pred) if str(pred).isdigit() else 0
            except:
                out["Control"] = 0

        results.append(out)

    return {"status": "success", "result": {"organizational": results}}

# ------------------------------------------------------------------
class LightPredictor:
    def __init__(self):
        pass
    def run(self, data, *args, **kwargs):
        return predict_batch(data)
    predict = run