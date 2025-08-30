# ai/service/predict.py
import os
import re
import joblib
import numpy as np
from django.conf import settings
from hazm import word_tokenize, Normalizer, stopwords_list, Stemmer
from sklearn.metrics.pairwise import cosine_similarity


class PredictCustomersData:
    def __init__(self, input_payload):
        """
        input_payload: dict با دو کلید اصلی:
          - "data": لیست دیکشنری‌ها {"Id":..., "Title":...}
          - "mapping": dict اختیاری {"categories": [...], "sarfasls": [...], "grouhs": [...]}
        """
        self.normalizer = Normalizer()
        self.stopwords = set(stopwords_list())
        self.stemmer = Stemmer()
        self.__model_path = os.path.join(settings.MEDIA_ROOT, "models")

        if not isinstance(input_payload, dict):
            raise ValueError("ورودی باید دیکشنری باشد.")

        self.data_list = input_payload.get("data", [])
        if not isinstance(self.data_list, list):
            raise ValueError("کلید 'data' باید لیست باشد.")
        for item in self.data_list:
            if "Title" not in item:
                raise ValueError("هر آیتم در data باید فیلد 'Title' داشته باشد.")

        self.mapping = input_payload.get("mapping", {}) or {}

    def execute(self):
        texts = [self._preprocess_to_string(item.get("Title", "")) for item in self.data_list]
        ids = [item.get("Id") for item in self.data_list]

        vec = self._load_joblib("vectorizer.joblib")
        X = vec.transform(texts)

        # پیش‌بینی‌ها
        rf1 = self._load_joblib("RF_model_y1.joblib")
        enc1 = self._load_joblib("encoder1.joblib")
        preds_cat = enc1.inverse_transform(rf1.predict(X))

        rf2 = self._load_joblib("RF_model_y2.joblib")
        enc2 = self._load_joblib("encoder2.joblib")
        preds_sar = enc2.inverse_transform(rf2.predict(X))

        rf3 = self._load_joblib("RF_model_y3.joblib")
        enc3 = self._load_joblib("encoder3.joblib")
        preds_gro = enc3.inverse_transform(rf3.predict(X))

        # محاسبه similarity
        try:
            vec_train = self._load_joblib("vec_title.joblib")
            sim = cosine_similarity(X, vec_train)
            sim_scores = np.max(sim, axis=1).astype(float).tolist()
        except Exception:
            sim_scores = [None] * len(texts)

        # ساخت نتایج اولیه فقط با Id و similarity
        results = []
        for i in range(len(texts)):
            results.append({
                "Id": ids[i],
                "similarity": sim_scores[i],
                "_pred_cat": preds_cat[i],
                "_pred_sar": preds_sar[i],
                "_pred_gro": preds_gro[i],
            })

        # mapping اختیاری: فقط IDهای متناظر را اضافه می‌کنیم
        if self.mapping:
            results = self._map_predictions_to_ids(results)

        # حذف فیلدهای پیش‌بینی برای خروجی نهایی
        for r in results:
            r.pop("_pred_cat", None)
            r.pop("_pred_sar", None)
            r.pop("_pred_gro", None)

        return results

    # ---------- توابع کمکی ----------
    def _preprocess_to_string(self, text):
        if text is None:
            text = ""
        text = self.normalizer.normalize(str(text))
        text = text.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
        tokens = word_tokenize(text)
        tokens = [t for t in tokens if t not in self.stopwords]
        stems = [self.stemmer.stem(t) for t in tokens]
        return " ".join(stems)

    def _normalize_for_map(self, text):
        if text is None:
            return ""
        s = str(text)
        s = s.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
        s = s.replace("‌", " ")
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^\w\s]", "", s)
        return s.strip().lower()

    def _map_predictions_to_ids(self, results):
        # ساخت دیکشنری mapping ها
        def build_map(items, id_field, name_field):
            m = {}
            for x in items or []:
                _id = x.get(id_field)
                _name = x.get(name_field)
                if _id is not None and _name:
                    m[self._normalize_for_map(_name)] = _id
            return m

        cat_map = build_map(self.mapping.get("categories", []), "Category_id", "Category")
        sar_map = build_map(self.mapping.get("sarfasls", []), "Sarfasl_id", "Sarfasl")
        gro_map = build_map(self.mapping.get("grouhs", []), "Grouh_id", "Grouh")

        enriched = []
        for r in results:
            enriched.append({
                "Id": r["Id"],
                "CategoryId": cat_map.get(self._normalize_for_map(r["_pred_cat"])),
                "SarfaslId": sar_map.get(self._normalize_for_map(r["_pred_sar"])),
                "GrouhId": gro_map.get(self._normalize_for_map(r["_pred_gro"])),
                "similarity": r["similarity"],
            })
        return enriched

    def _load_joblib(self, filename):
        path = os.path.join(self.__model_path, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"فایل مدل یافت نشد: {path}")
        return joblib.load(path)
