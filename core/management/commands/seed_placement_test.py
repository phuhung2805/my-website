"""
seed_placement_test.py – Script khởi tạo dữ liệu câu hỏi bài kiểm tra đầu vào (Placement Test).
Chạy lệnh: python manage.py seed_placement_test
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import PlacementQuestion, PlacementChoice

from ._level_up_questions import LEVEL_UP_QUESTIONS


SAMPLE_QUESTIONS = [
    # ----------------------------------------------------
    # Level A1 (Căn bản - 10 câu)
    # ----------------------------------------------------
    {
        "order": 1,
        "level": "A1",
        "question_text": "She _______ from Vietnam. She is twenty years old.",
        "choices": [
            ("am", False),
            ("is", True),
            ("are", False),
            ("be", False),
        ],
    },
    {
        "order": 2,
        "level": "A1",
        "question_text": "What time _______ you usually wake up in the morning?",
        "choices": [
            ("do", True),
            ("does", False),
            ("are", False),
            ("did", False),
        ],
    },
    {
        "order": 3,
        "level": "A1",
        "question_text": "There are four _______ on the table.",
        "choices": [
            ("apple", False),
            ("apples", True),
            ("an apple", False),
            ("appleses", False),
        ],
    },
    {
        "order": 4,
        "level": "A1",
        "question_text": "I cannot find my keys. Have you seen _______?",
        "choices": [
            ("they", False),
            ("them", True),
            ("their", False),
            ("it", False),
        ],
    },
    {
        "order": 5,
        "level": "A1",
        "question_text": "My brother _______ like drinking coffee. He prefers tea.",
        "choices": [
            ("doesn't", True),
            ("don't", False),
            ("isn't", False),
            ("aren't", False),
        ],
    },
    {
        "order": 6,
        "level": "A1",
        "question_text": "Where _______ you go yesterday evening?",
        "choices": [
            ("did", True),
            ("do", False),
            ("was", False),
            ("were", False),
        ],
    },
    {
        "order": 7,
        "level": "A1",
        "question_text": "This book is very interesting, but that one is _______ boring.",
        "choices": [
            ("a bit", True),
            ("much", False),
            ("many", False),
            ("few", False),
        ],
    },
    {
        "order": 8,
        "level": "A1",
        "question_text": "Can you help me carry this bag? It is very _______.",
        "choices": [
            ("heavy", True),
            ("light", False),
            ("small", False),
            ("thin", False),
        ],
    },
    {
        "order": 9,
        "level": "A1",
        "question_text": "We have English class _______ Monday and Thursday mornings.",
        "choices": [
            ("on", True),
            ("in", False),
            ("at", False),
            ("to", False),
        ],
    },
    {
        "order": 10,
        "level": "A1",
        "question_text": "_______ is your favorite color? - It is navy blue.",
        "choices": [
            ("What", True),
            ("Who", False),
            ("When", False),
            ("Where", False),
        ],
    },

    # ----------------------------------------------------
    # Level A2 (Sơ cấp - 10 câu)
    # ----------------------------------------------------
    {
        "order": 11,
        "level": "A2",
        "question_text": "Yesterday, my family and I _______ a very interesting movie at the cinema.",
        "choices": [
            ("watch", False),
            ("watched", True),
            ("watching", False),
            ("have watched", False),
        ],
    },
    {
        "order": 12,
        "level": "A2",
        "question_text": "Traveling by airplane is much _______ than traveling by train.",
        "choices": [
            ("fast", False),
            ("faster", True),
            ("more fast", False),
            ("fastest", False),
        ],
    },
    {
        "order": 13,
        "level": "A2",
        "question_text": "Look at those dark clouds! It _______ rain very soon.",
        "choices": [
            ("is going to", True),
            ("will to", False),
            ("goes to", False),
            ("is raining", False),
        ],
    },
    {
        "order": 14,
        "level": "A2",
        "question_text": "He was very tired, _______ he still finished all his homework before bed.",
        "choices": [
            ("because", False),
            ("so", False),
            ("but", True),
            ("although", False),
        ],
    },
    {
        "order": 15,
        "level": "A2",
        "question_text": "I haven't seen Sarah _______ last week's conference.",
        "choices": [
            ("since", True),
            ("for", False),
            ("from", False),
            ("until", False),
        ],
    },
    {
        "order": 16,
        "level": "A2",
        "question_text": "You _______ wear a helmet when riding a motorbike; it is the law.",
        "choices": [
            ("must", True),
            ("might", False),
            ("can", False),
            ("would", False),
        ],
    },
    {
        "order": 17,
        "level": "A2",
        "question_text": "If it rains tomorrow, we _______ stay at home and watch television.",
        "choices": [
            ("will", True),
            ("would", False),
            ("did", False),
            ("are", False),
        ],
    },
    {
        "order": 18,
        "level": "A2",
        "question_text": "While my mother was cooking dinner, my father _______ the garden.",
        "choices": [
            ("was watering", True),
            ("watered", False),
            ("is watering", False),
            ("waters", False),
        ],
    },
    {
        "order": 19,
        "level": "A2",
        "question_text": "She wants to know _______ to bake chocolate cookies.",
        "choices": [
            ("how", True),
            ("what", False),
            ("which", False),
            ("why", False),
        ],
    },
    {
        "order": 20,
        "level": "A2",
        "question_text": "Would you mind _______ the window? It is quite noisy outside.",
        "choices": [
            ("closing", True),
            ("close", False),
            ("to close", False),
            ("closed", False),
        ],
    },

    # ----------------------------------------------------
    # Level B1 (Trung cấp - 10 câu)
    # ----------------------------------------------------
    {
        "order": 21,
        "level": "B1",
        "question_text": "I _______ in this international company for over five years, and I really enjoy it.",
        "choices": [
            ("work", False),
            ("worked", False),
            ("have worked", True),
            ("am working", False),
        ],
    },
    {
        "order": 22,
        "level": "B1",
        "question_text": "If I _______ more free time, I would participate in the English speaking club.",
        "choices": [
            ("have", False),
            ("had", True),
            ("will have", False),
            ("would have", False),
        ],
    },
    {
        "order": 23,
        "level": "B1",
        "question_text": "The student _______ essay won the first prize will receive a scholarship.",
        "choices": [
            ("who", False),
            ("which", False),
            ("whose", True),
            ("whom", False),
        ],
    },
    {
        "order": 24,
        "level": "B1",
        "question_text": "The historical museum _______ by thousands of tourists every summer.",
        "choices": [
            ("visited", False),
            ("was visited", False),
            ("is visited", True),
            ("is visiting", False),
        ],
    },
    {
        "order": 25,
        "level": "B1",
        "question_text": "She asked me where I _______ during my previous summer vacation.",
        "choices": [
            ("had gone", True),
            ("went", False),
            ("have gone", False),
            ("did go", False),
        ],
    },
    {
        "order": 26,
        "level": "B1",
        "question_text": "Despite _______ severely injured, the athlete managed to complete the marathon.",
        "choices": [
            ("being", True),
            ("to be", False),
            ("was", False),
            ("been", False),
        ],
    },
    {
        "order": 27,
        "level": "B1",
        "question_text": "You had better _______ your doctor before taking this strong medication.",
        "choices": [
            ("consult", True),
            ("to consult", False),
            ("consulting", False),
            ("consulted", False),
        ],
    },
    {
        "order": 28,
        "level": "B1",
        "question_text": "The meeting was postponed _______ the keynote speaker was delayed by heavy snow.",
        "choices": [
            ("because", True),
            ("although", False),
            ("despite", False),
            ("in spite of", False),
        ],
    },
    {
        "order": 29,
        "level": "B1",
        "question_text": "We need to find an effective solution to _______ pollution in urban areas.",
        "choices": [
            ("reduce", True),
            ("increase", False),
            ("maintain", False),
            ("destroy", False),
        ],
    },
    {
        "order": 30,
        "level": "B1",
        "question_text": "Neither the manager nor his assistants _______ present at the annual briefing.",
        "choices": [
            ("were", True),
            ("was", False),
            ("has been", False),
            ("is", False),
        ],
    },

    # ----------------------------------------------------
    # Level B2 (Trung cao cấp - 10 câu)
    # ----------------------------------------------------
    {
        "order": 31,
        "level": "B2",
        "question_text": "If she had followed the doctor's instructions strictly, she _______ sick today.",
        "choices": [
            ("wouldn't be", True),
            ("wouldn't have been", False),
            ("won't be", False),
            ("isn't", False),
        ],
    },
    {
        "order": 32,
        "level": "B2",
        "question_text": "Hardly _______ entered the laboratory when the experiment commenced.",
        "choices": [
            ("the researchers had", False),
            ("had the researchers", True),
            ("did the researchers", False),
            ("have the researchers", False),
        ],
    },
    {
        "order": 33,
        "level": "B2",
        "question_text": "The government has implemented strict measures to _______ carbon dioxide emissions.",
        "choices": [
            ("cut down on", True),
            ("put up with", False),
            ("look down on", False),
            ("carry away with", False),
        ],
    },
    {
        "order": 34,
        "level": "B2",
        "question_text": "Under no circumstances _______ unauthorized personnel to access the server room.",
        "choices": [
            ("are we permitted", True),
            ("we permit", False),
            ("we are permitting", False),
            ("we should permit", False),
        ],
    },
    {
        "order": 35,
        "level": "B2",
        "question_text": "The new policy is expected to stimulate economic growth, _______ enhancing public welfare.",
        "choices": [
            ("thereby", True),
            ("whereas", False),
            ("nevertheless", False),
            ("nonetheless", False),
        ],
    },
    {
        "order": 36,
        "level": "B2",
        "question_text": "Had I known about the flight cancellation earlier, I _______ other travel arrangements.",
        "choices": [
            ("would have made", True),
            ("will make", False),
            ("had made", False),
            ("make", False),
        ],
    },
    {
        "order": 37,
        "level": "B2",
        "question_text": "It is imperative that every candidate _______ by the examination regulations.",
        "choices": [
            ("abide", True),
            ("abides", False),
            ("abided", False),
            ("abiding", False),
        ],
    },
    {
        "order": 38,
        "level": "B2",
        "question_text": "Not only _______ the competition, but she also set a new national record.",
        "choices": [
            ("did she win", True),
            ("she won", False),
            ("she had won", False),
            ("wins she", False),
        ],
    },
    {
        "order": 39,
        "level": "B2",
        "question_text": "The CEO's ambiguous remarks gave _______ to widespread speculation in the financial market.",
        "choices": [
            ("rise", True),
            ("birth", False),
            ("way", False),
            ("place", False),
        ],
    },
    {
        "order": 40,
        "level": "B2",
        "question_text": "In retrospect, the decision to launch the product prematurely proved to be utterly _______.",
        "choices": [
            ("disastrous", True),
            ("miraculous", False),
            ("triumphant", False),
            ("prestigious", False),
        ],
    },
]


class Command(BaseCommand):
    help = "Tạo 40 câu bài đầu vào và 45 câu thi nâng band (hai ngân hàng đề riêng)."

    def handle(self, *args, **options):
        with transaction.atomic():
            for item in SAMPLE_QUESTIONS:
                self._save_question(
                    PlacementQuestion.EXAM_PLACEMENT,
                    item["order"],
                    item["level"],
                    item["question_text"],
                    item["choices"],
                )

            order = 0
            for level, questions in LEVEL_UP_QUESTIONS.items():
                for text, options_list, answer in questions:
                    order += 1
                    self._save_question(
                        PlacementQuestion.EXAM_LEVEL_UP,
                        order,
                        level,
                        text,
                        [(option, option == answer) for option in options_list],
                    )

        self.stdout.write(self.style.SUCCESS(
            f"Da cap nhat {len(SAMPLE_QUESTIONS)} cau dau vao va {order} cau thi nang band."
        ))

    @staticmethod
    def _save_question(exam_type, order, level, text, choices):
        question, _ = PlacementQuestion.objects.update_or_create(
            exam_type=exam_type,
            order=order,
            defaults={"level": level, "question_text": text},
        )
        question.choices.exclude(choice_text__in=[choice for choice, _ in choices]).delete()
        for choice_text, is_correct in choices:
            PlacementChoice.objects.update_or_create(
                question=question,
                choice_text=choice_text,
                defaults={"is_correct": is_correct},
            )
