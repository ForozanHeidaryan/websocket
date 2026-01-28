import os
import joblib
import re
import numpy as np
from hazm import Normalizer, word_tokenize, stopwords_list
from difflib import get_close_matches
from scipy.sparse import hstack, csr_matrix

# ------------------------------------------------------------------
# پیش‌پردازش متن (مطابق train_dual_rf.py)
normalizer = Normalizer()
stopwords = set(stopwords_list())

def ultra_normalize(text: str) -> str:
    if not text:
        return ""
    t = str(text)
    t = t.replace("\u200c", "").replace("\u200f", "")
    t = t.replace("ي", "ی").replace("ك", "ک").replace("ئ", "ی")
    t = t.replace("\r", "").replace("\n", "").replace("\t", "")
    t = normalizer.normalize(t)
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'[^\w\s\u0600-\u06FF0-9]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return t

def preprocess_text(text: str) -> str:
    t = ultra_normalize(text)
    tokens = word_tokenize(t)
    tokens = [tok for tok in tokens if tok not in stopwords and len(tok) > 1 and not tok.isdigit()]
    return " ".join(tokens)

# ------------------------------------------------------------------
# نرمال‌سازی برچسب‌ها
ARABIC_NUMS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

def normalize_label_strong(text: str) -> str:
    if text is None:
        return "نامشخص"

    t = str(text)
    t = ''.join(c for c in t if c.isprintable())
    t = t.replace("\u200c", "").replace("\u200f", "")
    t = t.replace("ي", "ی").replace("ك", "ک").replace("ئ", "ی")
    t = t.replace("ۀ", "ه").replace("ة", "ه")

    # تبدیل اعداد عربی و فارسی به انگلیسی
    t = t.translate(ARABIC_NUMS)

    t = re.sub(r'[^\u0600-\u06FF0-9\s]', ' ', t)


    t = re.sub(r'\s+', ' ', t).strip().lower()

    t = t.replace(' ', '')

    return t if t else "نامشخص"



def normalize_category_preserve_numbers(val):
    if val is None:
        return "نامشخص"
    return str(val).replace(" ", "").replace("\u200c", "")

# ------------------------------------------------------------------
class LightPredictor:
    """
    Predictor سازگار با train_dual_rf.py
    پشتیبانی هر دو جدول organizational و indexing
    """

    def __init__(self, table_name="organizational"):
        assert table_name in ("organizational", "indexing")
        self.table = table_name
        self.model_dir = os.path.join("media", "models")

        # vectorizer
        self.vectorizer = joblib.load(os.path.join(self.model_dir, f"{table_name}_vectorizer.joblib"))

        # models & encoders
        self.models = {}
        self.encoders = {}

        for col in ["Category", "Grouh", "Sarfasl", "contorol"]:
            model_path = os.path.join(self.model_dir, f"{table_name}_{col}_model.joblib")
            encoder_path = os.path.join(self.model_dir, f"{table_name}_{col}_encoder.joblib")
            if os.path.exists(model_path) and os.path.exists(encoder_path):
                self.models[col] = joblib.load(model_path)
                self.encoders[col] = joblib.load(encoder_path)

    # ------------------------------------------------------------------
    def predict_batch(self, payload: dict):
        rows = payload.get("data", [])
        mapping = payload.get("mapping", {})

        # mapping dictionaries
        grouhs_map = {normalize_label_strong(x["Name"]): x["ID"] for x in mapping.get("grouhs", [])}
        sarfasls_map = {normalize_label_strong(x["Name"]): x["ID"] for x in mapping.get("sarfasls", [])}
        categories_map = {normalize_category_preserve_numbers(x["Name"]): x["ID"] for x in mapping.get("categories", [])}
        controls_map = {normalize_label_strong(x["Name"]): x["ID"] for x in mapping.get("contorol", [])}

        # نگهداری Category سطح ۱ برای Level 2
        level1_categories = {}

        outputs = []

        for row in rows:
            rid = row.get("ID")
            title = row.get("Name", "")
            level = row.get("LevelNumber", 1)
            parent_id = row.get("ParentId")

            clean_title = preprocess_text(title)

            out = {
                "input_id": rid,
                "Category": 0,
                "Grouh": 0,
                "Sarfasl": 0,
                "Control": 0,
                "similarity": 1.0
            }

            if len(clean_title) < 2:
                outputs.append(out)
                continue

            X_text = self.vectorizer.transform([clean_title])

            # --------------------------------------------------
            # Level 1
            if level == 1:
                if "Category" in self.models:
                    idx = self.models["Category"].predict(X_text)[0]
                    cat_val = self.encoders["Category"].inverse_transform([idx])[0]
                    cat_val = normalize_category_preserve_numbers(cat_val)

                    level1_categories[rid] = cat_val
                    if cat_val in categories_map:
                        out["Category"] = categories_map[cat_val]

                if "Grouh" in self.models:
                    idx = self.models["Grouh"].predict(X_text)[0]
                    val = normalize_label_strong(self.encoders["Grouh"].inverse_transform([idx])[0])
                    if val in grouhs_map:
                        out["Grouh"] = grouhs_map[val]

                if "Sarfasl" in self.models:
                    idx = self.models["Sarfasl"].predict(X_text)[0]
                    val = normalize_label_strong(self.encoders["Sarfasl"].inverse_transform([idx])[0])
                    if val in sarfasls_map:
                        out["Sarfasl"] = sarfasls_map[val]

            # --------------------------------------------------
            # Level 2 — contorol
            elif level == 2 and "contorol" in self.models:
                parent_cat = level1_categories.get(parent_id, "0")

                if self.table == "organizational":
                    try:
                        cat_feature = int(parent_cat)
                    except:
                        cat_feature = 0
                else:  # indexing: حروف لاتین → عدد یکتا برای مدل
                    cat_feature = hash(parent_cat) % 10**8

                X_final = hstack([X_text, csr_matrix([[cat_feature]])])

                idx = self.models["contorol"].predict(X_final)[0]
                val = normalize_label_strong(self.encoders["contorol"].inverse_transform([idx])[0])

                if val in controls_map:
                    out["Control"] = controls_map[val]
                else:
                    close = get_close_matches(val, list(controls_map.keys()), n=1, cutoff=0.88)
                    if close:
                        out["Control"] = controls_map[close[0]]

            outputs.append(out)

        return {"status": "success", "result": {self.table: outputs}}

    # ------------------------------------------------------------------
    # API compatibility
    def run(self, data, *args, **kwargs):
        return self.predict_batch(data)

    predict = run
