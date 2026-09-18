import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from core.models import (
    Category, Vocabulary, Flashcard,
    ReadingPassage, ReadingQuestion,
    ListeningTrack, ListeningQuestion,
    WritingTask, SpeakingPrompt,
    VocabularyQuestion
)

# ---------------------------------------------------------------------------
# Morphology Rules Engine for Scale-up Vocabulary (3000 Words)
# ---------------------------------------------------------------------------

def add_suffix(word, suffix):
    if not suffix:
        return word
    vowels = 'aeiou'
    # 1. Final 'y' to 'i' rule (except if suffix starts with 'i')
    if word.endswith('y') and len(word) > 1 and word[-2] not in vowels and not suffix.startswith('i'):
        word = word[:-1] + 'i'
    # 2. Drop silent 'e' if suffix starts with a vowel
    elif word.endswith('e') and suffix[0] in vowels:
        word = word[:-1]
    # 3. Double consonant rule (CVC)
    elif len(word) >= 3 and suffix[0] in vowels:
        c1, v, c2 = word[-3], word[-2], word[-1]
        if (c1 not in vowels and c1 != 'y') and (v in vowels) and (c2 not in vowels and c2 not in 'wxy'):
            word = word + c2
    return word + suffix

def generate_ipa(base_ipa, suffix):
    ipa = base_ipa.strip('/')
    if not ipa.startswith('ˈ') and not ipa.startswith('ˌ'):
        ipa = 'ˈ' + ipa
    
    if suffix == 'er':
        ipa = ipa + 'ər'
    elif suffix == 'ing':
        ipa = ipa + 'ɪŋ'
    elif suffix in ('s', 's_noun'):
        if ipa[-1] in 'ptkfθ':
            ipa = ipa + 's'
        elif ipa[-1] in 'sʃzʒtʃdʒ':
            ipa = ipa + 'ɪz'
        else:
            ipa = ipa + 'z'
    elif suffix == 'ed':
        if ipa[-1] in 'td':
            ipa = ipa + 'ɪd'
        elif ipa[-1] in 'ptkfʃθs':
            ipa = ipa + 't'
        else:
            ipa = ipa + 'd'
    elif suffix == 'ly':
        ipa = ipa + 'li'
    elif suffix == 'ness':
        ipa = ipa + 'nəs'
    elif suffix == 'less':
        ipa = ipa + 'ləs'
    elif suffix == 'ful':
        ipa = ipa + 'fəl'
    elif suffix == 'y':
        ipa = ipa + 'i'
    elif suffix == 'able':
        ipa = ipa + 'əbl'
    return f"/{ipa}/"

# ---------------------------------------------------------------------------
# Seed Roots Dataset (630 roots total: 210 per level)
# ---------------------------------------------------------------------------

ROOTS_A1 = {
    'verb': [
        ("work", "làm việc", "wɜːrk"), ("play", "chơi", "pleɪ"), ("study", "học tập", "stʌdi"), ("learn", "học hỏi", "lɜːrn"),
        ("read", "đọc", "riːd"), ("write", "viết", "raɪt"), ("speak", "nói", "spiːk"), ("listen", "lắng nghe", "lɪsn"),
        ("run", "chạy", "rʌn"), ("walk", "đi bộ", "wɔːk"), ("jump", "nhảy", "dʒʌmp"), ("swim", "bơi", "swɪm"),
        ("eat", "ăn", "iːt"), ("drink", "uống", "drɪŋk"), ("sleep", "ngủ", "sliːp"), ("wake", "thức giấc", "weɪk"),
        ("open", "mở", "oʊpən"), ("close", "đóng", "kloʊz"), ("hear", "nghe thấy", "hɪər"), ("see", "nhìn thấy", "siː"),
        ("look", "nhìn", "lʊk"), ("watch", "xem", "wɑːtʃ"), ("want", "muốn", "wɑːnt"), ("like", "thích", "laɪk"),
        ("love", "yêu", "lʌv"), ("hate", "ghét", "heɪt"), ("help", "giúp đỡ", "hɛlp"), ("make", "chế tạo", "meɪk"),
        ("do", "làm", "duː"), ("go", "đi", "ɡoʊ"), ("come", "đến", "kʌm"), ("call", "gọi", "kɔːl"),
        ("send", "gửi", "sɛnd"), ("buy", "mua", "baɪ"), ("sell", "bán", "sɛl"), ("pay", "trả tiền", "peɪ"),
        ("meet", "gặp gỡ", "miːt"), ("live", "sống", "lɪv"), ("clean", "lau chùi", "kliːn"), ("wash", "rửa", "wɑːʃ"),
        ("cook", "nấu ăn", "kʊk"), ("sing", "hát", "sɪŋ"), ("dance", "nhảy múa", "dæns"), ("laugh", "cười", "læf"),
        ("cry", "khóc", "kraɪ"), ("smile", "mỉm cười", "smaɪl"), ("ride", "cưỡi", "raɪd"), ("drive", "lái xe", "draɪv"),
        ("fly", "bay", "flaɪ"), ("fall", "rơi", "fɔːl"), ("grow", "lớn lên", "ɡroʊ"), ("know", "biết", "noʊ"),
        ("think", "nghĩ", "θɪŋk"), ("understand", "hiểu", "ʌndərstænd"), ("remember", "nhớ", "rɪmɛmbər"), ("forget", "quên", "fərɡɛt"),
        ("show", "chỉ ra", "ʃoʊ"), ("tell", "kể", "tɛl"), ("say", "nói", "seɪ"), ("ask", "hỏi", "æsk"),
        ("answer", "trả lời", "ænsər"), ("start", "bắt đầu", "stɑːrt"), ("begin", "bắt đầu", "bɪɡɪn"), ("stop", "dừng", "stɑːp"),
        ("finish", "hoàn thành", "fɪnɪʃ"), ("end", "kết thúc", "ɛnd"), ("sit", "ngồi", "sɪt"), ("stand", "đứng", "stænd"),
        ("bring", "mang lại", "brɪŋ"), ("take", "lấy", "teɪk"), ("give", "cho", "ɡɪv"), ("keep", "giữ", "kiːp"),
        ("hold", "nắm giữ", "hoʊld"), ("carry", "mang theo", "kæri"), ("pull", "kéo", "pʊl"), ("push", "đẩy", "pʊʃ"),
        ("turn", "xoay", "tɜːrn"), ("change", "thay đổi", "tʃeɪndʒ"), ("move", "di chuyển", "muːv"), ("stay", "ở lại", "steɪ"),
        ("leave", "rời đi", "liːv"), ("lose", "mất", "luːz"), ("find", "tìm thấy", "faɪnd"), ("win", "chiến thắng", "wɪn"),
        ("try", "cố gắng", "traɪ"), ("use", "sử dụng", "juːz"), ("need", "cần", "niːd"), ("mean", "có nghĩa là", "miːn"),
        ("seem", "dường như", "siːm"), ("feel", "cảm thấy", "fiːl"), ("talk", "trò chuyện", "tɔːk"), ("hope", "hy vọng", "hoʊp"),
        ("wish", "ước", "wɪʃ"), ("break", "làm vỡ", "breɪk"), ("cut", "cắt", "kʌt"), ("build", "xây dựng", "bɪld"),
        ("paint", "sơn", "peɪnt"), ("cost", "trị giá", "kɔːst"), ("touch", "chạm", "tʌtʃ"), ("add", "thêm", "æd")
    ],
    'noun': [
        ("family", "gia đình", "fæməli"), ("friend", "bạn bè", "frɛnd"), ("school", "trường học", "skuːl"), ("teacher", "giáo viên", "tiːtʃər"),
        ("student", "học sinh", "stuːdnt"), ("class", "lớp học", "klæs"), ("book", "sách", "bʊk"), ("pen", "bút", "pɛn"),
        ("pencil", "bút chì", "pɛnsl"), ("paper", "giấy", "peɪpər"), ("desk", "bàn học", "dɛsk"), ("chair", "ghế", "tʃɛr"),
        ("door", "cửa", "dɔːr"), ("window", "cửa sổ", "wɪndoʊ"), ("room", "căn phòng", "ruːm"), ("house", "ngôi nhà", "haʊs"),
        ("home", "nhà", "hoʊm"), ("table", "bàn", "teɪbl"), ("bed", "giường", "bɛd"), ("clock", "đồng hồ", "klɑːk"),
        ("watch", "đồng hồ đeo tay", "wɑːtʃ"), ("phone", "điện thoại", "foʊn"), ("computer", "máy tính", "kəmˈpjuːtər"), ("water", "nước", "wɔːtər"),
        ("milk", "sữa", "mɪlk"), ("bread", "bánh mì", "brɛd"), ("apple", "quả táo", "æpl"), ("banana", "quả chuối", "bənænə"),
        ("orange", "quả cam", "ɔːrɪndʒ"), ("food", "thức ăn", "fuːd"), ("street", "con đường", "striːt"), ("road", "đường đi", "roʊd"),
        ("city", "thành phố", "sɪti"), ("town", "thị trấn", "taʊn"), ("country", "đất nước", "kʌntri"), ("world", "thế giới", "wɜːrld"),
        ("sun", "mặt trời", "sʌn"), ("moon", "mặt trăng", "muːn"), ("star", "ngôi sao", "stɑːr"), ("sky", "bầu trời", "skaɪ"),
        ("cloud", "đám mây", "klaʊd"), ("rain", "mưa", "reɪn"), ("wind", "gió", "wɪnd"), ("father", "bố", "fɑːðər"),
        ("mother", "mẹ", "mʌðər"), ("brother", "anh trai", "brʌðər"), ("sister", "chị gái", "sɪstər"), ("baby", "em bé", "beɪbi"),
        ("child", "trẻ em", "tʃaɪld"), ("boy", "cậu bé", "bɔɪ"), ("girl", "cô bé", "ɡɜːrl"), ("man", "đàn ông", "mæn"),
        ("woman", "phụ nữ", "wʊmən"), ("person", "người", "pɜːrsn"), ("people", "mọi người", "piːpl"), ("animal", "động vật", "ænɪml"),
        ("dog", "con chó", "dɔːɡ"), ("cat", "con mèo", "kæt"), ("bird", "con chim", "bɜːrd"), ("fish", "con cá", "fɪʃ"),
        ("tree", "cây", "triː"), ("flower", "hoa", "flaʊər"), ("grass", "cỏ", "ɡræs"), ("garden", "khu vườn", "ɡɑːrdn"),
        ("park", "công viên", "pɑːrk"), ("market", "chợ", "mɑːrkɪt"), ("shop", "cửa hàng", "ʃɑːp"), ("store", "kho chứa", "stɔːr"),
        ("bag", "túi xách", "bæɡ"), ("box", "hộp", "bɑːks")
    ],
    'adjective': [
        ("happy", "vui vẻ", "hæpi"), ("sad", "buồn bã", "sæd"), ("angry", "tức giận", "æŋɡri"), ("tired", "mệt mỏi", "taɪərd"),
        ("good", "tốt", "ɡʊd"), ("bad", "xấu", "bæd"), ("new", "mới", "nuː"), ("old", "cũ", "oʊld"),
        ("young", "trẻ", "jʌŋ"), ("hot", "nóng", "hɑːt"), ("cold", "lạnh", "koʊld"), ("warm", "ấm", "wɔːrm"),
        ("cool", "mát mẻ", "kuːl"), ("big", "to", "bɪɡ"), ("small", "nhỏ", "smɔːl"), ("tall", "cao", "tɔːl"),
        ("short", "ngắn", "ʃɔːrt"), ("long", "dài", "lɔːŋ"), ("clean", "sạch", "kliːn"), ("dirty", "bẩn", "dɜːrti"),
        ("easy", "dễ", "iːzi"), ("hard", "khó", "hɑːrd"), ("slow", "chậm", "sloʊ"), ("fast", "nhanh", "fæst"),
        ("soft", "mềm", "sɔːft"), ("loud", "to", "laʊd"), ("quiet", "yên lặng", "kwaɪət"), ("busy", "bận rộn", "bɪzi"),
        ("free", "tự do", "friː"), ("rich", "giàu", "rɪtʃ"), ("poor", "nghèo", "pʊr"), ("healthy", "khỏe mạnh", "hɛlθi"),
        ("sick", "ốm", "sɪk"), ("strong", "mạnh mẽ", "strɔːŋ"), ("weak", "yếu", "wiːk"), ("heavy", "nặng", "hɛvi"),
        ("light", "nhẹ", "laɪt"), ("full", "đầy", "fʊl"), ("empty", "trống rỗng", "ɛmpti"), ("dry", "khô", "draɪ")
    ]
}

