# consumers.py
import json
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from ai.service.predict import LightPredictor  # مسیر خودت رو چک کن


class PredictionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # یک بار مدل رو لود می‌کنیم تا هر درخواست سریع باشه
        self.predictor = LightPredictor()

        await self.send(text_data=json.dumps({
            "message": "WebSocket connection established"
        }))

    async def disconnect(self, close_code):
        print(f"Client disconnected (code={close_code})")

    async def receive(self, text_data):
        try:
            payload = json.loads(text_data)

            # ──────── بررسی کلید امنیتی ────────
            received_secret = payload.get("SECRET_KEY") or payload.get("secret")
            expected_secret = getattr(settings, "PREDICT_SECRET_KEY", "123")  # اگه تو settings نبود، 123 قبول می‌شه

            if received_secret != expected_secret:
                await self.send(text_data=json.dumps({
                    "error": "Invalid secret key"
                }))
                return

            # ──────── حالت مدل ────────
            mode = str(payload.get("mode", "organizational")).strip().lower()
            if mode not in ["organizational", "indexing"]:
                await self.send(text_data=json.dumps({
                    "error": "mode باید 'organizational' یا 'indexing' باشد"
                }))
                return

            # ──────── ساخت payload کامل برای predict.py ────────
            input_for_predictor = {
                "data": payload.get("data", []),
                # حتی اگه با حرف بزرگ یا اسم قدیمی فرستاده باشه، قبول می‌کنه
                "control": (
                    payload.get("control") or
                    payload.get("Control") or
                    payload.get("CONTROL") or
                    payload.get("contorol") or
                    payload.get("contorol1") or
                    []
                ),
                "mapping": payload.get("mapping", {})
            }

            # ──────── اجرای مدل در ترد جدا (غیرمسدودکننده) ────────
            prediction_result = await sync_to_async(self.predictor.predict)(
                input_for_predictor, mode
            )

            # ──────── ارسال نتیجه به فرانت‌اند ────────
            await self.send(text_data=json.dumps({
                "status": "success",
                "result": prediction_result
            }, ensure_ascii=False))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "JSON نامعتبر است"
            }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                "status": "error",
                "message": f"خطا در پردازش: {str(e)}"
            }))