from django.core.management.base import BaseCommand
from ai.models import Organizational
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import random

class Command(BaseCommand):
    help = "Advanced NLP Paraphrasing Augmentation for Organizational"

    def add_arguments(self, parser):
        parser.add_argument('--copies', type=int, default=2)

    def handle(self, *args, **options):

        copies = options['copies']

        self.stdout.write("Loading paraphraser model...")

        tokenizer = AutoTokenizer.from_pretrained("persiannlp/paraphraser-mt5-small")
        model = AutoModelForSeq2SeqLM.from_pretrained("persiannlp/paraphraser-mt5-small")

        objs = Organizational.objects.all()

        def paraphrase(text):
            input_ids = tokenizer.encode(text, return_tensors="pt")
            outputs = model.generate(
                input_ids,
                max_length=60,
                num_return_sequences=1,
                temperature=0.8,
                top_p=0.90,
                do_sample=True
            )
            return tokenizer.decode(outputs[0], skip_special_tokens=True)

        count = 0

        for obj in objs:

            for _ in range(copies):
                try:
                    new_title = paraphrase(obj.Title)

                    # اگر بازنویسی خیلی شبیه بود، رد می‌کنیم
                    if len(new_title) < 3 or new_title == obj.Title:
                        continue

                    Organizational.objects.create(
                        Grouh=obj.Grouh,
                        Category=obj.Category,
                        Sarfasl=obj.Sarfasl,
                        contorol=obj.contorol,
                        Title=new_title
                    )
                    count += 1

                except Exception as e:
                    print("Error in paraphrasing:", e)
                    continue

        self.stdout.write(self.style.SUCCESS(
            f"Advanced augmentation completed! {count} new rows added."
        ))