ROOTS_A2 = {
    'verb': [
        ("travel", "du lịch", "trævl"), ("explore", "khám phá", "ɪksplɔːr"), ("visit", "thăm", "vɪzɪt"), ("arrive", "đến nơi", "əraɪv"),
        ("depart", "khởi hành", "dɪpɑːrt"), ("return", "trở về", "rɪtɜːrn"), ("book", "đặt trước", "bʊk"), ("reserve", "dành riêng", "rɪzɜːrv"),
        ("cancel", "hủy bỏ", "kænsl"), ("check", "kiểm tra", "tʃɛk"), ("confirm", "xác nhận", "kənfɜːrm"), ("pack", "đóng gói", "pæk"),
        ("unpack", "mở gói", "ʌnpæk"), ("collect", "thu thập", "kəlɛkt"), ("gather", "tập hợp", "ɡæðər"), ("choose", "chọn", "tʃuːz"),
        ("select", "lựa chọn", "sɪlɛkt"), ("decide", "quyết định", "dɪsaɪd"), ("agree", "đồng ý", "əɡriː"), ("disagree", "không đồng ý", "dɪsəɡriː"),
        ("explain", "giải thích", "ɪkspleɪn"), ("describe", "mô tả", "dɪskraɪb"), ("discuss", "thảo luận", "dɪskʌs"), ("argue", "tranh luận", "ɑːrɡjuː"),
        ("promise", "hứa", "prɑːmɪs"), ("refuse", "từ chối", "rɪfjuːz"), ("accept", "chấp nhận", "æksɛpt"), ("receive", "nhận", "rɪsiːv"),
        ("deliver", "giao hàng", "dɪlɪvər"), ("share", "chia sẻ", "ʃɛr"), ("borrow", "mượn", "bɑːroʊ"), ("lend", "cho mượn", "lɛnd"),
        ("spend", "tiêu dùng", "spɛnd"), ("waste", "lãng phí", "weɪst"), ("save", "tiết kiệm", "seɪv"), ("earn", "kiếm được", "ɜːrn"),
        ("invest", "đầu tư", "ɪnvɛst"), ("value", "định giá", "væljuː"), ("measure", "đo lường", "mɛʒər"), ("weigh", "cân nặng", "weɪ"),
        ("compare", "so sánh", "kəmpɛr"), ("contrast", "tương phản", "kəntræst"), ("prefer", "thích hơn", "prɪfɜːr"), ("enjoy", "thưởng thức", "ɪndʒɔɪ"),
        ("dislike", "không thích", "dɪslaɪk"), ("mind", "chú ý", "maɪnd"), ("avoid", "tránh", "əvɔɪd"), ("suggest", "gợi ý", "səɡdʒɛst"),
        ("recommend", "khuyên dùng", "rɛkəmɛnd"), ("advise", "khuyên bảo", "ədvaɪz"), ("warn", "cảnh báo", "wɔːrn"), ("inform", "thông báo", "ɪnfɔːrm"),
        ("remind", "nhắc nhở", "rɪmaɪnd"), ("train", "đào tạo", "treɪn"), ("coach", "hướng dẫn", "koʊtʃ"), ("guide", "chỉ dẫn", "ɡaɪd"),
        ("lead", "dẫn dắt", "liːd"), ("follow", "theo dõi", "fɑːloʊ"), ("support", "hỗ trợ", "səpɔːrt"), ("encourage", "khuyến khích", "ɪnkɜːrɪdʒ"),
        ("protect", "bảo vệ", "prətɛkt"), ("defend", "phòng thủ", "dɪfɛnd"), ("attack", "tấn công", "ətæk"), ("fight", "chiến đấu", "faɪt"),
        ("defeat", "đánh bại", "dɪfiːt"), ("enter", "đi vào", "ɛntər"), ("exit", "đi ra", "ɛɡzɪt"), ("remain", "còn lại", "rɪmeɪn"),
        ("continue", "tiếp tục", "kəntɪnjuː"), ("repeat", "lặp lại", "rɪpiːt"), ("practice", "luyện tập", "præktɪs"), ("improve", "cải thiện", "ɪmpruːv"),
        ("develop", "phát triển", "dɪvɛləp"), ("create", "sáng tạo", "kriːeɪt"), ("design", "thiết kế", "dɪzaɪn"), ("solve", "giải quyết", "sɑːlv"),
        ("plan", "lên kế hoạch", "plæn"), ("organize", "tổ chức", "ɔːrɡənaɪz"), ("manage", "quản lý", "mænɪdʒ"), ("control", "kiểm soát", "kəntroʊl"),
        ("direct", "hướng dẫn", "dərɛkt"), ("report", "báo cáo", "rɪpɔːrt"), ("present", "trình bày", "prɪzɛnt"), ("introduce", "giới thiệu", "ɪntrəduːs"),
        ("prepare", "chuẩn bị", "prɪpɛr"), ("provide", "cung cấp", "prəvaɪd"), ("offer", "đề nghị", "ɔːfər"), ("invite", "mời", "ɪnvaɪt"),
        ("attend", "tham dự", "ətɛnd"), ("join", "gia nhập", "dʒɔɪn"), ("participate", "tham gia", "pɑːrtɪsɪpeɪt"), ("connect", "kết nối", "kənɛkt"),
        ("link", "liên kết", "lɪŋk"), ("attach", "đính kèm", "ətætʃ"), ("separate", "phân chia", "sɛpəreɪt"), ("publish", "xuất bản", "pʌblɪʃ"),
        ("print", "in ấn", "prɪnt"), ("record", "ghi âm", "rɪkɔːrd"), ("discover", "phát hiện", "dɪskʌvər"), ("invent", "sáng chế", "ɪnvɛnt"),
        ("repair", "sửa chữa", "rɪpɛr")
    ],
    'noun': [
        ("airport", "sân bay", "eəpɔːrt"), ("ticket", "vé", "tɪkɪt"), ("flight", "chuyến bay", "flaɪt"), ("hotel", "khách sạn", "hoʊtɛl"),
        ("luggage", "hành lý", "lʌɡɪdʒ"), ("tourist", "khách du lịch", "tʊərɪst"), ("museum", "bảo tàng", "mjuˈziːəm"), ("beach", "bãi biển", "biːtʃ"),
        ("mountain", "núi", "maʊntən"), ("forest", "rừng", "fɑːrɪst"), ("river", "sông", "rɪvər"), ("lake", "hồ", "leɪk"),
        ("weather", "thời tiết", "wɛðər"), ("climate", "khí hậu", "klaɪmət"), ("season", "mùa", "siːzn"), ("spring", "mùa xuân", "sprɪŋ"),
        ("summer", "mùa hè", "sʌmər"), ("autumn", "mùa thu", "ɔːtəm"), ("winter", "mùa đông", "wɪntər"), ("doctor", "bác sĩ", "dɑːktər"),
        ("nurse", "y tá", "nɜːrs"), ("hospital", "bệnh viện", "hɑːspɪtl"), ("medicine", "thuốc", "mɛdsn"), ("exercise", "bài tập", "ɛksərsaɪz"),
        ("sport", "thể thao", "spɔːrt"), ("game", "trò chơi", "ɡeɪm"), ("team", "đội", "tiːm"), ("match", "trận đấu", "mætʃ"),
        ("winner", "người chiến thắng", "wɪnər"), ("hobby", "sở thích", "hɑːbi"), ("music", "âm nhạc", "mjuːzɪk"), ("song", "bài hát", "sɔːŋ"),
        ("movie", "phim", "muːvi"), ("film", "phim điện ảnh", "fɪlm"), ("theater", "nhà hát", "θiːətər"), ("actor", "diễn viên nam", "æktər"),
        ("artist", "nghệ sĩ", "ɑːrtɪst"), ("painting", "bức tranh", "peɪntɪŋ"), ("drawing", "bức vẽ", "drɔːɪŋ"), ("photo", "bức ảnh", "foʊtoʊ"),
        ("camera", "máy ảnh", "kæmrə"), ("internet", "mạng", "ɪntərnɛt"), ("email", "thư điện tử", "iːmeɪl"), ("message", "tin nhắn", "mɛsɪdʒ"),
        ("news", "tin tức", "nuːz"), ("newspaper", "tờ báo", "nuːzpeɪpər"), ("magazine", "tạp chí", "mæɡəziːn"), ("article", "bài báo", "prints"),
        ("reporter", "phóng viên", "rɪpɔːrtər"), ("writer", "nhà văn", "raɪtər"), ("poet", "nhà thơ", "poʊət"), ("story", "câu chuyện", "stɔːri"),
        ("novel", "tiểu thuyết", "nɑːvl"), ("poem", "bài thơ", "poʊəm"), ("language", "ngôn ngữ", "læŋɡwɪdʒ"), ("word", "từ", "wɜːrd"),
        ("sentence", "câu", "sɛntəns"), ("grammar", "ngữ pháp", "ɡræmər"), ("conversation", "cuộc trò chuyện", "kɑːnvərseɪʃn"), ("dialogue", "đối thoại", "daɪəlɔːɡ"),
        ("group", "nhóm", "ɡruːp"), ("meeting", "cuộc họp", "miːtɪŋ"), ("party", "bữa tiệc", "pɑːrti"), ("event", "sự kiện", "ɪvɛnt"),
        ("festival", "lễ hội", "fɛstɪvl"), ("celebration", "sự kỷ niệm", "sɛlɪbreɪʃn"), ("gift", "quà tặng", "ɡɪft"), ("present", "món quà", "prɛznt"),
        ("card", "thẻ", "kɑːrd"), ("letter", "thư", "lɛtər")
    ],
    'adjective': [
        ("famous", "nổi tiếng", "feɪməs"), ("popular", "phổ biến", "pɑːpjələr"), ("local", "địa phương", "loʊkl"), ("national", "quốc gia", "næʃnəl"),
        ("international", "quốc tế", "ɪntərnæʃnəl"), ("traditional", "truyền thống", "trədɪʃnəl"), ("cultural", "văn hóa", "kʌltʃərəl"), ("historical", "lịch sử", "hɪstɔːrɪkl"),
        ("natural", "tự nhiên", "nætʃrəl"), ("wild", "hoang dã", "waɪld"), ("safe", "an toàn", "seɪf"), ("dangerous", "nguy hiểm", "deɪndʒərəs"),
        ("quiet", "yên tĩnh", "kwaɪət"), ("noisy", "ồn ào", "nɔɪzi"), ("crowded", "đông đúc", "kraʊdɪd"), ("comfortable", "dễ chịu", "kʌmftəbl"),
        ("expensive", "đắt", "ɪkspɛnsɪv"), ("cheap", "rẻ", "tʃiːp"), ("useful", "hữu ích", "juːsfl"), ("useless", "vô ích", "juːsləs"),
        ("careful", "cẩn thận", "kɛrfl"), ("careless", "cẩu thả", "kɛrləs"), ("helpful", "giúp ích", "hɛlpfl"), ("helpless", "bất lực", "hɛlpləs"),
        ("active", "năng động", "æktɪv"), ("lazy", "lười biếng", "leɪzi"), ("polite", "lịch sự", "pəlaɪt"), ("rude", "thô lỗ", "ruːd"),
        ("friendly", "thân thiện", "frɛndli"), ("unfriendly", "không thân thiện", "ʌnfrɛndli"), ("kind", "tốt bụng", "kaɪnd"), ("unkind", "không tốt bụng", "ʌnkaɪnd"),
        ("honest", "trung thực", "ɑːnɪst"), ("dishonest", "không trung thực", "dɪsɑːnɪst"), ("brave", "dũng cảm", "breɪv"), ("clever", "khôn khéo", "klɛvər"),
        ("stupid", "ngốc nghếch", "stuːpɪd"), ("creative", "sáng tạo", "kriːeɪtɪv"), ("perfect", "hoàn hảo", "pɜːrfɪkt"), ("possible", "có thể", "pɑːsəbl")
    ]
}

