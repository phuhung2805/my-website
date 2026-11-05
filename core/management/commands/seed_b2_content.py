"""
seed_b2_content.py – Nội dung học cho trình độ B2. Chạy lại nhiều lần không tạo bản trùng.
Lệnh: python manage.py seed_b2_content
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    Category,
    ListeningQuestion,
    ListeningTrack,
    ReadingPassage,
    ReadingQuestion,
    SpeakingPrompt,
    Vocabulary,
    WritingTask,
)

# (từ, IPA, nghĩa, từ loại, câu ví dụ, nhóm)
VOCABULARY = [
    ("accommodate", "/əˈkɒmədeɪt/", "đáp ứng, cung cấp chỗ ở", "verb", "The new hall can accommodate five hundred guests.", "travel"),
    ("acknowledge", "/əkˈnɒlɪdʒ/", "thừa nhận", "verb", "She acknowledged that the plan had some weaknesses.", "communication"),
    ("advocate", "/ˈædvəkeɪt/", "ủng hộ, bênh vực", "verb", "Many doctors advocate regular exercise for older people.", "professional"),
    ("allocate", "/ˈæləkeɪt/", "phân bổ", "verb", "The school allocated more money to its library.", "professional"),
    ("anticipate", "/ænˈtɪsɪpeɪt/", "dự đoán, lường trước", "verb", "We did not anticipate so many people arriving early.", "verbs"),
    ("assess", "/əˈses/", "đánh giá", "verb", "Teachers assess students through essays and projects.", "school"),
    ("assumption", "/əˈsʌmpʃn/", "giả định", "noun", "His argument rests on a false assumption.", "professional"),
    ("bias", "/ˈbaɪəs/", "sự thiên vị, định kiến", "noun", "The report was criticised for its political bias.", "communication"),
    ("burden", "/ˈbɜːdn/", "gánh nặng", "noun", "High rent is a heavy burden for young workers.", "professional"),
    ("coherent", "/kəʊˈhɪərənt/", "mạch lạc", "adjective", "A good essay presents a coherent argument.", "school"),
    ("collaborate", "/kəˈlæbəreɪt/", "cộng tác", "verb", "The two universities collaborate on climate research.", "school"),
    ("comprehensive", "/ˌkɒmprɪˈhensɪv/", "toàn diện", "adjective", "The guide gives a comprehensive overview of the city.", "adjectives"),
    ("consequence", "/ˈkɒnsɪkwəns/", "hậu quả", "noun", "Pollution has serious consequences for public health.", "health"),
    ("constraint", "/kənˈstreɪnt/", "sự hạn chế, ràng buộc", "noun", "Budget constraints forced the team to change its plan.", "professional"),
    ("contradict", "/ˌkɒntrəˈdɪkt/", "mâu thuẫn", "verb", "The latest figures contradict the earlier report.", "communication"),
    ("controversial", "/ˌkɒntrəˈvɜːʃl/", "gây tranh cãi", "adjective", "The new law remains highly controversial.", "adjectives"),
    ("crucial", "/ˈkruːʃl/", "cốt yếu", "adjective", "Sleep is crucial for memory and learning.", "adjectives"),
    ("deteriorate", "/dɪˈtɪəriəreɪt/", "xấu đi", "verb", "Air quality deteriorates quickly during the winter.", "nature"),
    ("diminish", "/dɪˈmɪnɪʃ/", "giảm bớt", "verb", "The pain diminished after a few days of rest.", "health"),
    ("disclose", "/dɪsˈkləʊz/", "tiết lộ", "verb", "The company refused to disclose its profits.", "communication"),
    ("diverse", "/daɪˈvɜːs/", "đa dạng", "adjective", "The city has a diverse population.", "people"),
    ("emerge", "/ɪˈmɜːdʒ/", "nổi lên, xuất hiện", "verb", "New evidence emerged during the investigation.", "verbs"),
    ("emphasise", "/ˈemfəsaɪz/", "nhấn mạnh", "verb", "The speaker emphasised the need for early action.", "communication"),
    ("enhance", "/ɪnˈhɑːns/", "nâng cao", "verb", "Regular reading can enhance your vocabulary.", "school"),
    ("evaluate", "/ɪˈvæljueɪt/", "đánh giá", "verb", "Researchers evaluated the effects of the new treatment.", "health"),
    ("evolve", "/ɪˈvɒlv/", "phát triển dần", "verb", "Languages evolve as societies change.", "verbs"),
    ("feasible", "/ˈfiːzəbl/", "khả thi", "adjective", "Is it feasible to finish the bridge by June?", "adjectives"),
    ("fluctuate", "/ˈflʌktʃueɪt/", "dao động", "verb", "Food prices fluctuate from month to month.", "food"),
    ("fundamental", "/ˌfʌndəˈmentl/", "cơ bản, nền tảng", "adjective", "Access to clean water is a fundamental need.", "adjectives"),
    ("hypothesis", "/haɪˈpɒθəsɪs/", "giả thuyết", "noun", "The experiment was designed to test the hypothesis.", "school"),
    ("implement", "/ˈɪmplɪment/", "thực hiện, triển khai", "verb", "The government will implement the policy next year.", "professional"),
    ("implication", "/ˌɪmplɪˈkeɪʃn/", "hàm ý, hệ quả", "noun", "The study has important implications for teachers.", "school"),
    ("incentive", "/ɪnˈsentɪv/", "sự khuyến khích", "noun", "Tax cuts give companies an incentive to invest.", "professional"),
    ("inevitable", "/ɪnˈevɪtəbl/", "không thể tránh khỏi", "adjective", "Some mistakes are inevitable when you learn a language.", "adjectives"),
    ("infrastructure", "/ˈɪnfrəstrʌktʃə(r)/", "cơ sở hạ tầng", "noun", "Poor infrastructure slows economic growth.", "travel"),
    ("innovative", "/ˈɪnəveɪtɪv/", "đổi mới, sáng tạo", "adjective", "The startup developed an innovative payment system.", "tech"),
    ("justify", "/ˈdʒʌstɪfaɪ/", "biện minh, chứng minh là đúng", "verb", "How can you justify such a high price?", "communication"),
    ("mitigate", "/ˈmɪtɪɡeɪt/", "giảm nhẹ", "verb", "Trees help to mitigate the effects of heat in cities.", "nature"),
    ("negotiate", "/nɪˈɡəʊʃieɪt/", "đàm phán", "verb", "The union negotiated a better contract for its members.", "professional"),
    ("notion", "/ˈnəʊʃn/", "khái niệm, ý niệm", "noun", "He rejected the notion that money brings happiness.", "professional"),
    ("obstacle", "/ˈɒbstəkl/", "trở ngại", "noun", "Lack of confidence is the biggest obstacle to speaking.", "school"),
    ("outcome", "/ˈaʊtkʌm/", "kết quả", "noun", "Nobody could predict the outcome of the election.", "professional"),
    ("perceive", "/pəˈsiːv/", "nhận thức, cảm nhận", "verb", "Children perceive risk differently from adults.", "people"),
    ("phenomenon", "/fəˈnɒmɪnən/", "hiện tượng", "noun", "Global migration is not a new phenomenon.", "nature"),
    ("prevalent", "/ˈprevələnt/", "phổ biến", "adjective", "The disease is most prevalent in tropical regions.", "health"),
    ("priority", "/praɪˈɒrəti/", "ưu tiên", "noun", "Safety must be our first priority.", "professional"),
    ("profound", "/prəˈfaʊnd/", "sâu sắc", "adjective", "The internet has had a profound effect on education.", "tech"),
    ("reinforce", "/ˌriːɪnˈfɔːs/", "củng cố", "verb", "Practice tests reinforce what students have learned.", "school"),
    ("reluctant", "/rɪˈlʌktənt/", "miễn cưỡng", "adjective", "He was reluctant to discuss his private life.", "adjectives"),
    ("resilient", "/rɪˈzɪliənt/", "kiên cường, phục hồi nhanh", "adjective", "Children are often more resilient than adults expect.", "people"),
    ("scrutiny", "/ˈskruːtəni/", "sự xem xét kỹ", "noun", "The minister's decisions came under close scrutiny.", "communication"),
    ("significant", "/sɪɡˈnɪfɪkənt/", "đáng kể", "adjective", "There was a significant rise in online sales.", "adjectives"),
    ("substantial", "/səbˈstænʃl/", "lớn, đáng kể", "adjective", "The project requires a substantial investment.", "professional"),
    ("sustainable", "/səˈsteɪnəbl/", "bền vững", "adjective", "We need more sustainable forms of transport.", "nature"),
    ("tendency", "/ˈtendənsi/", "xu hướng", "noun", "There is a growing tendency to work from home.", "professional"),
    ("undermine", "/ˌʌndəˈmaɪn/", "làm suy yếu", "verb", "Constant criticism can undermine a child's confidence.", "people"),
    ("unprecedented", "/ʌnˈpresɪdentɪd/", "chưa từng có", "adjective", "The city faced an unprecedented water shortage.", "nature"),
    ("vulnerable", "/ˈvʌlnərəbl/", "dễ bị tổn thương", "adjective", "Older people are more vulnerable to extreme heat.", "health"),
    ("widespread", "/ˈwaɪdspred/", "lan rộng, phổ biến", "adjective", "The storm caused widespread damage along the coast.", "weather"),
    ("workforce", "/ˈwɜːkfɔːs/", "lực lượng lao động", "noun", "Automation will change the skills the workforce needs.", "professional"),
]

READING = [
    (
        "The Four-Day Working Week (B2)",
        "Several companies have recently experimented with a four-day working week, keeping salaries unchanged "
        "while reducing working hours. Supporters argue that employees who are well rested concentrate better, "
        "take fewer days of sick leave and are less likely to look for another job. In one large trial, most of "
        "the participating firms reported that revenue remained stable and decided to continue the scheme after "
        "the trial had ended.\n\n"
        "Critics, however, point out that such results may not apply everywhere. The firms that volunteered were "
        "probably confident that the change would work, and many of them were small office-based businesses. "
        "Hospitals, schools and factories cannot simply close for an extra day, so they would need to hire more "
        "staff, which could raise costs substantially. Whether shorter weeks spread may depend less on the "
        "evidence than on whether employers believe the benefits outweigh the risks.",
        [
            ("What remained the same for workers in these experiments?",
             ["Their working hours", "Their salaries", "Their job titles", "Their office locations"], "Their salaries"),
            ("According to supporters, a shorter week makes employees...",
             ["more likely to change jobs", "less able to concentrate", "less likely to take sick leave", "more dependent on managers"],
             "less likely to take sick leave"),
            ("What did most firms in the large trial decide?",
             ["To stop the scheme immediately", "To reduce salaries", "To keep the scheme", "To hire more managers"], "To keep the scheme"),
            ("Why might the trial results not apply everywhere?",
             ["The firms were volunteers and mostly small offices", "The trial lasted only one day",
              "Employees refused to take part", "Revenue fell sharply in all firms"],
             "The firms were volunteers and mostly small offices"),
            ("What problem would hospitals and schools face?",
             ["They would lose all their customers", "They would need extra staff, raising costs",
              "They would have to close permanently", "They could not pay any salaries"],
             "They would need extra staff, raising costs"),
        ],
    ),
    (
        "Why Cities Are Planting Trees (B2)",
        "As summers become hotter, urban planners are paying closer attention to trees. Concrete and asphalt absorb "
        "heat during the day and release it slowly at night, which can make city centres several degrees warmer than "
        "the surrounding countryside. A street lined with mature trees provides shade and cools the air, reducing "
        "the need for air conditioning in nearby buildings.\n\n"
        "Planting alone is not enough, though. Young trees need regular watering for their first few years, and many "
        "die because this maintenance is underfunded. Choosing the right species also matters: a tree that thrives "
        "today may struggle in a much warmer climate decades from now. There is also a question of fairness. "
        "Wealthier neighbourhoods tend to have far more greenery than poorer ones, so some cities now direct new "
        "planting to the areas with the fewest trees.",
        [
            ("Why are city centres often warmer than the countryside?",
             ["They receive more sunlight", "Concrete and asphalt store and release heat",
              "They have more rain", "Wind is always stronger there"], "Concrete and asphalt store and release heat"),
            ("What benefit do mature street trees give nearby buildings?",
             ["Less need for air conditioning", "Lower building taxes", "Stronger walls", "More natural light"],
             "Less need for air conditioning"),
            ("Why do many young trees die?",
             ["They are planted too close to roads", "Their maintenance is underfunded",
              "People cut them down", "The soil contains too much water"], "Their maintenance is underfunded"),
            ("Why must planners think carefully about species?",
             ["Some species are too expensive to import", "Residents dislike certain colours",
              "A suitable tree today may not survive a warmer future", "Only one species can grow in cities"],
             "A suitable tree today may not survive a warmer future"),
            ("What is the fairness issue mentioned in the text?",
             ["Poorer areas have fewer trees", "Rich areas pay no taxes",
              "Only children benefit from trees", "Trees are planted only in parks"], "Poorer areas have fewer trees"),
        ],
    ),
    (
        "Learning in the Age of Search Engines (B2)",
        "Because almost any fact can now be found in seconds, some people question whether memorising information "
        "still matters. Psychologists disagree with the idea that it has become pointless. Knowledge stored in "
        "long-term memory allows us to understand new material quickly, because we connect it to what we already "
        "know. A student who has to look up every second word in a text will struggle to follow its argument.\n\n"
        "Research also suggests that people remember less when they expect information to remain available online, "
        "an effect sometimes called digital amnesia. This does not mean that technology harms learning in every case. "
        "Used deliberately, online tools can provide practice and immediate feedback. The danger lies in confusing "
        "the ability to find an answer with actually understanding it.",
        [
            ("What question do some people now ask?",
             ["Whether memorising information still matters", "Whether search engines are accurate",
              "Whether students should use books", "Whether psychologists use computers"],
             "Whether memorising information still matters"),
            ("How does stored knowledge help us, according to psychologists?",
             ["It lets us avoid reading", "It helps us connect and understand new material",
              "It makes us use search engines faster", "It replaces the need for feedback"],
             "It helps us connect and understand new material"),
            ("What is 'digital amnesia'?",
             ["Losing data from a computer", "Forgetting passwords",
              "Remembering less when information stays available online", "A disease caused by screens"],
             "Remembering less when information stays available online"),
            ("What is the writer's view of technology in learning?",
             ["It always harms learning", "It can help if used deliberately",
              "It should replace teachers", "It has no effect at all"], "It can help if used deliberately"),
            ("What danger does the writer identify?",
             ["Spending too much on devices", "Confusing finding an answer with understanding it",
              "Reading too many books", "Practising too often"], "Confusing finding an answer with understanding it"),
        ],
    ),
]

LISTENING = [
    (
        "A Talk on Remote Work (B2)",
        "Good afternoon. Today I would like to look at what has happened since remote work became common. "
        "At first, many managers feared that productivity would collapse. In practice, surveys suggest that it stayed "
        "about the same, although results vary by job. Employees value the time saved on commuting, which averages "
        "nearly an hour a day in large cities. On the other hand, new staff often say they learn more slowly when they "
        "rarely meet colleagues in person. That is why most companies now prefer a hybrid model, with two or three days "
        "in the office. My advice is to use office days for discussion and training, and keep quiet, focused tasks for home.",
        [
            ("What did managers fear at first?", ["Productivity would collapse", "Rents would rise", "Staff would ask for more pay", "Offices would close"], "Productivity would collapse"),
            ("What do employees value most, according to the speaker?", ["Better computers", "Time saved on commuting", "Longer holidays", "Free lunches"], "Time saved on commuting"),
            ("Which group has difficulty with remote work?", ["Senior managers", "New staff", "Part-time cleaners", "Delivery drivers"], "New staff"),
            ("What model do most companies now prefer?", ["Fully remote", "Fully in the office", "Hybrid", "Four-day week"], "Hybrid"),
            ("What should office days be used for?", ["Quiet individual tasks", "Discussion and training", "Answering emails only", "Long holidays"], "Discussion and training"),
        ],
    ),
    (
        "Interview About Food Waste (B2)",
        "Interviewer: Why is food waste such a serious issue? Expert: Roughly a third of the food produced in the world "
        "is never eaten. When it rots in landfill it produces methane, a powerful greenhouse gas. Interviewer: Where does "
        "most of the waste happen? Expert: In poorer countries it happens mainly during storage and transport, because "
        "refrigeration is limited. In richer countries, households are the main source. People buy more than they need "
        "and misunderstand date labels. Interviewer: What can individuals do? Expert: Plan meals, check the fridge before "
        "shopping, and remember that 'best before' refers to quality, not safety.",
        [
            ("How much of the world's food is never eaten?", ["About a tenth", "About a third", "About a half", "Almost all"], "About a third"),
            ("What gas does rotting food produce in landfill?", ["Oxygen", "Hydrogen", "Methane", "Nitrogen"], "Methane"),
            ("Why is food wasted in poorer countries?", ["People buy too much", "Refrigeration is limited", "Date labels are confusing", "Restaurants throw it away"], "Refrigeration is limited"),
            ("What is the main source of waste in richer countries?", ["Farms", "Households", "Ships", "Schools"], "Households"),
            ("What does 'best before' refer to?", ["Safety", "Price", "Quality", "Weight"], "Quality"),
        ],
    ),
    (
        "Lecture on Sleep and Memory (B2)",
        "Most students know they should sleep more, yet many stay up late before an exam. Research shows this is usually "
        "a mistake. During deep sleep, the brain moves new information into long-term memory. In one experiment, people who "
        "slept after studying a word list recalled about twenty percent more than those who stayed awake. A short nap can "
        "help too, provided it lasts less than thirty minutes, because longer naps can leave you feeling tired. So the "
        "best strategy is to spread revision over several days and protect your sleep on the final night.",
        [
            ("What do many students do before an exam?", ["Sleep early", "Stay up late", "Skip breakfast", "Go jogging"], "Stay up late"),
            ("What happens during deep sleep?", ["New information moves into long-term memory", "The brain stops working", "Vocabulary is forgotten", "Heart rate increases sharply"], "New information moves into long-term memory"),
            ("How much more did the sleep group recall?", ["About five percent", "About ten percent", "About twenty percent", "About fifty percent"], "About twenty percent"),
            ("How long should a nap last?", ["Under thirty minutes", "About one hour", "Two hours", "All afternoon"], "Under thirty minutes"),
            ("What is the best strategy according to the speaker?", ["Revise everything the night before", "Spread revision and protect sleep", "Avoid revising altogether", "Replace sleep with naps"], "Spread revision and protect sleep"),
        ],
    ),
]

WRITING = [
    ("Public Transport or Private Cars (B2)", "Some people believe that governments should spend more on public transport than on building new roads. To what extent do you agree or disagree? Give reasons and examples."),
    ("Technology in the Classroom (B2)", "Discuss the advantages and disadvantages of replacing printed textbooks with digital devices in schools, and give your own opinion."),
    ("Working Abroad (B2)", "More young people now choose to work in another country for several years. What are the main reasons for this trend, and is it a positive development?"),
]

SPEAKING = [
    ("A Difficult Decision (B2)", "Describe a difficult decision you have made. You should say:\n1. what the decision was\n2. what options you had\n3. who or what influenced you\nand explain whether you think you made the right choice."),
    ("Social Media and Society (B2)", "Discuss how social media has changed the way people get news. Cover:\n1. the benefits of fast information\n2. the risk of false information\n3. how people can check what they read."),
    ("A Skill for the Future (B2)", "Talk about a skill that you think will be important in ten years. You should say:\n1. what the skill is\n2. how people can learn it\nand explain why it will matter."),
]


class Command(BaseCommand):
    help = "Tạo nội dung học trình độ B2 (từ vựng và bài luyện 4 kỹ năng)."

    def handle(self, *args, **options):
        with transaction.atomic():
            category, _ = Category.objects.get_or_create(
                name="Tiếng Anh B2",
                defaults={"description": "Từ vựng và bài học cấp độ B2.", "level": "B2"},
            )
            for word, ipa, meaning, word_type, example, topic in VOCABULARY:
                Vocabulary.objects.update_or_create(
                    word=word,
                    level="B2",
                    user=None,
                    defaults={
                        "category": category,
                        "ipa": ipa,
                        "meaning": meaning,
                        "word_type": word_type,
                        "example": example,
                        "topic": topic,
                    },
                )

            for title, text, questions in READING:
                passage, _ = ReadingPassage.objects.update_or_create(
                    title=title, level="B2", defaults={"text_content": text},
                )
                self._sync_questions(passage.questions, ReadingQuestion, "passage", passage, questions)

            for title, transcript, questions in LISTENING:
                track, _ = ListeningTrack.objects.update_or_create(
                    title=title, level="B2", defaults={"transcript": transcript, "audio_file": ""},
                )
                self._sync_questions(track.questions, ListeningQuestion, "track", track, questions)

            for title, prompt in WRITING:
                WritingTask.objects.update_or_create(title=title, level="B2", defaults={"prompt_text": prompt})
            for title, prompt in SPEAKING:
                SpeakingPrompt.objects.update_or_create(title=title, level="B2", defaults={"prompt_text": prompt})

        self.stdout.write(self.style.SUCCESS(
            f"Da tao noi dung B2: {len(VOCABULARY)} tu, {len(READING)} bai doc, {len(LISTENING)} bai nghe, "
            f"{len(WRITING)} de viet, {len(SPEAKING)} de noi."
        ))

    @staticmethod
    def _sync_questions(manager, model, parent_field, parent, questions):
        manager.all().delete()
        model.objects.bulk_create([
            model(
                **{parent_field: parent},
                question_text=text,
                options=options,
                correct_answer=answer,
                level="B2",
            )
            for text, options, answer in questions
        ])
