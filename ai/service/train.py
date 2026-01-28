# ai/train_dual_rf.py
# آموزش با RandomForest — هم Organizational و هم Indexing

import os
import django
import joblib
import re
import numpy as np
import difflib
from collections import Counter
from hazm import Normalizer, word_tokenize, stopwords_list
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder
from scipy.sparse import hstack

# ------------------------------------------------------
# ستاپ جنگو
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HadiHesabAI.settings")
django.setup()
from ai.models import Organizational, Indexing

# ------------------------------------------------------
# پیش‌پردازش متن
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
    t = re.sub(r'[^\w\s\u0600-\u06FF0-9]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return t

def preprocess_text(text: str) -> str:
    t = ultra_normalize(text)
    tokens = word_tokenize(t)
    tokens = [tok for tok in tokens if tok not in stopwords and len(tok) > 1 and not tok.isdigit()]
    return " ".join(tokens)

# ------------------------------------------------------
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


def build_merge_map(unique_labels, freq_map=None, threshold=0.88):
    labels = list(unique_labels)
    if freq_map:
        labels.sort(key=lambda x: (-freq_map.get(x, 0), -len(x)))
    else:
        labels.sort(key=lambda x: -len(x))
    canonical = []
    mapping = {}
    for lab in labels:
        if not lab or lab == "نامشخص":
            mapping[lab] = "نامشخص"
            continue
        mapped = False
        for can in canonical:
            ratio = difflib.SequenceMatcher(None, lab, can).ratio()
            if ratio >= threshold:
                mapping[lab] = can
                mapped = True
                break
        if not mapped:
            canonical.append(lab)
            mapping[lab] = lab
    return mapping

def merge_labels_dynamic(labels_list, threshold=0.88):
    normalized = [normalize_label_strong(x) for x in labels_list]
    cnt = Counter(normalized)
    unique = list(cnt.keys())
    mapping = build_merge_map(unique, freq_map=cnt, threshold=threshold)
    merged = [mapping.get(x, x) for x in normalized]
    stats = {
        "original_unique": len(set(labels_list)),
        "normalized_unique": len(unique),
        "merged_unique": len(set(merged)),
        "mapping_sample": dict(list(mapping.items())[:30])
    }
    return merged, mapping, stats

def normalize_category_preserve_numbers(val):
    if val is None:
        return "نامشخص"
    s = str(val).replace(" ", "").replace("\u200c", "")
    return s

# ------------------------------------------------------
def train_table(table_name):
    if table_name == "organizational":
        Model = Organizational
        model_prefix = "organizational"
    elif table_name == "indexing":
        Model = Indexing
        model_prefix = "indexing"
    else:
        raise ValueError("نام جدول نامعتبر است!")

    print(f"\nآموزش با RandomForest برای جدول {table_name} — نسخه اصلاح‌شده و یکپارچه‌سازی کلاس‌ها (LevelNumber-based)")

    data = Model.objects.all().values_list("Title", "Category", "Grouh", "Sarfasl", "contorol", "LevelNumber")

    texts = []
    labels = {"Category": [], "Grouh": [], "Sarfasl": [], "contorol": [], "LevelNumber": []}
    raw_rows = []
    for row in data.iterator():
        title = str(row[0] or "").strip()
        if not title or len(title) < 3:
            continue
        clean_title = preprocess_text(title)
        if len(clean_title) < 2:
            continue
        raw_rows.append((clean_title, row[1], row[2], row[3], row[4], row[5]))

    for r in raw_rows:
        texts.append(r[0])
        labels["Category"].append(str(r[1]).strip() if r[1] is not None else "نامشخص")
        labels["Grouh"].append(r[2])
        labels["Sarfasl"].append(r[3])
        labels["contorol"].append(r[4])
        labels["LevelNumber"].append(r[5])

    print(f"تعداد نمونه: {len(texts)}")

    # merge Grouh, Sarfasl, contorol
    for col in ["Grouh", "Sarfasl", "contorol"]:
        normalized_labels = [normalize_label_strong(x) for x in labels[col]]
        merged_list, mapping_used, stats = merge_labels_dynamic(normalized_labels, threshold=0.88)
        labels[col] = merged_list
        print(f"\nستون: {col}")
        print(f"  unique (merged)   : {stats['merged_unique']}")
        print(f"  mapping نمونه     : {list(mapping_used.items())[:10]}")

    # normalize Category
    labels["Category"] = [normalize_category_preserve_numbers(x) for x in labels["Category"]]

    # Vectorizer
    vectorizer = CountVectorizer(ngram_range=(1, 3), min_df=1, max_features=20000)
    X = vectorizer.fit_transform(texts)
    os.makedirs("media/models", exist_ok=True)
    joblib.dump(vectorizer, f"media/models/{model_prefix}_vectorizer.joblib")

    # train models
    encoders = {}
    models = {}

    for col in ["Category", "Grouh", "Sarfasl", "contorol"]:
        print(f"\nآموزش {col}...")
        y = np.array(labels[col])
        level_numbers = np.array(labels["LevelNumber"])

        if col in ["Category", "Grouh", "Sarfasl"]:
            valid_idx = [i for i, v in enumerate(y) if v and v != "نامشخص" and str(v).strip() and level_numbers[i] == 1]
            X_valid = X[valid_idx]
            y_valid = y[valid_idx]
            encoder = LabelEncoder()
            y_encoded = encoder.fit_transform(y_valid)
            encoders[col] = encoder
            joblib.dump(encoder, f"media/models/{model_prefix}_{col}_encoder.joblib")
            if len(np.unique(y_encoded)) <= 1:
                model = DummyClassifier(strategy="constant", constant=y_encoded[0])
                model.fit(np.zeros((len(y_encoded), 1)), y_encoded)
                print(" → فقط یک کلاس وجود داشت (DummyClassifier)")
            else:
                model = RandomForestClassifier(n_estimators=300, max_depth=None, random_state=42, n_jobs=-1)
                model.fit(X_valid, y_encoded)
            models[col] = model
            joblib.dump(model, f"media/models/{model_prefix}_{col}_model.joblib")
            print(f" → {col} آموزش داده شد — {len(encoder.classes_)} کلاس")
        else:
            # contorol — Level 2
            valid_idx = [i for i, v in enumerate(y) if v is not None and str(v).strip() and level_numbers[i] == 2]
            X_level2_texts = [texts[i] for i in valid_idx]
            X_level2_category = [labels["Category"][i] for i in valid_idx]
            X_text_vec = vectorizer.transform(X_level2_texts)

            # تبدیل Category به عدد برای ورودی مدل Level 2
            if table_name == "organizational":
                X_category_vec = np.array(X_level2_category, dtype=np.int32).reshape(-1, 1)
            else:  # indexing: حروف لاتین → عدد یکتا برای مدل
                le_indexing = LabelEncoder()
                X_category_vec = le_indexing.fit_transform(X_level2_category).reshape(-1, 1)

            X_valid = hstack([X_text_vec, X_category_vec])
            y_valid = y[valid_idx]
            encoder = LabelEncoder()
            y_encoded = encoder.fit_transform(y_valid)
            encoders[col] = encoder
            joblib.dump(encoder, f"media/models/{model_prefix}_{col}_encoder.joblib")
            if len(np.unique(y_encoded)) <= 1:
                model = DummyClassifier(strategy="constant", constant=y_encoded[0])
                model.fit(np.zeros((len(y_encoded), 1)), y_encoded)
                print(" → فقط یک کلاس وجود داشت (DummyClassifier)")
            else:
                model = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
                model.fit(X_valid, y_encoded)
            models[col] = model
            joblib.dump(model, f"media/models/{model_prefix}_{col}_model.joblib")
            print(f" → {col} آموزش داده شد — {len(encoder.classes_)} کلاس")

    print(f"\n🎉 مدل RandomForest جدول {table_name} با موفقیت ساخته شد!")
    return models, encoders, vectorizer

# ------------------------------------------------------
if __name__ == "__main__":
    # آموزش هر دو جدول
    train_table("organizational")
    train_table("indexing")