ROOTS_B1 = {
    'verb': [
        ("achieve", "đạt được", "ətʃiːv"), ("acquire", "thu được", "əkwaɪər"), ("advertise", "quảng cáo", "ædvərtaɪz"), ("analyze", "phân tích", "ænəlaɪz"),
        ("conclude", "kết luận", "kənkluːd"), ("implement", "thực hiện", "ɪmplɪmɛnt"), ("optimize", "tối ưu hóa", "ɑːptɪmaɪz"), ("integrate", "tích hợp", "ɪntɪɡreɪt"),
        ("generate", "tạo ra", "dʒɛnəreɪt"), ("coordinate", "phối hợp", "koʊɔːrdɪneɪt"), ("evaluate", "đánh giá", "ɪvæljueɪt"), ("assess", "đánh giá", "əsɛs"),
        ("monitor", "giám sát", "mɑːnɪtər"), ("supervise", "giám sát", "suːpərvaɪz"), ("inspect", "thanh tra", "ɪnspɛkt"), ("review", "đánh giá lại", "rɪvjuː"),
        ("verify", "xác minh", "vɛrɪfaɪ"), ("validate", "phê chuẩn", "vælɪdeɪt"), ("update", "cập nhật", "ʌpdeɪt"), ("upgrade", "nâng cấp", "ʌpɡreɪd"),
        ("backup", "sao lưu", "bækʌp"), ("restore", "khôi phục", "rɪstɔːr"), ("recover", "phục hồi", "rɪkʌvər"), ("install", "cài đặt", "ɪnstɔːl"),
        ("uninstall", "gỡ cài đặt", "ʌnɪnstɔːl"), ("execute", "thi hành", "ɛksɪkjuːt"), ("compile", "biên dịch", "kəmpaɪl"), ("debug", "gỡ lỗi", "diːbʌɡ"),
        ("deploy", "triển khai", "dɪplɔɪ"), ("configure", "cấu hình", "kənfɪɡjər"), ("authenticate", "xác thực", "ɔːθɛntɪkeɪt"), ("authorize", "ủy quyền", "ɔːθəraɪz"),
        ("encrypt", "mã hóa", "ɪnkrɪpt"), ("decrypt", "giải mã", "diːkrɪpt"), ("compress", "nén", "kəmprɛs"), ("decompress", "giải nén", "diːkəmprɛs"),
        ("transfer", "chuyển nhượng", "trænsfɜːr"), ("transmit", "truyền tải", "trænzmɪt"), ("broadcast", "phát sóng", "brɔːdkæst"), ("subscribe", "đăng ký", "səbskraɪb"),
        ("contribute", "đóng góp", "kəntrɪbjuːt"), ("collaborate", "hợp tác", "kəlæbəreɪt"), ("negotiate", "thương lượng", "nɪɡoʊʃieɪt"), ("compromise", "thỏa hiệp", "kɑːmprəmaɪz"),
        ("resolve", "giải quyết", "rɪzɑːlv"), ("settle", "dàn xếp", "sɛtl"), ("facilitate", "tạo điều kiện", "fəsɪlɪteɪt"), ("promote", "quảng bá", "prəmoʊt"),
        ("boost", "thúc đẩy", "buːst"), ("enhance", "nâng cao", "ɛnhæns"), ("motivate", "thúc đẩy", "moʊtɪveɪt"), ("inspire", "truyền cảm hứng", "ɪnspaɪər"),
        ("influence", "ảnh hưởng", "ɪnfluəns"), ("persuade", "thuyết phục", "pərsweɪd"), ("convince", "thuyết phục", "kənvɪns"), ("advocate", "biện hộ", "ædvəkeɪt"),
        ("oppose", "phản đối", "əpoʊz"), ("resist", "kháng cự", "rɪzɪst"), ("prevent", "ngăn chặn", "prɪvɛnt"), ("prohibit", "nghiêm cấm", "proʊhɪbɪt"),
        ("forbid", "ngăn cấm", "fərbɪd"), ("allow", "cho phép", "əlaʊ"), ("permit", "cho phép", "pərmɪt"), ("enable", "cho phép", "ɛneɪbl"),
        ("require", "yêu cầu", "rɪkwaɪər"), ("demand", "yêu cầu", "dɪmænd"), ("request", "yêu cầu", "rɪkwɛst"), ("submit", "nộp", "səbmɪt"),
        ("register", "đăng ký", "rɛdʒɪstər"), ("apply", "áp dụng", "əplaɪ"), ("enroll", "ghi danh", "ɪnroʊl"), ("engage", "thu hút", "ɛnɡeɪdʒ"),
        ("involve", "liên quan", "ɪnvɑːlv"), ("contain", "chứa đựng", "kənteɪn"), ("consist", "bao gồm", "kənsɪst"), ("exclude", "loại trừ", "ɪkskluːd"),
        ("include", "bao gồm", "ɪnkluːd"), ("eliminate", "loại bỏ", "ɪlɪmɪneɪt"), ("remove", "xóa bỏ", "rɪmuːv"), ("delete", "xóa", "dɪliːt"),
        ("insert", "chèn", "ɪnsɜːrt"), ("replace", "thay thế", "rɪpleɪs"), ("modify", "sửa đổi", "mɑːdɪfaɪ"), ("alter", "thay đổi", "ɔːltər"),
        ("adjust", "điều chỉnh", "ədʒʌst"), ("adapt", "thích nghi", "ədæpt"), ("transform", "biến đổi", "trænsfɔːrm"), ("convert", "chuyển đổi", "kənvɜːrt"),
        ("translate", "dịch", "trænsleɪt"), ("interpret", "giải thích", "ɪntɜːrprət"), ("clarify", "làm rõ", "klærəfaɪ"), ("illustrate", "minh họa", "ɪləstreɪt"),
        ("demonstrate", "chứng minh", "dɛmənstreɪt"), ("prove", "chứng minh", "pruːv"), ("assume", "thừa nhận", "əsuːm"), ("presume", "giả định", "prɪzuːm"),
        ("estimate", "ước tính", "ɛstɪmeɪt"), ("predict", "dự đoán", "prɪdɪkt"), ("anticipate", "mong đợi", "æntɪsɪpeɪt"), ("guarantee", "bảo hành", "ɡærənti")
    ],
    'noun': [
        ("ability", "khả năng", "əbɪlɪti"), ("advantage", "lợi thế", "ədvæntɪdʒ"), ("analysis", "sự phân tích", "ənæləsɪs"), ("standard", "tiêu chuẩn", "stændərd"),
        ("target", "mục tiêu", "tɑːrɡɪt"), ("quality", "chất lượng", "kwɑːlɪti"), ("focus", "sự tập trung", "foʊkəs"), ("process", "quá trình", "prɑːsɛs"),
        ("project", "dự án", "prɑːdʒɛkt"), ("feedback", "phản hồi", "fiːdbæk"), ("concept", "khái niệm", "kɑːnsɛpt"), ("context", "ngữ cảnh", "kːntɛkst"),
        ("structure", "cấu trúc", "strʌktʃər"), ("function", "chức năng", "fʌŋkʃn"), ("source", "nguồn", "sɔːrs"), ("resource", "tài nguyên", "riːsɔːrs"),
        ("database", "cơ sở dữ liệu", "deɪtəbeɪs"), ("network", "mạng lưới", "nɛtwɜːrk"), ("client", "máy khách", "klaɪənt"), ("server", "máy chủ", "sɜːrvər"),
        ("software", "phần mềm", "sɔːftwɛr"), ("hardware", "phần cứng", "hɑːrdwɛr"), ("system", "hệ thống", "sɪstəm"), ("program", "chương trình", "proʊɡræm"),
        ("application", "ứng dụng", "æplɪkeɪʃn"), ("website", "trang web", "wɛbsaɪt"), ("browser", "trình duyệt", "braʊzər"), ("search", "sự tìm kiếm", "sɜːrtʃ"),
        ("option", "lựa chọn", "ɑːpʃn"), ("category", "danh mục", "kætəɡɔːri"), ("profile", "hồ sơ", "proʊfaɪl"), ("schedule", "lịch trình", "skɛdʒuːl"),
        ("calendar", "lịch", "kælɪndər"), ("deadline", "hạn chót", "dɛdlaɪn"), ("result", "kết quả", "rɪzʌlt"), ("score", "điểm số", "skɔːr"),
        ("percent", "phần trăm", "pərsɛnt"), ("average", "trung bình", "ævərɪdʒ"), ("total", "tổng số", "toʊtl"), ("summary", "tóm tắt", "sʌməri"),
        ("report", "báo cáo", "rɪpɔːrt"), ("document", "tài liệu", "dɑːkjumənt"), ("file", "tệp tin", "faɪl"), ("folder", "thư mục", "foʊldər"),
        ("record", "hồ sơ", "rɛkərd"), ("upload", "sự tải lên", "ʌploʊd"), ("download", "sự tải xuống", "daʊnloʊd"), ("password", "mật khẩu", "pæswɜːrd"),
        ("account", "tài khoản", "əkaʊnt"), ("notification", "thông báo", "noʊtɪfɪkeɪʃn"), ("alert", "cảnh báo", "əlɜːrt"), ("warning", "sự cảnh báo", "wɔːrnɪŋ"),
        ("status", "trạng thái", "steɪtəs"), ("progress", "tiến trình", "prɑːɡrɛs"), ("interval", "khoảng thời gian", "ɪntərvl"), ("factor", "yếu tố", "fæktər"),
        ("ease", "sự dễ dàng", "iːz"), ("logic", "lô-gíc", "lɑːdʒɪk"), ("design", "thiết kế", "dɪzaɪn"), ("code", "mã", "koʊd"),
        ("framework", "khung công việc", "freɪmwɜːrk"), ("backend", "phía máy chủ", "bækɛnd"), ("frontend", "phía người dùng", "frʌntɛnd"), ("conclusion", "kết luận", "kənkluːʒn"),
        ("evidence", "bằng chứng", "ɛvɪdəns"), ("innovation", "sự đổi mới", "ɪnəveɪʃn"), ("strategy", "chiến lược", "strætədʒi"), ("efficiency", "hiệu suất", "ɪfɪʃnsi"),
        ("collaboration", "sự hợp tác", "kəlæbəreɪʃn"), ("productivity", "năng suất", "proʊdʌktɪvəti")
    ],
    'adjective': [
        ("dynamic", "năng động", "daɪnæmɪk"), ("complex", "phức tạp", "kɑːmplɛks"), ("constant", "hằng số", "kɑːnstənt"), ("efficient", "hiệu quả", "ɪfɪʃnt"),
        ("global", "toàn cầu", "ɡloʊbl"), ("secure", "an toàn", "sɪkjʊr"), ("significant", "quan trọng", "sɪɡnɪfɪkənt"), ("logical", "hợp lý", "lɑːdʒɪkl"),
        ("innovative", "sáng tạo", "ɪnəveɪtɪv"), ("strategic", "chiến lược", "strətiːdʒɪk"), ("productive", "năng suất", "prədʌktɪv"), ("flexible", "linh hoạt", "flɛksəbl"),
        ("variable", "biến đổi", "vɛriəbl"), ("stable", "ổn định", "steɪbl"), ("unstable", "không ổn định", "ʌnsteɪbl"), ("reliable", "đáng tin cậy", "rɪlaɪəbl"),
        ("unreliable", "không đáng tin cậy", "ʌnrɪlaɪəbl"), ("accurate", "chính xác", "ækjərət"), ("inaccurate", "không chính xác", "ɪnækjərət"), ("precise", "tỉ mỉ", "prɪsaɪs"),
        ("imprecise", "không tỉ mỉ", "ɪmprɪsaɪs"), ("relevant", "liên quan", "rɛləvənt"), ("irrelevant", "không liên quan", "ɪrɛləvənt"), ("essential", "thiết yếu", "ɪsɛnʃl"),
        ("nonessential", "không thiết yếu", "nɑːnɪsɛnʃl"), ("critical", "nguy ngập", "krɪtɪkl"), ("crucial", "chủ yếu", "kruːʃl"), ("primary", "chính", "praɪmeri"),
        ("secondary", "phụ", 'sɛkənderi'), ("internal", "nội bộ", "ɪntɜːrnl"), ("external", "bên ngoài", "ɪkstɜːrnl"), ("major", "chủ yếu", "meɪdʒər"),
        ("minor", "thứ yếu", "maɪnər"), ("temporary", "tạm thời", "tɛmpəreri"), ("permanent", "lâu dài", "pɜːrmənənt"), ("adequate", "đầy đủ", "ædɪkwət"),
        ("inadequate", "không đầy đủ", "ɪnædɪkwət"), ("mutual", "lẫn nhau", "mjuːtʃuəl"), ("neutral", "trung lập", "nuːtrəl"), ("potential", "tiềm năng", "pətɛnʃl")
    ]
}

# ---------------------------------------------------------------------------
# Suffix Rules Maps & Templates for DynVocab
# ---------------------------------------------------------------------------

SUFFIX_MAPS = {
    'verb': ['er', 'ing', 's', 'ed', 'able'],
    'noun': ['s_noun', 'less'],
    'adjective': ['ly', 'ness']
}

IPA_CORRECTIONS = {
    'ed': {'t': 't', 'd': 'd', 'id': 'ɪd'},
}

def generate_sentence(word, word_type, suffix, level):
    word_cap = word.capitalize()
    templates = {
        'A1': {
            'verb': {
                '': f"I always {word} in the morning.",
                'er': f"He is a good {word}.",
                'ing': f"They enjoy {word} together.",
                's': f"She {word} every day.",
                'ed': f"Yesterday, they {word} at school.",
                'able': f"This is a {word} activity."
            },
            'noun': {
                '': f"This is a nice {word}.",
                's_noun': f"We have many {word} in our room.",
                'less': f"He felt completely {word}."
            },
            'adjective': {
                '': f"She is a very {word} student.",
                'ly': f"He smiled {word} at his friend.",
                'ness': f"They found great {word} in the garden."
            }
        },
        'A2': {
            'verb': {
                '': f"You should {word} to improve your skills.",
                'er': f"She worked as a professional {word}.",
                'ing': f"{word_cap} helps people learn faster.",
                's': f"He {word} his work on time.",
                'ed': f"We {word} the project last week.",
                'able': f"The system is very {word}."
            },
            'noun': {
                '': f"We visited the local {word} yesterday.",
                's_noun': f"They bought several {word} for the trip.",
                'less': f"The traveler was left {word}."
            },
            'adjective': {
                '': f"This is an important and {word} lesson.",
                'ly': f"The reporter explained the news {word}.",
                'ness': f"The doctor measured his physical {word}."
            }
        },
        'B1': {
            'verb': {
                '': f"The team needs to {word} the strategic plan.",
                'er': f"The senior {word} managed the process.",
                'ing': f"{word_cap} requires constant communication and focus.",
                's': f"The manager {word} the new application.",
                'ed': f"They {word} the database backup successfully.",
                'able': f"We must ensure the process is {word}."
            },
            'noun': {
                '': f"We need to analyze the {word} of the project.",
                's_noun': f"The company implemented new {word} for security.",
                'less': f"The system is designed to be {word}."
            },
            'adjective': {
                '': f"The software provides a {word} interface.",
                'ly': f"The engineer optimized the code {word}.",
                'ness': f"The analysis showed the level of {word}."
            }
        }
    }
    
    level_dict = templates.get(level, templates['A1'])
    type_dict = level_dict.get(word_type, level_dict['verb'])
    return type_dict.get(suffix, f"We use {word} in this context.")

# ---------------------------------------------------------------------------
# Skill content with 5-10 detailed questions/exercises each
# ---------------------------------------------------------------------------

SKILLS_DATA = {
    "reading": {
        "A1": [
            ("My Family", "I love my family. I have a father, a mother, and one brother. We live in a small house. My father is a teacher and my mother is a doctor. We eat dinner together every evening.", [
                ("Who is a doctor?", ["Father", "Mother", "Brother", "Sister"], "Mother"),
                ("How many brothers does the author have?", ["One", "Two", "Three", "None"], "One"),
                ("Where does the family live?", ["In a big city", "In a small house", "In an apartment", "On a farm"], "In a small house"),
                ("What is the father's job?", ["Doctor", "Teacher", "Driver", "Artist"], "Teacher"),
                ("When does the family eat dinner together?", ["In the morning", "At noon", "Every evening", "On weekends"], "Every evening")
            ]),
            ("At School", "My school is big and clean. I have many friends here. My teacher is very nice. We learn English, math, and science. I like English the most because it is fun.", [
                ("Which subject does the author like most?", ["Math", "Science", "English", "History"], "English"),
                ("How is the school described?", ["Small and old", "Big and clean", "Dark and noisy", "New but dirty"], "Big and clean"),
                ("Who is very nice?", ["The doctor", "The teacher", "The friend", "The brother"], "The teacher"),
                ("What subjects does the author learn?", ["English, math, and science", "History, art, and music", "Geography, biology, and chemistry", "None of the above"], "English, math, and science"),
                ("Why does the author like English?", ["Because it is easy", "Because it is fun", "Because the teacher is strict", "Because it starts early"], "Because it is fun")
            ]),
            ("My Day", "I wake up at 6 AM. I eat bread and drink milk for breakfast. Then, I go to school by bus. I study from 8 AM to 4 PM. In the evening, I play football with my friends.", [
                ("What time does the author wake up?", ["5 AM", "6 AM", "7 AM", "8 AM"], "6 AM"),
                ("What does the author eat for breakfast?", ["Rice", "Bread", "Eggs", "Noodles"], "Bread"),
                ("How does the author go to school?", ["By bus", "By car", "On foot", "By bicycle"], "By bus"),
                ("What does the author do in the evening?", ["Read books", "Play football", "Do homework", "Watch TV"], "Play football"),
                ("When does the author study?", ["From 8 AM to 4 PM", "From 9 AM to 5 PM", "From 7 AM to 3 PM", "All day long"], "From 8 AM to 4 PM")
            ]),
            ("My Hobby", "My hobby is reading books. I have a small bookshelf in my room. I read stories every night before sleep. It helps me learn new words and sleep better.", [
                ("What is the author's hobby?", ["Reading books", "Playing football", "Cooking", "Gardening"], "Reading books"),
                ("Where does the author keep books?", ["On a desk", "On a bookshelf", "In a box", "Under the bed"], "On a bookshelf"),
                ("When does the author read stories?", ["Every morning", "Every night", "On weekends", "In the afternoon"], "Every night"),
                ("How does reading help the author?", ["Learn new words and sleep better", "Pass exams", "Make friends", "Earn money"], "Learn new words and sleep better"),
                ("Where is the bookshelf located?", ["In the author's room", "In the living room", "In the kitchen", "At school"], "In the author's room")
            ]),
            ("Our Small Town", "Our town is small but beautiful. There is a green park, a school, and a local market. People are very friendly. On Sundays, I ride my bicycle around the town.", [
                ("What does the town have?", ["A park, a school, and a market", "A cinema, a supermarket, and a library", "A big factory and a hospital", "None of the above"], "A park, a school, and a market"),
                ("How are the people in the town described?", ["Very quiet", "Very busy", "Very friendly", "Very lazy"], "Very friendly"),
                ("What does the author do on Sundays?", ["Ride a bicycle", "Go to the market", "Visit the school", "Play football"], "Ride a bicycle"),
                ("How is the town described?", ["Small but beautiful", "Big and noisy", "Old and dirty", "Modern and crowded"], "Small but beautiful"),
                ("Where does the author ride the bicycle?", ["Around the town", "In the school yard", "On the highway", "In the park only"], "Around the town")
            ]),
            ("My Favorite Food", "I love healthy food. My favorite fruits are apples and bananas. I drink milk every morning. I do not like fast food because it is bad for my health.", [
                ("What fruits does the author like?", ["Oranges and grapes", "Apples and bananas", "Watermelons and mangos", "Pineapples"], "Apples and bananas"),
                ("What does the author drink every morning?", ["Water", "Coffee", "Tea", "Milk"], "Milk"),
                ("Why doesn't the author like fast food?", ["It is bad for health", "It is expensive", "It is bad for health", "It is not tasty", "It is hard to buy"], "It is bad for health"),
                ("How is the food the author loves described?", ["Healthy", "Sweet", "Spicy", "Fast"], "Healthy"),
                ("When does the author drink milk?", ["Every morning", "At night", "Every afternoon", "Never"], "Every morning")
            ]),
            ("My Pet Dog", "I have a small dog named Max. He has brown hair and a short tail. He is very happy and runs fast. We play together in the garden every afternoon.", [
                ("What is the dog's name?", ["Max", "Sam", "Buddy", "Rocky"], "Max"),
                ("What color is Max's hair?", ["White", "Black", "Brown", "Grey"], "Brown"),
                ("Where do they play together?", ["In the park", "In the room", "In the garden", "On the street"], "In the garden"),
                ("How is Max's tail described?", ["Long", "Short", "Curly", "No tail"], "Short"),
                ("When do they play together?", ["Every afternoon", "Every morning", "Every afternoon", "Every evening", "On Sundays"], "Every afternoon")
            ])
        ],
        "A2": [
            ("A Trip to Paris", "Last summer, I traveled to Paris. It was an amazing holiday. We visited the Eiffel Tower and explored famous museums. The food was delicious, especially the croissants. It was crowded but very exciting.", [
                ("Where did the author travel last summer?", ["London", "Paris", "Rome", "Tokyo"], "Paris"),
                ("How was the holiday described?", ["Boring", "Amazing", "Tiring", "Short"], "Amazing"),
                ("What famous tower did they visit?", ["Eiffel Tower", "Big Ben", "Tokyo Tower", "Leaning Tower"], "Eiffel Tower"),
                ("What food was mentioned as especially delicious?", ["Pizza", "Croissants", "Burgers", "Sushi"], "Croissants"),
                ("How was the atmosphere described?", ["Crowded but exciting", "Quiet and peaceful", "Crowded but exciting", "Boring and slow", "Cold and windy"], "Crowded but exciting")
            ]),
            ("A Healthy Lifestyle", "Staying healthy is important. You should drink plenty of water and eat fresh vegetables. Doing exercise for 30 minutes daily is also good. Try to sleep 8 hours every night to stay active.", [
                ("What should you drink plenty of?", ["Soda", "Coffee", "Water", "Milk tea"], "Water"),
                ("What kind of vegetables should you eat?", ["Canned vegetables", "Fresh vegetables", "Fried vegetables", "No vegetables"], "Fresh vegetables"),
                ("How long should you exercise daily?", ["10 minutes", "30 minutes", "1 hour", "2 hours"], "30 minutes"),
                ("How many hours of sleep are recommended tonight?", ["5 hours", "6 hours", "8 hours", "10 hours"], "8 hours"),
                ("Why is staying healthy important?", ["To stay active", "To lose weight only", "To sleep more", "To avoid work"], "To stay active")
            ]),
            ("Shopping for Clothes", "Yesterday, I went to the shopping mall. The store had a big sale. I bought a red jacket, blue jeans, and comfortable running shoes. I spent fifty dollars in total.", [
                ("Where did the author go yesterday?", ["Library", "Park", "Shopping mall", "Hospital"], "Shopping mall"),
                ("What special event did the store have?", ["A big sale", "A party", "A new opening", "No event"], "A big sale"),
                ("What did the author buy?", ["Jacket, jeans, and shoes", "Shirt and hat", "Dress and bag", "Socks and gloves"], "Jacket, jeans, and shoes"),
                ("What color was the jacket?", ["Blue", "Red", "Black", "Yellow"], "Red"),
                ("How much did the author spend in total?", ["$30", "$40", "$50", "$60"], "$50")
            ]),
            ("Everyday Technology", "Technology is everywhere today. Most people use computers and smartphones for work and study. We can send emails, write messages, and search for information instantly. It makes life easier.", [
                ("Where is technology today?", ["Only at work", "Everywhere", "Only in schools", "Nowhere"], "Everywhere"),
                ("What do most people use technology for?", ["Work and study", "Sleeping", "Cooking", "Driving only"], "Work and study"),
                ("What actions can be done instantly with technology?", ["Send emails, write messages, search info", "Cook food", "Clean house", "Fly to other countries"], "Send emails, write messages, search info"),
                ("What device was mentioned besides computers?", ["Smartphones", "Calculators", "Radios", "Televisions"], "Smartphones"),
                ("How does technology affect life?", ["Makes life easier", "Makes life easier", "Has no effect", "Makes life boring"], "Makes life easier")
            ]),
            ("The Football Match", "Our school football team played a match yesterday. The weather was warm. We played hard and won the game by 2-1. Our teacher and friends cheered for us excitedly.", [
                ("Who played a match yesterday?", ["School football team", "Professional players", "National team", "Teachers"], "School football team"),
                ("How was the weather yesterday?", ["Hot", "Cold", "Rainy", "Warm"], "Warm"),
                ("What was the final score of the match?", ["1-0", "2-1", "3-2", "0-0"], "2-1"),
                ("Who cheered for the team?", ["Teacher and friends", "Parents only", "Opponents", "Nobody"], "Teacher and friends"),
                ("How did the team play?", ["Hard", "Slowly", "Hard", "Badly", "Lazily"], "Hard")
            ]),
            ("Beautiful Winter", "Winter is the coldest season. In some countries, it snows and children build snowmen. The landscape looks beautiful and white. People wear warm coats, gloves, and scarves.", [
                ("Which season is the coldest?", ["Winter", "Spring", "Summer", "Autumn", "Winter"], "Winter"),
                ("What do children build in winter?", ["Sandcastles", "Snowmen", "Houses", "Kites"], "Snowmen"),
                ("How does the landscape look?", ["Green and warm", "Beautiful and white", "Grey and rainy", "Dark and dry"], "Beautiful and white"),
                ("What clothing items do people wear?", ["Coats, gloves, and scarves", "T-shirts and shorts", "Dresses and hats", "Swimwear"], "Coats, gloves, and scarves"),
                ("What falls in winter in some countries?", ["Rain", "Snow", "Leaves", "Dust"], "Snow")
            ]),
            ("The Local Museum", "The local museum exhibits ancient objects, paintings, and drawings. Yesterday, a guide showed us drawings of people from three hundred years ago. It was an educational trip.", [
                ("What does the museum exhibit?", ["Ancient objects, paintings, drawings", "Modern cars and planes", "Space rockets", "Computers and tools"], "Ancient objects, paintings, drawings"),
                ("Who showed the drawings?", ["A guide", "A teacher", "A guide", "An artist", "A doctor"], "A guide"),
                ("From when were the drawings of people?", ["300 years ago", "200 years ago", "300 years ago", "500 years ago"], "300 years ago"),
                ("What kind of trip was it?", ["Educational trip", "Boring trip", "Educational trip", "Long journey", "Shopping trip"], "Educational trip"),
                ("What is another name for pictures drawn?", ["Drawings and paintings", "Photos", "Sculptures", "Books"], "Drawings and paintings")
            ])
        ],
        "B1": [
            ("AI and the Future", "Artificial Intelligence (AI) is transforming various industries, from healthcare to finance. Experts argue that while AI can automate repetitive tasks, human creativity, critical thinking, and empathy remain irreplaceable.", [
                ("What industries are being transformed by AI?", ["Various industries including healthcare and finance", "Only gaming", "Agriculture only", "No industries yet"], "Various industries including healthcare and finance"),
                ("What can AI automate according to the text?", ["All human jobs", "Repetitive tasks", "Human emotions", "Critical thinking only"], "Repetitive tasks"),
                ("What human qualities remain irreplaceable?", ["Memory and speed", "Creativity, critical thinking, and empathy", "Repetitive labor", "Calculation skills"], "Creativity, critical thinking, and empathy"),
                ("Who argues about the impact of AI?", ["Students", "Experts", "Politicians", "Artists"], "Experts"),
                ("What is AI an acronym for?", ["Artificial Intelligence", "Advanced Integration", "Automated Industry", "Applied Internet"], "Artificial Intelligence")
            ]),
            ("Climate Action", "Climate change is a major global threat. Increasing greenhouse gases raise global temperatures. To secure our future, we must implement strategies like using renewable energy and reducing waste.", [
                ("What is climate change described as?", ["A minor local issue", "A major global threat", "A seasonal event", "A temporary problem"], "A major global threat"),
                ("What raises global temperatures?", ["Solar energy", "Greenhouse gases", "Wind turbines", "Planting trees"], "Greenhouse gases"),
                ("What must we do to secure our future?", ["Implement environmental strategies", "Use more fossil fuels", "Implement environmental strategies", "Ignore the issue", "Increase waste"], "Implement environmental strategies"),
                ("What strategies were mentioned?", ["Renewable energy and reducing waste", "Driving more cars", "Building factories", "Cutting forests"], "Renewable energy and reducing waste"),
                ("Why should we implement these actions?", ["To secure our future", "To save money only", "To increase temperatures", "To travel more"], "To secure our future")
            ]),
            ("Remote Work", "Working from home has become highly popular. It offers employees flexible schedules and eliminates the daily commute. However, it requires strong self-discipline and constant communication to stay productive.", [
                ("How popular has working from home become?", ["Less popular", "Highly popular", "Unpopular", "Only for teachers"], "Highly popular"),
                ("What benefits does remote work offer?", ["Flexible schedules and no commute", "Higher salaries and less work", "Free meals and gym access", "No responsibilities"], "Flexible schedules and no commute"),
                ("What does remote work eliminate?", ["Meetings", "Daily commute", "Salary", "Discipline"], "Daily commute"),
                ("What is required to stay productive?", ["Strong self-discipline and constant communication", "A strict boss", "Watching TV", "Working alone without talking"], "Strong self-discipline and constant communication"),
                ("What is another term for working from home?", ["Remote work", "Office work", "Manual labor", "Part-time job"], "Remote work")
            ]),
            ("Is University Essential?", "Many argue that university education is essential for a successful career. Others believe that practical work experience teaches more valuable skills. A balanced view suggests both have unique advantages.", [
                ("What do many people think about university?", ["A waste of time", "Essential for a successful career", "Only for rich people", "Very easy to complete"], "Essential for a successful career"),
                ("What do others believe teaches more valuable skills?", ["Reading books only", "Practical work experience", "Traveling", "Playing games"], "Practical work experience"),
                ("What does a balanced view suggest?", ["University is better", "Work experience is better", "Both are useless", "Both have unique advantages"], "Both have unique advantages"),
                ("What does university education aim for?", ["Successful career", "Physical strength", "Artistic talent only", "Entertainment"], "Successful career"),
                ("What is the key debate mentioned?", ["Online vs. offline learning", "Math vs. science", "University education vs. practical experience", "Full-time vs. part-time work"], "University education vs. practical experience")
            ]),
            ("Social Media Dynamics", "Social media connects millions of people globally. While it helps build professional networks, it can also lead to anxiety and the fear of missing out (FOMO). Users should manage screen time efficiently.", [
                ("Who does social media connect?", ["Only students", "Millions of people globally", "Only families", "Business managers only"], "Millions of people globally"),
                ("What does it help build?", ["Factories", "Professional networks", "Highways", "New languages"], "Professional networks"),
                ("What negative psychological impacts are mentioned?", ["Depression and fatigue", "Anxiety and FOMO", "Anger and aggression", "Boredom and laziness"], "Anxiety and FOMO"),
                ("What does FOMO stand for?", ["Fear of missing out", "Focus on major options", "Future of mobile online", "None of the above"], "Fear of missing out"),
                ("How should users manage their screen time?", ["Inefficiently", "Efficiently", "By increasing it", "By stopping completely"], "Efficiently")
            ]),
            ("A Balanced Diet", "Eating a balanced diet with protein, complex carbohydrates, and vitamins is crucial. It supports your immune system and maintains energy levels. Avoid excessive sugars and processed food for better health.", [
                ("What should a balanced diet contain?", ["Protein, complex carbohydrates, vitamins", "Sugars and fats only", "Fast food and soda", "Only water"], "Protein, complex carbohydrates, vitamins"),
                ("What does a balanced diet support?", ["Immune system and energy levels", "Muscle building only", "Sleeping hours", "Mental focus only"], "Immune system and energy levels"),
                ("What should be avoided for better health?", ["Vitamins", "Excessive sugars and processed food", "Vegetables", "Water"], "Excessive sugars and processed food"),
                ("Why should you avoid processed food?", ["Because it is cheap", "For better health", "Because it is hard to cook", "Because it contains vitamins"], "For better health"),
                ("What type of carbohydrates are recommended?", ["Simple carbohydrates", "Complex carbohydrates", "Refined carbohydrates", "No carbohydrates"], "Complex carbohydrates")
            ]),
            ("Green Energy Resources", "Solar and wind energy are sustainable resources. Unlike fossil fuels, they do not release greenhouse gases. Transitioning to green energy is key to reducing air pollution and protecting nature.", [
                ("What are solar and wind energy described as?", ["Fossil fuels", "Sustainable resources", "Expensive energy", "Temporary solutions"], "Sustainable resources"),
                ("How do they differ from fossil fuels?", ["They release more carbon", "They do not release greenhouse gases", "They are harder to find", "They pollute air"], "They do not release greenhouse gases"),
                ("What is key to reducing air pollution?", ["Burning more coal", "Transitioning to green energy", "Using more cars", "Building more houses"], "Transitioning to green energy"),
                ("What does green energy protect?", ["Fossil fuels", "Factories", "Nature", "Cars"], "Nature"),
                ("What are two types of green energy mentioned?", ["Coal and gas", "Solar and wind", "Nuclear and oil", "Water and steam"], "Solar and wind")
            ])
        ]
    },
    "listening": {
        "A1": [
            ("Weather Forecast", "Good morning! Today it will be sunny and warm in Hanoi. The temperature will be 28 degrees Celsius. In the evening, it will be cool, so take a light jacket.", [
                ("What will the weather be like today?", ["Rainy", "Sunny and warm", "Snowy", "Windy"], "Sunny and warm"),
                ("Where is the forecast for?", ["Hanoi", "Saigon", "Danang", "Hue"], "Hanoi"),
                ("What will the temperature be?", ["20 degrees Celsius", "25 degrees Celsius", "28 degrees Celsius", "32 degrees Celsius"], "28 degrees Celsius"),
                ("How will the weather be in the evening?", ["Hot", "Cold", "Cool", "Rainy"], "Cool"),
                ("What should you take in the evening?", ["An umbrella", "A light jacket", "A hat", "Gloves"], "A light jacket")
            ]),
            ("Meeting a Friend", "Hi John! Long time no see. How is your sister? She is good, she started school last week. Let's drink some milk tea at the shop.", [
                ("Who is the speaker talking to?", ["John", "Sam", "Tom", "Alex"], "John"),
                ("How is John's sister?", ["She is sick", "She is good", "She is tired", "She is busy"], "She is good"),
                ("What did the sister do last week?", ["Went on holiday", "Started school", "Started work", "Visited the hospital"], "Started school"),
                ("What do they want to drink?", ["Coffee", "Milk tea", "Fruit juice", "Water"], "Milk tea"),
                ("Where do they want to go?", ["To the shop", "To the park", "To school", "To the shop", "To the cinema"], "To the shop")
            ]),
            ("At the Market", "Hello, I want to buy one kilogram of apples and some bread, please. That will be five dollars. Here you go, thank you.", [
                ("What does the customer buy?", ["Apples and bread", "Oranges and milk", "Bananas and eggs", "Meat and bread"], "Apples and bread"),
                ("How many apples does the customer want?", ["One kilogram", "Two kilograms", "Three pieces", "Five pieces"], "One kilogram"),
                ("How much does the customer pay?", ["$3", "$4", "$5", "$6"], "$5"),
                ("Who is the customer speaking to?", ["A friend", "A seller", "A teacher", "A doctor"], "A seller"),
                ("What word does the customer say at the end?", ["Goodbye", "Thank you", "Sorry", "Hello"], "Thank you")
            ]),
            ("Daily Routine", "I wake up at 7 AM. I wash my face and brush my teeth. I eat breakfast at 7:30. I walk to school because my house is very close.", [
                ("What time does the speaker wake up?", ["6 AM", "7 AM", "8 AM", "9 AM"], "7 AM"),
                ("What does the speaker do first after waking up?", ["Wash face and brush teeth", "Eat breakfast", "Go to school", "Read a book"], "Wash face and brush teeth"),
                ("What time is breakfast?", ["7:00 AM", "7:30 AM", "8:00 AM", "8:30 AM"], "7:30 AM"),
                ("How does the speaker go to school?", ["By bus", "By car", "Walk", "By bicycle"], "Walk"),
                ("Why does the speaker walk to school?", ["House is close", "No bus", "Likes exercise", "It is cheap"], "House is close")
            ]),
            ("My Family Pet", "My family has a beautiful white cat. She sleeps on my bed every night. She eats fish and drinks fresh water. We love her very much.", [
                ("What animal does the family have?", ["A dog", "A cat", "A bird", "A rabbit"], "A cat"),
                ("What color is the cat?", ["Black", "White", "Brown", "Grey"], "White"),
                ("Where does the cat sleep?", ["On the bed", "Under the table", "On the chair", "In the garden"], "On the bed"),
                ("What does the cat eat?", ["Meat", "Fish", "Bread", "Rice"], "Fish"),
                ("What does the cat drink?", ["Milk", "Water", "Juice", "Tea"], "Water")
            ]),
            ("In the Classroom", "Open your English book to page 15. Listen to the conversation and write the words. Do your homework before tomorrow.", [
                ("What book should the students open?", ["Math book", "English book", "Science book", "History book"], "English book"),
                ("What page should the students open?", ["Page 5", "Page 10", "Page 15", "Page 20"], "Page 15"),
                ("What should the students write?", ["The sentences", "The numbers", "The words", "The answers"], "The words"),
                ("When must the homework be done?", ["Before tomorrow", "Before next week", "Tonight", "Next Monday"], "Before tomorrow"),
                ("What should the students listen to?", ["The music", "The conversation", "The teacher only", "The radio"], "The conversation")
            ]),
            ("Weekend Plans", "On Saturday, I will go to the park with my brother. We will play football. On Sunday, I will stay at home and read a book.", [
                ("When will the speaker go to the park?", ["On Saturday", "On Sunday", "Tomorrow", "Next week"], "On Saturday"),
                ("Who will the speaker go to the park with?", ["Father", "Mother", "Brother", "Sister"], "Brother"),
                ("What game will they play?", ["Basketball", "Football", "Tennis", "Chess"], "Football"),
                ("What will the speaker do on Sunday?", ["Stay at home and read a book", "Go to the market", "Play football", "Visit friends"], "Stay at home and read a book"),
                ("Where will they play football?", ["At school", "In the park", "In the garden", "On the street"], "In the park")
            ])
        ],
        "A2": [
            ("Hotel Booking", "Welcome to Grand Hotel. I have a booking under the name of Sarah Smith. Yes, a double room for three nights. Here is your key card, room 405.", [
                ("Under what name is the booking?", ["Sarah Smith", "Jane Doe", "Lisa Chen", "Mary Jones"], "Sarah Smith"),
                ("What type of room is booked?", ["A single room", "A double room", "A suite", "A family room"], "A double room"),
                ("How many nights will Sarah stay?", ["2 nights", "3 nights", "4 nights", "5 nights"], "3 nights"),
                ("What room number was given?", ["Room 304", "Room 405", "Room 506", "Room 101"], "Room 405"),
                ("What card was handed to the customer?", ["Credit card", "ID card", "Key card", "Member card"], "Key card")
            ]),
            ("Airport Announcement", "Attention passengers of flight VN123 to Tokyo. The flight is delayed by thirty minutes due to weather. New departure time is 10:30 AM.", [
                ("What is the flight number mentioned?", ["VN123", "VN456", "VN789", "VN100"], "VN123"),
                ("Where is the flight going?", ["Paris", "Tokyo", "London", "Hanoi"], "Tokyo"),
                ("Why is the flight delayed?", ["Due to maintenance", "Due to weather", "Due to traffic", "No reason given"], "Due to weather"),
                ("How long is the delay?", ["15 minutes", "30 minutes", "45 minutes", "1 hour"], "30 minutes"),
                ("What is the new departure time?", ["10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM"], "10:30 AM")
            ]),
            ("Directions to the Museum", "Excuse me, how can I go to the local museum? Walk straight for two blocks, then turn left at the traffic light. The museum is on your right.", [
                ("What place is the tourist asking for directions to?", ["The hotel", "The station", "The local museum", "The park"], "The local museum"),
                ("How far should the tourist walk straight?", ["One block", "Two blocks", "Three blocks", "Five blocks"], "Two blocks"),
                ("Where should the tourist turn?", ["Right", "Left", "Back", "Around"], "Left"),
                ("Where is the museum located?", ["On the left", "On the right", "Straight ahead", "Behind the park"], "On the right"),
                ("Where should the turn be made?", ["At the traffic light", "At the corner", "At the bus stop", "At the bridge"], "At the traffic light")
            ]),
            ("Doctor's Advice", "You have a cold. You should take this medicine twice a day after meals. Drink warm water and do not do heavy exercise for a week.", [
                ("What illness does the patient have?", ["A fever", "A cold", "A headache", "A stomachache"], "A cold"),
                ("How often should the patient take medicine?", ["Once a day", "Twice a day", "Three times a day", "Every hour"], "Twice a day"),
                ("When should the medicine be taken?", ["Before meals", "After meals", "During meals", "Before sleep"], "After meals"),
                ("What kind of water should the patient drink?", ["Cold water", "Warm water", "Ice water", "Soda"], "Warm water"),
                ("What should the patient avoid for a week?", ["Sleeping", "Working", "Heavy exercise", "Eating"], "Heavy exercise")
            ]),
            ("Leisure Hobbies", "My hobby is taking photos of nature. I carry my camera whenever I travel to the mountains or the beach. It helps me relax.", [
                ("What is the speaker's hobby?", ["Taking photos of nature", "Hiking in mountains", "Swimming", "Painting"], "Taking photos of nature"),
                ("What device does the speaker carry?", ["A phone", "A camera", "A laptop", "A book"], "A camera"),
                ("Where does the speaker travel to take photos?", ["Mountains or beach", "Big cities", "Museums", "Markets"], "Mountains or beach"),
                ("How does the hobby help the speaker?", ["Helps earn money", "Helps relax", "Helps make friends", "Helps study"], "Helps relax"),
                ("What does the speaker take photos of?", ["Nature", "People", "Cars", "Nature", "Buildings"], "Nature")
            ]),
            ("The Shopping Sale", "Great news! The clothes store is having a winter sale. Get up to fifty percent discount on warm coats, jackets, and boots. Sale ends Sunday.", [
                ("Which store is having a sale?", ["The book store", "The clothes store", "The food market", "The phone shop"], "The clothes store"),
                ("What season is the sale for?", ["Spring", "Summer", "Autumn", "Winter"], "Winter"),
                ("What is the maximum discount offered?", ["20%", "30%", "40%", "50%"], "50%"),
                ("What items are mentioned in the sale?", ["Coats, jackets, boots", "T-shirts, shorts, shoes", "Hats, gloves, socks", "Jeans and shirts"], "Coats, jackets, boots"),
                ("When does the sale end?", ["Friday", "Saturday", "Sunday", "Monday"], "Sunday")
            ]),
            ("Traditional Festival", "Tomorrow is the spring festival in our village. There will be music, traditional games, and delicious local food. Everyone wears colorful clothes.", [
                ("When is the spring festival in the village?", ["Today", "Tomorrow", "Next week", "Yesterday"], "Tomorrow"),
                ("What season is the festival for?", ["Spring", "Summer", "Autumn", "Winter"], "Spring"),
                ("What activities will be at the festival?", ["Music and traditional games", "Movie watching", "Shopping sale", "Sports match"], "Music and traditional games"),
                ("What do people wear at the festival?", ["Warm coats", "Colorful clothes", "School uniforms", "Black suits"], "Colorful clothes"),
                ("Where is the festival held?", ["In the city", "In the village", "At school", "At the hotel"], "In the village")
            ])
        ],
        "B1": [
            ("Tech Interview", "Welcome. Today we interview Lisa Chen, CEO of TechVibe. She highlights the role of digital collaboration tools in boosting employee productivity.", [
                ("Who is being interviewed today?", ["Sarah Smith", "Lisa Chen", "John Doe", "Alex Wang"], "Lisa Chen"),
                ("What is Lisa Chen's position?", ["Manager", "Developer", "CEO of TechVibe", "Designer"], "CEO of TechVibe"),
                ("What tools does she highlight?", ["Programming tools", "Digital collaboration tools", "Hardware tools", "Design tools"], "Digital collaboration tools"),
                ("What do these tools boost?", ["Product prices", "Employee productivity", "Server speed", "Internet connection"], "Employee productivity"),
                ("What is the company name?", ["TechVibe", "TechSoft", "GrandHotel", "CloudTech"], "TechVibe")
            ]),
            ("Environmental Strategy", "To secure a green future, our city is implementing a new waste recycling program. Citizens must separate plastic, glass, and organic waste starting next month.", [
                ("Why is the city implementing a new waste program?", ["To save money", "To secure a green future", "To build new roads", "To clean offices"], "To secure a green future"),
                ("What must citizens separate starting next month?", ["Plastic, glass, and organic waste", "Paper and metal", "Electronic waste", "Nothing"], "Plastic, glass, and organic waste"),
                ("When does the new program start?", ["Today", "Tomorrow", "Next week", "Next month"], "Next month"),
                ("What kind of program is it?", ["Waste recycling program", "Water clean program", "Solar panel program", "Tree planting program"], "Waste recycling program"),
                ("Who is responsible for separating the waste?", ["Sanitation workers", "Citizens", "Government officials", "Students"], "Citizens")
            ]),
            ("Workplace Flexibility", "Workplace flexibility is a key factor in employee retention. Allowing team members to schedule their hours improves work-life balance and overall focus.", [
                ("What is a key factor in employee retention?", ["High salaries", "Workplace flexibility", "Free lunch", "Short working hours"], "Workplace flexibility"),
                ("What are team members allowed to schedule?", ["Their tasks", "Their hours", "Their holidays", "Their meetings"], "Their hours"),
                ("What does scheduling their own hours improve?", ["Work-life balance and overall focus", "Salary size", "Travel time", "Vacation days"], "Work-life balance and overall focus"),
                ("Who benefits from the flexibility?", ["Employees and team members", "Clients only", "Government", "Server managers"], "Employees and team members"),
                ("What is another term for scheduling hours flexibly?", ["Flexible scheduling", "Overtime", "Part-time", "Shift work"], "Flexible scheduling")
            ]),
            ("Software Update", "Please save all your files and log out. We are performing a critical database backup and software update on the server between 11 PM and 1 AM.", [
                ("What should users do before logging out?", ["Close window", "Save all files", "Delete account", "Send email"], "Save all files"),
                ("What critical operations are being performed?", ["Hardware repair", "Database backup and software update", "Server moving", "Account creation"], "Database backup and software update"),
                ("Between what hours is the update happening?", ["9 PM and 12 AM", "11 PM and 1 AM", "12 AM and 2 AM", "10 PM and 11 PM"], "11 PM and 1 AM"),
                ("Where are the backup and update happening?", ["On the database only", "On the local computer", "On the server", "On the website"], "On the server"),
                ("Why should you log out?", ["Because it is late", "Because of the update and backup", "To save energy", "To avoid errors on PC"], "Because of the update and backup")
            ]),
            ("Workplace Communication", "Constant feedback is essential for project success. Team leaders should hold weekly progress meetings to review targets and address status warnings.", [
                ("What is essential for project success?", ["High speed", "Constant feedback", "Expensive tools", "Working alone"], "Constant feedback"),
                ("Who should hold weekly progress meetings?", ["Team leaders", "Clients", "All workers", "Office managers"], "Team leaders"),
                ("How often should progress meetings be held?", ["Daily", "Weekly", "Monthly", "Quarterly"], "Weekly"),
                ("What should be reviewed in the meetings?", ["Targets and address status warnings", "Salaries", "Holidays", "Code syntax"], "Targets and address status warnings"),
                ("What is another name for milestones to achieve?", ["Targets", "Bugs", "Frameworks", "Backups"], "Targets")
            ]),
            ("Healthy Eating Habits", "To maintain energy, health experts recommend eating complex carbohydrates and avoiding processed foods containing excessive refined sugars.", [
                ("What do health experts recommend eating?", ["Simple carbohydrates", "Complex carbohydrates", "Sugars", "Processed food"], "Complex carbohydrates"),
                ("What should be avoided according to experts?", ["Vitamins", "Processed foods containing refined sugars", "Water", "Fruit juice"], "Processed foods containing refined sugars"),
                ("Why are complex carbohydrates recommended?" , ["To sleep better", "To maintain energy", "To lose weight", "To build muscle"], "To maintain energy"),
                ("What do processed foods contain excessive amounts of?", ["Proteins", "Refined sugars", "Vitamins", "Fiber"], "Refined sugars"),
                ("Who gave these healthy eating recommendations?", ["Doctors only", "Health experts", "Teachers", "Sports coaches"], "Health experts")
            ]),
            ("Solar Energy Transition", "Transitioning to solar power reduces carbon emissions significantly. The government offers subsidies for installing solar panels on residential roofs.", [
                ("What does transitioning to solar power reduce?", ["Installation costs", "Carbon emissions", "Sunlight hours", "Electricity usage"], "Carbon emissions"),
                ("How much are carbon emissions reduced?", ["Slightly", "Significantly", "Not at all", "Double"], "Significantly"),
                ("What does the government offer for installing solar panels?", ["Free panels", "Subsidies", "Loans", "Nothing"], "Subsidies"),
                ("Where are the solar panels installed?", ["On residential roofs", "In the gardens", "In the streets", "In the offices"], "On residential roofs"),
                ("What does transitioning to solar power help protect?", ["Fossil fuels", "The environment and nature", "Roofs", "Government budget"], "The environment and nature")
            ])
        ]
    }
}

# Detailed prompts for Writing & Speaking (5 guide questions each)
WRITING_PROMPTS = {
    "A1": [
        ("A Friendly Letter", "Write a letter (50-80 words) to your friend. Answer these 5 guide questions:\n1. What is your friend's name?\n2. Where does your friend live?\n3. Who is in your family?\n4. What is your school name?\n5. Why do you like your school?"),
        ("My Daily Routine", "Describe your daily routine (60-80 words). Cover these 5 questions:\n1. What time do you wake up?\n2. What do you eat for breakfast?\n3. How do you go to school/work?\n4. What time do you finish study/work?\n5. What time do you go to bed?"),
        ("Favorite Food", "Write about your favorite food (50-70 words). Cover these 5 questions:\n1. What is your favorite food?\n2. What does it taste like?\n3. How often do you eat it?\n4. Who cooks it for you?\n5. Why do you like it?"),
        ("My House", "Write a description of your house or room (60 words). Cover these 5 questions:\n1. Is your house big or small?\n2. What color is the front door?\n3. How many windows are in your room?\n4. Where is your desk?\n5. What is on your bed?"),
        ("Weekend Activities", "Write about your weekend activities (60-80 words). Cover these 5 questions:\n1. Who do you play with on Saturday?\n2. What games do you play?\n3. Where do you go?\n4. What do you do on Sunday?\n5. Do you enjoy your weekend?"),
        ("My Pet", "Describe your pet dog, cat, or an animal you like (50-70 words). Cover these 5 questions:\n1. What animal is it?\n2. What is its name?\n3. What color is its hair?\n4. What does it eat?\n5. Where does it sleep?"),
        ("Meet My Teacher", "Write a paragraph about your English teacher (50-70 words). Cover these 5 questions:\n1. What is your teacher's name?\n2. Is your teacher nice?\n3. What do you learn in class?\n4. What book do you use?\n5. Why do you like this class?")
    ],
    "A2": [
        ("An Email invitation", "Write an email to invite your friend to a holiday (80-100 words). Cover these 5 questions:\n1. Where is the holiday beach?\n2. What hotel will you stay at?\n3. What dates are you going?\n4. What luggage should they pack?\n5. What activities will you do together?"),
        ("My Last Holiday", "Describe your last trip or holiday (100-120 words). Cover these 5 questions:\n1. Where did you travel?\n2. Who went with you?\n3. What museum or place did you explore?\n4. How was the food and climate?\n5. What was the best part of the trip?"),
        ("Healthy Habits", "Write an essay advising a friend on healthy habits (100-120 words). Cover these 5 questions:\n1. Why is fresh food important?\n2. How much water should they drink?\n3. What sport or exercise should they do?\n4. How many hours should they sleep?\n5. What bad food should they avoid?"),
        ("A Review of a Movie", "Write a review of a movie or film you watched recently (100-120 words). Cover these 5 questions:\n1. What is the movie title?\n2. Who are the main actors?\n3. What is the story about?\n4. How was the music and camera work?\n5. Why do you recommend it?"),
        ("Shopping Experience", "Describe a shopping trip you made recently (100 words). Cover these 5 questions:\n1. What store or mall did you visit?\n2. What item (clothes, phone, book) did you buy?\n3. How much did you pay?\n4. Was there a sale discount?\n5. Are you happy with your purchase?"),
        ("Life in a Village", "Compare life in a big city with life in a quiet village (100-120 words). Cover these 5 questions:\n1. Which place has cleaner air?\n2. Where is it quieter?\n3. What activities can you do in a village?\n4. Where is it easier to find a job?\n5. Which place do you prefer?"),
        ("A Special Festival", "Describe a traditional festival like Tet (100-120 words). Cover these 5 questions:\n1. What is the festival name?\n2. When does it happen?\n3. What special food do people eat?\n4. What colorful clothes do they wear?\n5. What traditional games do they play?")
    ],
    "B1": [
        ("University vs. Experience", "Some think university is essential, others prefer work experience. Discuss (200-250 words) answering these 5 questions:\n1. What are the advantages of a university degree?\n2. How does practical experience help you acquire skills?\n3. Which option do employers prefer?\n4. What are the costs and benefits of university?\n5. What is your balanced conclusion?"),
        ("Working Remotely", "Discuss the advantages and disadvantages of working from home (200-250 words). Cover these 5 questions:\n1. How does remote work eliminate the daily commute?\n2. In what ways does it offer flexible schedules?\n3. Why does it require strong self-discipline?\n4. How does constant communication prevent isolation?\n5. What is your final recommendation?"),
        ("Impact of Social Media", "Analyze the positive and negative impacts of social media (200-250 words). Cover these 5 questions:\n1. How does social media connect people globally?\n2. How does it help build professional networks?\n3. Why does it cause anxiety and FOMO?\n4. How does screen time affect productivity?\n5. How can users manage screen time efficiently?"),
        ("Climate Change Action", "What strategies should local governments implement to protect nature? Write 200-250 words covering:\n1. What is the main source of air pollution?\n2. How do greenhouse gases affect temperature?\n3. Why should cities transition to solar energy?\n4. What recycling rules should be set?\n5. How can citizens contribute?"),
        ("Workplace Flexibility", "Is flexible scheduling beneficial for team productivity? Write 200-250 words covering:\n1. What is flexible scheduling?\n2. How does it improve work-life balance?\n3. How does it affect employee retention?\n4. What tools help coordinate flexible teams?\n5. How can team leaders monitor targets?"),
        ("Technology in Education", "Does technology make learning more efficient, or does it distract students? Write 200-250 words covering:\n1. What devices are used in classrooms?\n2. How does the internet help research?\n3. What distractions do smartphones cause?\n4. How can teachers balance technology use?\n5. What is your personal experience?"),
        ("Renewable Energy Transition", "Discuss the importance of transitioning to sustainable green energy (200-250 words). Cover:\n1. What are the main green energy resources?\n2. How do they reduce carbon emissions?\n3. What are the limits of fossil fuels?\n4. What subsidies should the government offer?\n5. How does green energy affect nature?")
    ]
}

SPEAKING_PROMPTS = {
    "A1": [
        ("Introduce Yourself", "Speak for 1-2 minutes. Address these 5 questions:\n1. What is your name?\n2. How old are you?\n3. What country are you from?\n4. Who is in your family?\n5. What is your hobby?"),
        ("Talk About Your Classroom", "Describe your classroom. Cover these 5 questions:\n1. Is your classroom big or small?\n2. Where is the teacher's desk?\n3. How many chairs are in the room?\n4. Is there a clock on the wall?\n5. What can you see out the window?"),
        ("My Daily Activities", "Talk about your daily routine. Cover these 5 questions:\n1. What time do you wake up?\n2. What do you drink in the morning?\n3. Do you walk to school/work?\n4. What do you do in the afternoon?\n5. What time do you sleep?"),
        ("Favorite Fruits", "Describe your favorite fruits. Cover these 5 questions:\n1. What is your favorite fruit?\n2. What color is it?\n3. What does it taste like?\n4. How often do you eat it?\n5. Where do you buy it?"),
        ("My Best Friend", "Describe your best friend. Cover these 5 questions:\n1. What is your friend's name?\n2. How old is your friend?\n3. What does your friend look like?\n4. What games do you play together?\n5. Why do you like them?"),
        ("Weather Today", "Talk about the weather today. Cover these 5 questions:\n1. Is it hot, cold, or warm today?\n2. Is the sun shining?\n3. Is it raining or windy?\n4. What clothes are you wearing?\n5. Do you like this weather?"),
        ("My Pet Max", "Talk about your pet or an animal you love. Cover these 5 questions:\n1. What animal is it?\n2. What does it look like?\n3. What does it eat?\n4. What is its name?\n5. Where does it play?")
    ],
    "A2": [
        ("A Trip I Remember", "Describe a trip or holiday you enjoyed. Address these 5 questions:\n1. Where did you travel?\n2. How did you travel there?\n3. What hotel or beach did you visit?\n4. What did you explore?\n5. Why do you remember this trip?"),
        ("Healthy Living Advice", "Give advice on how to keep fit. Address these 5 questions:\n1. What food should a person eat?\n2. What drinks should they avoid?\n3. What sports should they play?\n4. How many hours should they sleep?\n5. Why is exercise important?"),
        ("Shopping for Gifts", "Talk about buying a gift for a friend. Address these 5 questions:\n1. Who did you buy the gift for?\n2. What was the event?\n3. What gift (book, card, toy) did you choose?\n4. How much did you pay?\n5. How did your friend feel?"),
        ("A Film I Liked", "Describe a movie or film you watched recently. Address these 5 questions:\n1. What was the movie title?\n2. Who were the actors?\n3. Where did you watch it (theater/home)?\n4. What was the story about?\n5. Why did you like it?"),
        ("My Favorite Season", "Talk about your favorite season of the year. Address these 5 questions:\n1. What is your favorite season?\n2. What is the weather like in this season?\n3. What clothes do you wear?\n4. What activities do you do?\n5. Why do you like it?"),
        ("Staying Connected", "Talk about how you use technology to keep in touch. Address these 5 questions:\n1. Do you use email or phone calls?\n2. How often do you send messages?\n3. What internet chats do you use?\n4. Who do you contact most?\n5. Why is communication important?"),
        ("Village vs. City", "Describe life in a quiet village compared to a busy city. Cover:\n1. Where is it noisier?\n2. Where are there more cars and traffic?\n3. Where is the air cleaner?\n4. Where is it easier to find shops?\n5. Which place do you prefer?")
    ],
    "B1": [
        ("Academic Goals vs. Experience", "Discuss university studies vs. practical experience. Cover these 5 questions:\n1. What are your main academic goals?\n2. How does work experience help develop skills?\n3. Which is more important for a career?\n4. What skills have you acquired practically?\n5. What advice would you give to a student?"),
        ("Workplace Productivity", "Talk about team productivity and flexible scheduling. Cover:\n1. How does flexible hours improve focus?\n2. Why is constant communication important?\n3. What tools help coordinate team targets?\n4. How do you handle project deadlines?\n5. How should team leaders give feedback?"),
        ("Social Media and FOMO", "Discuss the psychological impact of social media. Cover these 5 questions:\n1. How do constant notifications affect focus?\n2. What causes anxiety and FOMO on social media?\n3. How much screen time is healthy?\n4. How can users control their screen time?\n5. What is your personal experience?"),
        ("Protecting the Environment", "Describe strategies to secure a green future. Cover these 5 questions:\n1. How can cities reduce greenhouse gases?\n2. What is the role of solar and wind energy?\n3. How should waste recycling be managed?\n4. What can local citizens do daily?\n5. How does pollution affect human health?"),
        ("Learning a New Skill", "Talk about a skill you want to acquire or develop. Cover:\n1. What skill do you want to learn?\n2. What tools or resources do you need?\n3. What challenges do you expect to face?\n4. How will you schedule your practice time?\n5. How will this skill help your career?"),
        ("Transition to Green Energy", "Discuss the importance of transitioning to solar power. Cover:\n1. Why are fossil fuels bad for nature?\n2. What are the benefits of solar energy?\n3. What are the main challenges of solar installation?\n4. What subsidies should the government offer?\n5. How does this transition affect health?"),
        ("The Role of AI", "Discuss how AI might automate tasks in the future. Cover:\n1. What repetitive tasks can AI automate?\n2. What jobs are safe from automation?\n3. How does AI help in healthcare or education?\n4. What are the main risks of AI?\n5. How should students prepare for the AI future?")
    ]
}

# ---------------------------------------------------------------------------
# Seed 15 Vocabulary Questions per level (45 total)
# ---------------------------------------------------------------------------

VOCAB_QUESTIONS = {
    "A1": [
        ("Từ nào sau đây có nghĩa là 'gia đình'?", ["school", "book", "family", "friend"], "family"),
        ("Từ 'teacher' có nghĩa tiếng Việt là gì?", ["học sinh", "giáo viên", "bác sĩ", "y tá"], "giáo viên"),
        ("Chọn từ viết đúng chính tả cho từ 'xin chào':", ["helo", "hello", "hellow", "heloo"], "hello"),
        ("Từ nào là 'bút mực'?", ["pencil", "pen", "desk", "paper"], "pen"),
        ("Điền từ vào chỗ trống: 'I sleep in my ______.'", ["chair", "desk", "bed", "clock"], "bed"),
        ("Từ 'milk' thuộc loại từ nào?", ["Động từ", "Danh từ", "Tính từ", "Trạng từ"], "Danh từ"),
        ("Từ nào có nghĩa là 'nóng'?", ["cold", "hot", "warm", "cool"], "hot"),
        ("Từ 'run' có nghĩa là gì?", ["đi bộ", "chạy", "ngủ", "chơi"], "chạy"),
        ("Chọn từ trái nghĩa với 'happy':", ["sad", "good", "angry", "tired"], "sad"),
        ("Từ nào có nghĩa là 'quả táo'?", ["orange", "banana", "apple", "milk"], "apple"),
        ("Từ 'student' nghĩa là gì?", ["học sinh/sinh viên", "giáo viên", "người lớn", "trẻ em"], "học sinh/sinh viên"),
        ("Điền từ: 'Please close the ______ because it is cold.'", ["window", "table", "clock", "floor"], "window"),
        ("Từ nào nghĩa là 'thành phố'?", ["country", "town", "city", "village"], "city"),
        ("Từ 'buy' thuộc nhóm từ loại nào?", ["noun", "verb", "adjective", "adverb"], "verb"),
        ("Từ 'water' nghĩa là gì?", ["sữa", "nước", "bánh mì", "cam"], "nước")
    ],
    "A2": [
        ("Từ 'travel' có nghĩa là gì?", ["khám phá", "du lịch", "chuyến bay", "sân bay"], "du lịch"),
        ("Từ nào sau đây nghĩa là 'ngọn núi'?", ["beach", "lake", "mountain", "river"], "mountain"),
        ("Điền từ vào chỗ trống: 'We arrived at the ______ to catch our flight.'", ["hotel", "airport", "museum", "garden"], "airport"),
        ("Từ 'luggage' có nghĩa là gì?", ["vé", "hành lý", "khách sạn", "tour du lịch"], "hành lý"),
        ("Từ nào có nghĩa là 'mùa đông'?", ["spring", "summer", "autumn", "winter"], "winter"),
        ("Từ 'medicine' nghĩa là gì?", ["bác sĩ", "y tá", "thuốc", "bệnh viện"], "thuốc"),
        ("Từ nào sau đây nghĩa là 'nghệ sĩ'?", ["actor", "artist", "writer", "poet"], "artist"),
        ("Điền từ: 'The tour ______ showed us around the ancient museum.'", ["guide", "writer", "reporter", "nurse"], "guide"),
        ("Từ 'explore' có nghĩa là gì?", ["khám phá", "nghỉ ngơi", "chạy bộ", "chụp ảnh"], "khám phá"),
        ("Chọn từ có nghĩa là 'khí hậu':", ["weather", "climate", "season", "wind"], "climate"),
        ("Từ 'movie' đồng nghĩa với từ nào sau đây?", ["song", "painting", "film", "drawing"], "film"),
        ("Từ 'hotel' nghĩa là gì?", ["sân bay", "viện bảo tàng", "khách sạn", "nhà hát"], "khách sạn"),
        ("Từ 'camera' dùng để làm gì?", ["nghe nhạc", "chụp ảnh", "đọc báo", "viết bài"], "chụp ảnh"),
        ("Từ nào nghĩa là 'bức họa'?", ["painting", "drawing", "photo", "camera"], "painting"),
        ("Từ 'health' có nghĩa là gì?", ["thể thao", "trận đấu", "sức khỏe", "bài tập"], "sức khỏe")
    ],
    "B1": [
        ("Từ 'achieve' có nghĩa là gì?", ["đạt được", "thất bại", "phát triển", "triển khai"], "đạt được"),
        ("Từ nào sau đây nghĩa là 'phức tạp'?", ["simple", "complex", "constant", "efficient"], "complex"),
        ("Điền từ: 'We need to ______ the database queries for faster results.'", ["direct", "optimize", "install", "restore"], "optimize"),
        ("Từ 'feedback' nghĩa là gì?", ["phản hồi", "yêu cầu", "báo cáo", "tóm tắt"], "phản hồi"),
        ("Từ nào có nghĩa là 'bằng chứng'?", ["conclusion", "evidence", "analysis", "concept"], "evidence"),
        ("Từ 'secure' có nghĩa là gì?", ["nguy hiểm", "bảo mật, an toàn", "chậm trễ", "phức tạp"], "bảo mật, an toàn"),
        ("Từ 'deadline' nghĩa là gì?", ["hạn chót", "lịch trình", "báo cáo", "cuộc họp"], "hạn chót"),
        ("Chọn từ có nghĩa là 'sự đổi mới sáng tạo':", ["strategy", "innovation", "analysis", "resource"], "innovation"),
        ("Từ 'client' nghĩa là gì?", ["máy chủ", "máy khách / khách hàng", "phần mềm", "tài nguyên"], "máy khách / khách hàng"),
        ("Từ 'implement' nghĩa là gì?", ["lên kế hoạch", "thực thi, triển khai", "đánh giá", "sao lưu"], "thực thi, triển khai"),
        ("Từ 'database' nghĩa là gì?", ["hệ thống", "cơ sở dữ liệu", "mạng lưới", "phần cứng"], "cơ sở dữ liệu"),
        ("Từ 'framework' nghĩa là gì?", ["khung làm việc", "phần mềm", "mã nguồn", "ứng dụng"], "khung làm việc"),
        ("Điền từ: 'Please enter your ______ to login to your account.'", ["password", "profile", "notification", "status"], "password"),
        ("Từ 'progress' có nghĩa là gì?", ["trạng thái", "tiến trình, tiến bộ", "kết quả", "tổng cộng"], "tiến trình, tiến bộ"),
        ("Từ 'efficiency' (danh từ của efficient) nghĩa là gì?", ["sự phức tạp", "hiệu suất, hiệu quả", "sự đổi mới", "sự an toàn"], "hiệu suất, hiệu quả")
    ]
}

# ---------------------------------------------------------------------------
# Topic Classification Helper
# ---------------------------------------------------------------------------

def classify_topic(word, word_type):
    w = word.lower()
    topics = [
        "people", "school", "home", "food", "verbs", "adjectives", 
        "travel", "weather", "nature", "health", "arts", "tech", 
        "communication", "professional"
    ]
    if any(x in w for x in ['family', 'friend', 'father', 'mother', 'brother', 'sister', 'child', 'baby', 'boy', 'girl', 'man', 'woman', 'person', 'people', 'kid']):
        return 'people'
    elif any(x in w for x in ['school', 'class', 'teacher', 'student', 'book', 'pen', 'pencil', 'paper', 'desk', 'chair', 'learn', 'study']):
        return 'school'
    elif any(x in w for x in ['door', 'window', 'room', 'house', 'home', 'table', 'bed', 'clock', 'watch', 'phone', 'computer', 'key', 'box', 'bag']):
        return 'home'
    elif any(x in w for x in ['water', 'milk', 'bread', 'apple', 'banana', 'orange', 'food', 'drink', 'eat', 'cook', 'sauce', 'shake', 'meal', 'fruit']):
        return 'food'
    elif any(x in w for x in ['travel', 'airport', 'ticket', 'flight', 'hotel', 'luggage', 'tourist', 'museum', 'beach', 'mountain', 'forest', 'river', 'lake', 'trip', 'tour', 'journey']):
        return 'travel'
    elif any(x in w for x in ['weather', 'climate', 'season', 'spring', 'summer', 'autumn', 'winter', 'rain', 'wind', 'sun', 'moon', 'star', 'sky', 'cloud', 'storm']):
        return 'weather'
    elif any(x in w for x in ['health', 'doctor', 'nurse', 'hospital', 'medicine', 'exercise', 'sport', 'game', 'team', 'match', 'winner', 'run', 'walk', 'swim', 'jump', 'sick', 'strong', 'weak']):
        return 'health'
    elif any(x in w for x in ['music', 'song', 'movie', 'film', 'theater', 'actor', 'artist', 'painting', 'drawing', 'photo', 'camera', 'dance', 'sing', 'art']):
        return 'arts'
    elif any(x in w for x in ['internet', 'email', 'message', 'news', 'newspaper', 'magazine', 'article', 'reporter', 'writer', 'poet', 'story', 'novel', 'poem', 'tech', 'web', 'browser', 'code', 'software', 'hardware', 'database', 'server', 'client', 'network']):
        return 'tech'
    elif any(x in w for x in ['language', 'word', 'sentence', 'grammar', 'conversation', 'dialogue', 'group', 'meeting', 'party', 'event', 'festival', 'celebration', 'gift', 'present', 'card', 'letter', 'talk', 'speak', 'write', 'say', 'tell', 'ask', 'answer']):
        return 'communication'
    elif any(x in w for x in ['ability', 'advantage', 'analysis', 'standard', 'target', 'quality', 'focus', 'process', 'project', 'feedback', 'concept', 'context', 'structure', 'function', 'source', 'resource', 'schedule', 'calendar', 'deadline', 'result', 'score', 'percent', 'average', 'total', 'summary', 'report', 'document', 'file', 'folder', 'record', 'upload', 'download', 'password', 'account', 'notification', 'alert', 'warning', 'status', 'progress', 'interval', 'factor', 'ease', 'logic', 'design', 'framework', 'backend', 'frontend', 'conclusion', 'evidence', 'innovation', 'strategy', 'efficiency', 'collaboration', 'productivity', 'professional', 'assess', 'evaluate', 'coordinate', 'implement', 'optimize', 'negotiate', 'manage', 'organize']):
        return 'professional'
    else:
        if word_type == 'verb':
            return 'verbs'
        elif word_type in ('adjective', 'adverb'):
            return 'adjectives'
        else:
            h = sum(ord(c) for c in w)
            return topics[h % len(topics)]

# ---------------------------------------------------------------------------
# Command Implementation
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Seed database with 3000 unique vocabularies and 84 detailed skills lessons."

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing database contents...")
        self._clear_data()

        with transaction.atomic():
            self.stdout.write("Creating Category nodes...")
            categories = self._create_categories()

            self.stdout.write("Generating and seeding 3000 vocabulary words...")
            self._seed_vocabulary(categories)

            self.stdout.write("Seeding 45 vocabulary questions...")
            self._seed_vocabulary_questions()

            self.stdout.write("Seeding 84 detailed skills lessons & questions...")
            self._seed_skills()

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))

    def _clear_data(self):
        Flashcard.objects.all().delete()
        Vocabulary.objects.all().delete()
        Category.objects.all().delete()
        ReadingQuestion.objects.all().delete()
        ReadingPassage.objects.all().delete()
        ListeningQuestion.objects.all().delete()
        ListeningTrack.objects.all().delete()
        WritingTask.objects.all().delete()
        SpeakingPrompt.objects.all().delete()
        VocabularyQuestion.objects.all().delete()

    def _create_categories(self):
        cats = {}
        for level in ["A1", "A2", "B1"]:
            name = f"Tiếng Anh {level}"
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={"description": f"Chủ đề từ vựng và bài học cấp độ {level}.", "level": level}
            )
            cats[level] = cat
        return cats

    def _seed_vocabulary(self, categories):
        levels_roots = {
            "A1": ROOTS_A1,
            "A2": ROOTS_A2,
            "B1": ROOTS_B1
        }
        
        global_seen = set()
        
        for level, roots in levels_roots.items():
            cat = categories[level]
            level_words = []
            seen_in_level = set()
            
            # 1. Add base roots first
            for word_type in ['verb', 'noun', 'adjective']:
                for base_word, meaning, base_ipa in roots[word_type]:
                    w_lower = base_word.lower()
                    if w_lower not in global_seen:
                        global_seen.add(w_lower)
                        seen_in_level.add(w_lower)
                        level_words.append(Vocabulary(
                            word=w_lower,
                            ipa=f"/{base_ipa}/",
                            meaning=meaning,
                            word_type=word_type,
                            example=generate_sentence(w_lower, word_type, '', level),
                            level=level,
                            category=cat,
                            topic=classify_topic(w_lower, word_type)
                        ))

            # 2. Add morphology derivatives
            for word_type in ['verb', 'noun', 'adjective']:
                suffixes = SUFFIX_MAPS[word_type]
                for base_word, meaning, base_ipa in roots[word_type]:
                    if len(level_words) >= 1000:
                        break
                        
                    for s in suffixes:
                        if len(level_words) >= 1000:
                            break
                            
                        # Spelling
                        w = add_suffix(base_word, s)
                        w_lower = w.lower()
                        
                        if w_lower not in global_seen and w_lower not in seen_in_level:
                            global_seen.add(w_lower)
                            seen_in_level.add(w_lower)
                            
                            # Meaning prefix/suffix
                            m = meaning
                            if word_type == 'verb':
                                if s == 'er': m = f"người {meaning}"
                                elif s == 'ing': m = f"việc {meaning}"
                                elif s == 'ed': m = f"đã {meaning}"
                                elif s == 'able': m = f"có thể {meaning}"
                            elif word_type == 'noun':
                                if s == 's_noun': m = f"những {meaning}"
                                elif s == 'less': m = f"không có {meaning}"
                            elif word_type == 'adjective':
                                if s == 'ly': m = f"một cách {meaning}"
                                elif s == 'ness': m = f"sự {meaning}"
                                
                            # Target type
                            target_type = word_type
                            if s in ('er', 'ing', 'ness', 's_noun'): target_type = 'noun'
                            elif s in ('able', 'less'): target_type = 'adjective'
                            elif s == 'ly': target_type = 'adverb'
                            
                            level_words.append(Vocabulary(
                                word=w_lower,
                                ipa=generate_ipa(base_ipa, s),
                                meaning=m,
                                word_type=target_type,
                                example=generate_sentence(w_lower, word_type, s, level),
                                level=level,
                                category=cat,
                                topic=classify_topic(w_lower, target_type)
                            ))

            # Use extra real words for fallback instead of dummy vocab_a2_14 strings
            extra_fallback_words = [
                ("apple", "quả táo", "æpl"), ("orange", "quả cam", "ɔːrɪndʒ"), ("grape", "quả nho", "ɡreɪp"),
                ("ocean", "đại dương", "oʊʃn"), ("river", "dòng sông", "rɪvər"), ("mountain", "ngọn núi", "maʊntn"),
                ("village", "ngôi làng", "vɪlɪdʒ"), ("city", "thành phố", "sɪti"), ("town", "thị trấn", "taʊn"),
                ("planet", "hành tinh", "plænɪt"), ("space", "không gian", "speɪs"), ("star", "ngôi sao", "stɑːr"),
                ("guitar", "đàn ghi-ta", "ɡɪtɑːr"), ("piano", "đàn piano", "piænoʊ"), ("violin", "đàn vĩ cầm", "vaɪəlɪn"),
                ("train", "tàu hỏa", "treɪn"), ("plane", "máy bay", "pleɪn"), ("bicycle", "xe đạp", "baɪsɪkl"),
                ("coffee", "cà phê", "kɔːfi"), ("sugar", "đường", "ʃʊɡər"), ("salt", "muối", "sɔːlt"),
                ("butter", "bơ", "bʌtər"), ("cheese", "pho mát", "tʃiːz"), ("chicken", "gà", "tʃɪkɪn"),
                ("wallet", "ví", "wɑːlɪt"), ("ticket", "vé", "tɪkɪt"), ("money", "tiền", "mʌni"),
                ("friend", "bạn bè", "frɛnd"), ("enemy", "kẻ thù", "ɛnəmi"), ("partner", "đối tác", "pɑːrtnər"),
                ("morning", "buổi sáng", "mɔːrnɪŋ"), ("afternoon", "buổi chiều", "æftərnuːn"), ("evening", "buổi tối", "iːvnɪŋ"),
                ("summer", "mùa hè", "sʌmər"), ("winter", "mùa đông", "wɪntər"), ("autumn", "mùa thu", "ɔːtəm"),
                ("doctor", "bác sĩ", "dɑːktər"), ("nurse", "y tá", "nɜːrs"), ("dentist", "nha sĩ", "dɛntɪst"),
                ("color", "màu sắc", "kʌlər"), ("shape", "hình dạng", "ʃeɪp"), ("size", "kích thước", "saɪz"),
                ("happy", "vui vẻ", "hæpi"), ("sad", "buồn bã", "sæd"), ("angry", "tức giận", "æŋɡri"),
                ("fast", "nhanh", "fæst"), ("slow", "chậm", "sloʊ"), ("quick", "nhanh nhẹn", "kwɪk"),
                ("smart", "thông minh", "smɑːrt"), ("clever", "khôn ngoan", "klɛvər"), ("bright", "sáng sủa", "braɪt")
            ]
            
            for word, meaning, ipa in extra_fallback_words:
                if len(level_words) >= 1000:
                    break
                w_lower = word.lower()
                if w_lower not in global_seen:
                    global_seen.add(w_lower)
                    level_words.append(Vocabulary(
                        word=w_lower,
                        ipa=f"/{ipa}/",
                        meaning=meaning,
                        word_type="other",
                        example=f"This is an example for {w_lower}.",
                        level=level,
                        category=cat,
                        topic=classify_topic(w_lower, "other")
                    ))

            Vocabulary.objects.bulk_create(level_words[:1000])
            self.stdout.write(f"   - Seeded {len(level_words[:1000])} unique real words for {level}")

        # Create Flashcards for all vocabulary objects
        vocabs = Vocabulary.objects.all()
        flashcards = [Flashcard(vocabulary=v, is_mastered=False) for v in vocabs]
        Flashcard.objects.bulk_create(flashcards)
        self.stdout.write(f"   - Created {len(flashcards)} flashcards")

    def _seed_vocabulary_questions(self):
        q_objs = []
        for level in ["A1", "A2", "B1"]:
            for q_text, opts, ans in VOCAB_QUESTIONS[level]:
                q_objs.append(VocabularyQuestion(
                    question_text=q_text,
                    options=opts,
                    correct_answer=ans,
                    level=level
                ))
        VocabularyQuestion.objects.bulk_create(q_objs)
        self.stdout.write(f"   - Seeded {len(q_objs)} vocabulary questions")

    def _seed_skills(self):
        # 1. Reading
        rp_count, rq_count = 0, 0
        for level in ["A1", "A2", "B1"]:
            for title, text, questions in SKILLS_DATA["reading"][level]:
                rp = ReadingPassage.objects.create(
                    title=f"{title} ({level})",
                    text_content=text,
                    level=level
                )
                rp_count += 1
                for q_text, opts, ans in questions:
                    ReadingQuestion.objects.create(
                        passage=rp,
                        question_text=q_text,
                        options=opts,
                        correct_answer=ans,
                        level=level
                    )
                    rq_count += 1
        self.stdout.write(f"   - Seeded {rp_count} Reading passages and {rq_count} Reading questions")

        # 2. Listening
        lt_count, lq_count = 0, 0
        for level in ["A1", "A2", "B1"]:
            for title, transcript, questions in SKILLS_DATA["listening"][level]:
                lt = ListeningTrack.objects.create(
                    title=f"{title} ({level})",
                    audio_file="",
                    transcript=transcript,
                    level=level
                )
                lt_count += 1
                for q_text, opts, ans in questions:
                    ListeningQuestion.objects.create(
                        track=lt,
                        question_text=q_text,
                        options=opts,
                        correct_answer=ans,
                        level=level
                    )
                    lq_count += 1
        self.stdout.write(f"   - Seeded {lt_count} Listening tracks and {lq_count} Listening questions")

        # 3. Writing
        wt_count = 0
        for level in ["A1", "A2", "B1"]:
            for title, prompt in WRITING_PROMPTS[level]:
                WritingTask.objects.create(
                    title=f"{title} ({level})",
                    prompt_text=prompt,
                    level=level
                )
                wt_count += 1
        self.stdout.write(f"   - Seeded {wt_count} Writing tasks")

        # 4. Speaking
        st_count = 0
        for level in ["A1", "A2", "B1"]:
            for title, prompt in SPEAKING_PROMPTS[level]:
                SpeakingPrompt.objects.create(
                    title=f"{title} ({level})",
                    prompt_text=prompt,
                    level=level
                )
                st_count += 1
        self.stdout.write(f"   - Seeded {st_count} Speaking prompts")
