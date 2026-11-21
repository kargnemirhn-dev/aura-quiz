import json
import logging
from typing import List, Dict, Optional, Any
from aura.config import settings
from aura.models import Question, QuestionOption

logger = logging.getLogger("aura.gemini")

# Curated High-Quality Fallback Question Bank (30 Summit-themed questions in Turkish)
FALLBACK_QUESTIONS: List[Dict] = [
    {
        "id": 1,
        "question": "Yapay zekanın modern dil modellerine (LLM) temel oluşturan ve 2017'de yayınlanan ünlü makalenin başlığı nedir?",
        "options": {
            "A": "Deep Residual Learning",
            "B": "Attention Is All You Need",
            "C": "Convolutional Networks for Vision",
            "D": "Generative Adversarial Nets"
        },
        "correct": "B",
        "explanation": "Google araştırmacılarının 2017'de yayınladığı 'Attention Is All You Need' makalesi Transformer mimarisini tanıttı.",
        "duration": 15
    },
    {
        "id": 2,
        "question": "Değerlemesi 1 Milyar Doları aşan özel girişimlere girişimcilik dünyasında ne ad verilir?",
        "options": {
            "A": "Decacorn",
            "B": "Centaur",
            "C": "Unicorn",
            "D": "Zebra"
        },
        "correct": "C",
        "explanation": "Unicorn terimi 2013'te Aileen Lee tarafından 1 milyar dolar değerlemeye ulaşan startuplar için kullanılmıştır.",
        "duration": 15
    },
    {
        "id": 3,
        "question": "Türkiye'nin ilk 'Decacorn'u (10 milyar dolar üzeri değerleme) unvanını kazanan teknoloji girişimi hangisidir?",
        "options": {
            "A": "Peak Games",
            "B": "Getir",
            "C": "Trendyol",
            "D": "Dream Games"
        },
        "correct": "C",
        "explanation": "Trendyol, 2021 yılında aldığı yatırım ile 16.5 milyar dolar değerlemeye ulaşarak Türkiye'nin ilk Decacorn'u olmuştur.",
        "duration": 15
    },
    {
        "id": 4,
        "question": "Büyük Dil Modellerinde (LLM) modelin gerçekte olmayan bilgileri gerçekmiş gibi kendinden emin şekilde üretmesine ne ad verilir?",
        "options": {
            "A": "Overfitting",
            "B": "Halüsinasyon (Hallucination)",
            "C": "Underfitting",
            "D": "Quantization"
        },
        "correct": "B",
        "explanation": "Yapay zekanın uydurma verileri olguymuş gibi sunmasına 'hallucination' (halüsinasyon) denir.",
        "duration": 15
    },
    {
        "id": 5,
        "question": "Yapay zeka modellerinin eğitiminde paralel hesaplama gücüyle devrim yaratan çip devinin adı nedir?",
        "options": {
            "A": "Intel",
            "B": "Qualcomm",
            "C": "Nvidia",
            "D": "Broadcom"
        },
        "correct": "C",
        "explanation": "Nvidia'nın geliştirdiği GPU'lar ve CUDA mimarisi derin öğrenme patlamasının temel itici gücü olmuştur.",
        "duration": 15
    },
    {
        "id": 6,
        "question": "Bir girişimin dış yatırım almadan, sadece kurucuların kendi kaynakları ve şirketin nakit akışıyla büyümesine ne denir?",
        "options": {
            "A": "Bootstrapping",
            "B": "Angel Round",
            "C": "Series A",
            "D": "Crowdfunding"
        },
        "correct": "A",
        "explanation": "Bootstrapping, bir girişimin sıfır veya minimum dış sermayeyle öz kaynaklarını kullanarak büyümesidir.",
        "duration": 15
    },
    {
        "id": 7,
        "question": "Girişimcilikte müşterilerin en temel ihtiyacını çözen en yalın ilk ürün versiyonuna ne ad verilir?",
        "options": {
            "A": "Proof of Concept (PoC)",
            "B": "Minimum Viable Product (MVP)",
            "C": "Final Candidate",
            "D": "Alpha Release"
        },
        "correct": "B",
        "explanation": "MVP (Minimum Viable Product), pazardan en hızlı geri bildirimi almak için geliştirilen temel sürümdür.",
        "duration": 15
    },
    {
        "id": 8,
        "question": "Hangisi bir 'Multimodal' (Çok modlu) yapay zeka modelinin temel yeteneğidir?",
        "options": {
            "A": "Sadece düz metin çevirisi yapabilmesi",
            "B": "Aynı anda metin, görsel, ses ve video işleyebilmesi",
            "C": "Yalnızca ilişkisel SQL verilerini sorgulayabilmesi",
            "D": "Sadece donanım hız aşırtması yapabilmesi"
        },
        "correct": "B",
        "explanation": "Multimodal modeller (Gemini vb.), metin, görsel, ses ve kod gibi farklı veri biçimlerini bir arada anlayabilir.",
        "duration": 15
    },
    {
        "id": 9,
        "question": "Bir makinenin insan düzeyinde düşünebildiğini kanıtlamak amacıyla 1950 yılında önerilen meşhur test nedir?",
        "options": {
            "A": "Voight-Kampff Testi",
            "B": "Turing Testi",
            "C": "Shannon Entropi Testi",
            "D": "Lovelace Kriteri"
        },
        "correct": "B",
        "explanation": "Alan Turing'in 'Computing Machinery and Intelligence' makalesinde önerdiği taklit oyunu Turing Testi olarak bilinir.",
        "duration": 15
    },
    {
        "id": 10,
        "question": "Girişimcilikte yatırımcılara projenin 3-5 dakikada özetlendiği slayt sunumuna ne ad verilir?",
        "options": {
            "A": "Term Sheet",
            "B": "Pitch Deck",
            "C": "Cap Table",
            "D": "Due Diligence"
        },
        "correct": "B",
        "explanation": "Pitch Deck, yatırımcılara girişimin vizyonunu, pazarını ve finansal projeksiyonlarını aktaran sunumdur.",
        "duration": 15
    },
    {
        "id": 11,
        "question": "RAG (Retrieval-Augmented Generation) mimarisinin yapay zekadaki temel amacı nedir?",
        "options": {
            "A": "Modeli harici ve güncel bir bilgi tabanıyla desteklemek",
            "B": "Modelin parametre sayısını sıfırlamak",
            "C": "Yapay zekanın internete erişimini engellemek",
            "D": "Ekran kartının bellek sıcaklığını düşürmek"
        },
        "correct": "A",
        "explanation": "RAG, dil modelini kurum içi veya güncel dokümanlarla zenginleştirerek halüsinasyonu engeller.",
        "duration": 15
    },
    {
        "id": 12,
        "question": "Bir girişimin şirketi satması veya halka arz (IPO) yoluyla yatırımcılarına getiri sağlamasına ne ad verilir?",
        "options": {
            "A": "Pivot",
            "B": "Exit (Çıkış)",
            "C": "Burn Rate",
            "D": "Valuation"
        },
        "correct": "B",
        "explanation": "Exit, kurucuların ve yatırımcıların hisselerini nakde dönüştürdüğü başarılı satış sürecidir.",
        "duration": 15
    },
    {
        "id": 13,
        "question": "Türkiye'nin ilk Unicorn'u olan ve Zynga tarafından 1.8 milyar dolara satın alınan mobil oyun şirketi hangisidir?",
        "options": {
            "A": "Peak Games",
            "B": "Gram Games",
            "C": "Rollic Games",
            "D": "Mynet"
        },
        "correct": "A",
        "explanation": "Peak Games, Haziran 2020'de Zynga'ya satılarak Türkiye'nin ilk Unicorn şirketi olmuştur.",
        "duration": 15
    },
    {
        "id": 14,
        "question": "Yapay zeka modellerine istenen çıktıyı en doğru şekilde ürettirmek için talimat tasarlama disiplinine ne denir?",
        "options": {
            "A": "Reverse Engineering",
            "B": "Prompt Engineering",
            "C": "Packet Sniffing",
            "D": "Scrum Master"
        },
        "correct": "B",
        "explanation": "Prompt Engineering (İstem Mühendisliği), yapay zekaya doğru bağlam ve talimatı verme sanatıdır.",
        "duration": 15
    },
    {
        "id": 15,
        "question": "Bir girişimin mevcut iş modeli çalışmadığında rotasını ve stratejisini kökten değiştirmesine ne ad verilir?",
        "options": {
            "A": "Pivot",
            "B": "Sprint",
            "C": "Dilution",
            "D": "Liquidation"
        },
        "correct": "A",
        "explanation": "Pivot, girişimin edindiği pazar dersleriyle yönünü yeni bir iş modeline çevirmesidir.",
        "duration": 15
    },
    {
        "id": 16,
        "question": "OpenAI tarafından geliştirilen ve video üretiminde çığır açan difüzyon tabanlı modelin adı nedir?",
        "options": {
            "A": "Sora",
            "B": "DALL-E",
            "C": "Whisper",
            "D": "Codex"
        },
        "correct": "A",
        "explanation": "Sora, OpenAI tarafından geliştirilen gerçekçi ve yüksek çözünürlüklü video üretim modelidir.",
        "duration": 15
    },
    {
        "id": 17,
        "question": "Yapay zeka modellerinde 'Fine-Tuning' terimi neyi ifade eder?",
        "options": {
            "A": "Önceden eğitilmiş bir modeli belirli bir uzmanlık alanı için yeniden eğitmek",
            "B": "Donanım fanlarını temizlemek",
            "C": "Veritabanını optimize etmek",
            "D": "Tüm yapay zeka kodunu silip sıfırdan yazmak"
        },
        "correct": "A",
        "explanation": "Fine-Tuning, genel bir temel modelin belirli veri kümeleriyle uzmanlaştırılmasıdır.",
        "duration": 15
    },
    {
        "id": 18,
        "question": "Bir girişimin kasasındaki nakdin her ay ne kadar azaldığını gösteren finansal metriğe ne denir?",
        "options": {
            "A": "Churn Rate",
            "B": "Burn Rate (Nakit Yakma Oranı)",
            "C": "CAC (Customer Acquisition Cost)",
            "D": "EBITDA"
        },
        "correct": "B",
        "explanation": "Burn Rate, girişimin karlı hale gelene kadar aylık harcadığı net nakit miktarıdır.",
        "duration": 15
    },
    {
        "id": 19,
        "question": "Google DeepMind'ın proteinlerin üç boyutlu yapılarını tahmin ederek biyolojide devrim yaratan yapay zekası nedir?",
        "options": {
            "A": "AlphaGo",
            "B": "AlphaFold",
            "C": "AlphaZero",
            "D": "MuZero"
        },
        "correct": "B",
        "explanation": "AlphaFold, 200 milyondan fazla protein yapısını çözerek 2024 Nobel Kimya Ödülü'ne de zemin hazırlamıştır.",
        "duration": 15
    },
    {
        "id": 20,
        "question": "Erken aşama girişimlere ilk sermayeyi, ofisi ve mentorluk desteğini sağlayan hızlandırıcı programlara dünyaca ünlü bir örnek hangisidir?",
        "options": {
            "A": "Y Combinator",
            "B": "Standard & Poor's",
            "C": "Moody's",
            "D": "NASDAQ"
        },
        "correct": "A",
        "explanation": "Y Combinator (YC), Airbnb, Stripe ve Dropbox gibi devleri mezun eden dünyanın en prestijli hızlandırıcısıdır.",
        "duration": 15
    },
    {
        "id": 21,
        "question": "Yapay zeka modellerinin insan değerleri ve güvenliğiyle uyumlu hale getirilmesi sürecine ne ad verilir?",
        "options": {
            "A": "AI Alignment (Hizalama)",
            "B": "Load Balancing",
            "C": "Tokenization",
            "D": "Clustering"
        },
        "correct": "A",
        "explanation": "AI Alignment, yapay zekanın insanlığın etik değerlerine, niyetine ve güvenliğine sadık kalmasını sağlar.",
        "duration": 15
    },
    {
        "id": 22,
        "question": "SaaS (Software as a Service) girişimlerinde bir müşteriyi kazanmak için harcanan toplam maliyet metriği hangisidir?",
        "options": {
            "A": "LTV (Lifetime Value)",
            "B": "CAC (Customer Acquisition Cost)",
            "C": "MRR (Monthly Recurring Revenue)",
            "D": "NPS (Net Promoter Score)"
        },
        "correct": "B",
        "explanation": "CAC (Müşteri Kazanım Maliyeti), pazarlama ve satış giderlerinin kazanılan müşteri sayısına oranıdır.",
        "duration": 15
    },
    {
        "id": 23,
        "question": "Doğal Dil İşleme (NLP) modellerinde metnin en küçük anlamlı veya sayısal parçalara bölünmesine ne ad verilir?",
        "options": {
            "A": "Tokenization (Jetonlama)",
            "B": "Normalization",
            "C": "Compiling",
            "D": "Indexing"
        },
        "correct": "A",
        "explanation": "Tokenization, metinlerin dil modelleri tarafından işlenebilmesi için token'lara dönüştürülmesidir.",
        "duration": 15
    },
    {
        "id": 24,
        "question": "Bir girişimin kurucuları ve çalışanları arasında hisse oranlarını gösteren tabloya ne ad verilir?",
        "options": {
            "A": "Balance Sheet",
            "B": "Cap Table (Sermaye Tablosu)",
            "C": "Kanban Board",
            "D": "Gantt Chart"
        },
        "correct": "B",
        "explanation": "Cap Table (Capitalization Table), ortaklık yüzdelerini ve hisse dağılımlarını gösterir.",
        "duration": 15
    },
    {
        "id": 25,
        "question": "Otonom olarak karar verip belirli hedeflere ulaşmak için araçları (browser, API, kod) kullanan yapay zeka sistemlerine ne denir?",
        "options": {
            "A": "AI Agents (Yapay Zeka Ajanları)",
            "B": "Static Scrapers",
            "C": "Regex Parsers",
            "D": "Batch Cron Jobs"
        },
        "correct": "A",
        "explanation": "AI Ajanları (Agentic AI), çevrelerini algılayıp bağımsız aksiyon alabilen yeni nesil sistemlerdir.",
        "duration": 15
    },
    {
        "id": 26,
        "question": "Bir girişimin ürününün pazarda gerçek ve sürdürülebilir bir talep bulduğu ana ne ad verilir?",
        "options": {
            "A": "Product-Market Fit (Ürün-Pazar Uyumu)",
            "B": "Seed Round",
            "C": "Honeymoon Phase",
            "D": "Incubation"
        },
        "correct": "A",
        "explanation": "Product-Market Fit (PMF), girişimin doğru ürünü doğru kitleye başarıyla ulaştırdığı kritik eşiktir.",
        "duration": 15
    },
    {
        "id": 27,
        "question": "RLHF (Reinforcement Learning from Human Feedback) tekniği modellerin geliştirilmesinde ne sağlar?",
        "options": {
            "A": "İnsan geri bildirimleriyle modelin daha yardımsever ve güvenli yanıtlar vermesini sağlamak",
            "B": "Sadece matematiksel işlem hızını artırmak",
            "C": "Ekran kartının güç tüketimini azaltmak",
            "D": "Modeli tamamen ücretsiz yapmak"
        },
        "correct": "A",
        "explanation": "RLHF, insan değerlendirmelerini ödül mekanizması olarak kullanarak LLM yanıtlarını optimize eder.",
        "duration": 15
    },
    {
        "id": 28,
        "question": "Girişim sermayesi (Venture Capital - VC) fonlarının ana gelir kaynağı olan kardan alınan yüzdeye ne ad verilir?",
        "options": {
            "A": "Management Fee",
            "B": "Carried Interest (Carry)",
            "C": "Dividend",
            "D": "Royalty"
        },
        "correct": "B",
        "explanation": "Carried Interest (genellikle %20), fon yöneticilerinin sağladığı yatırım karından aldığı paydır.",
        "duration": 15
    },
    {
        "id": 29,
        "question": "Yapay zeka dünyasında açık kaynak ağırlıklı modelleriyle bilinen ve 'Llama' serisini geliştiren şirket hangisidir?",
        "options": {
            "A": "Apple",
            "B": "Meta",
            "C": "Amazon",
            "D": "Netflix"
        },
        "correct": "B",
        "explanation": "Meta (eski adıyla Facebook), Llama 1, 2 ve 3 serisiyle açık kaynak yapay zeka topluluğuna öncülük etmektedir.",
        "duration": 15
    },
    {
        "id": 30,
        "question": "Bir girişimin 'Ağ Etkisi' (Network Effects) kazanması ne anlama gelir?",
        "options": {
            "A": "Her yeni kullanıcının sistemin tüm kullanıcılar için değerini katlayarak artırması",
            "B": "Sunucu kablolarının fiber optik olması",
            "C": "Girişimin sadece yerel ağda çalışabilmesi",
            "D": "Şirketin tüm bilgisayarlarının aynı WiFi'a bağlı olması"
        },
        "correct": "A",
        "explanation": "Ağ Etkisi, platforma katılan her yeni üyenin platformun toplam değerini artırmasıdır (Örn: Uber, LinkedIn).",
        "duration": 15
    }
]

class GeminiQuestionService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL

    def get_default_questions(self, folder_id: str = "default", difficulties_seq: Optional[List[str]] = None) -> List[Question]:
        """Returns the curated default 30 summit questions with difficulties tagged"""
        default_diffs = ["Kolay", "Orta", "Zor", "Çok Kolay"]
        questions = []
        for idx, q in enumerate(FALLBACK_QUESTIONS):
            if difficulties_seq and idx < len(difficulties_seq):
                diff = difficulties_seq[idx]
            else:
                diff = default_diffs[(q["id"] - 1) % len(default_diffs)]
            questions.append(
                Question(
                    id=q["id"],
                    question=q["question"],
                    options=QuestionOption(**q["options"]),
                    correct=q["correct"],
                    explanation=q.get("explanation", ""),
                    duration=q.get("duration", 15),
                    difficulty=diff,
                    folder_id=folder_id
                )
            )
        return questions

    async def generate_questions_with_gemini(
        self,
        count: int = 30,
        difficulties: Optional[Dict[str, int]] = None,
        folder_id: str = "default"
    ) -> List[Question]:
        """
        Uses Gemini API (google-genai SDK or direct REST) to generate count fresh,
        authentic, summit-themed questions in Turkish with optional difficulty distribution.
        Max 50 questions per single generation request.
        """
        # Enforce maximum 50 questions per single request (Requirement 9)
        count = min(50, max(1, count))

        # Build target difficulty sequence if specified
        target_diff_sequence: List[str] = []
        if difficulties:
            ck = int(difficulties.get("cok_kolay", 0))
            k = int(difficulties.get("kolay", 0))
            o = int(difficulties.get("orta", 0))
            z = int(difficulties.get("zor", 0))
            sum_diffs = ck + k + o + z
            if sum_diffs > 0:
                count = min(50, sum_diffs)
                target_diff_sequence = (["Çok Kolay"] * ck) + (["Kolay"] * k) + (["Orta"] * o) + (["Zor"] * z)

        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. Returning curated fallback questions.")
            return self.get_default_questions(folder_id, target_diff_sequence)[:count]

        diff_instructions = ""
        if difficulties and target_diff_sequence:
            ck = difficulties.get("cok_kolay", 0)
            k = difficulties.get("kolay", 0)
            o = difficulties.get("orta", 0)
            z = difficulties.get("zor", 0)
            diff_instructions = f"""
            ZORUNLU ZORLUK SEVİYESİ DAĞILIMI (BU ADETLERE KESİNLİKLE UYULMALIDIR):
            - 'Çok Kolay': TAM {ck} adet soru
            - 'Kolay': TAM {k} adet soru
            - 'Orta': TAM {o} adet soru
            - 'Zor': TAM {z} adet soru
            Her soru objesindeki "difficulty" alanını tam olarak bu etiketlerle ("Çok Kolay", "Kolay", "Orta", "Zor") belirt.
            Örnek: Eğer 30 Çok Kolay istendiyse, 30 sorunun tamamının difficulty değeri "Çok Kolay" olmalı ve sorular temel seviyede olmalıdır.
            """

        prompt = f"""
        Sen "AI ERA: TEKNOLOJİ & GİRİŞİMCİLİK ZİRVESİ" (Aura Bilgi Yarışması) için profesyonel bir soru hazırlama uzmanısın.
        Lütfen etkinliğin sahnesinde katılımcılara Kahoot tarzında sorulmak üzere TAM {count} ADET taze, özgün, merak uyandıran, Türkçe çoktan seçmeli yarışma sorusu üret.

        {diff_instructions}

        Soruların dağılımı şu dengede olmalıdır:
        1. Yapay Zeka, Derin Öğrenme, LLM'ler, Üretken Yapay Zeka (GenAI), Ajanlar (Agentic AI), GPU ve donanım teknolojileri.
        2. Küresel ve Türkiye Girişimcilik Ekosistemi: Unicornlar, Decacornlar, Yatırım Aşamaları (Seed, Series A), Pitch Deck, MVP, Pivot, Bootstrapping, Y Combinator vb.
        3. Teknoloji Tarihi & Öncü İnovasyonlar (Turing, DeepMind, OpenAI, Nvidia, Meta Llama vb.).

        ÖNEMLİ KURALLAR:
        - Her sorunun TAM 4 şıkkı olmalıdır (A, B, C, D).
        - Doğru şıklar A, B, C, D arasında dengeli dağılmalıdır.
        - Yanıt kesinlikle SADECE ve SADECE saf JSON formatında bir liste (array) olmalıdır. Markdown kod bloğu ```json veya açıklama ekleme!

        İstenen JSON şeması:
        [
          {{
            "id": 1,
            "question": "Soru metni buraya",
            "options": {{
              "A": "Şık A metni",
              "B": "Şık B metni",
              "C": "Şık C metni",
              "D": "Şık D metni"
            }},
            "correct": "C",
            "explanation": "Kısa ve eğitici açıklama",
            "duration": 15,
            "difficulty": "Orta"
          }},
          ...
        ]
        """

        try:
            # Try official google.genai SDK
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            raw_text = response.text.strip()
            
            # Clean markdown codeblocks if model included them
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed_list = json.loads(raw_text)
            questions: List[Question] = []
            for idx, item in enumerate(parsed_list, start=1):
                diff_val = item.get("difficulty", "Orta")
                if target_diff_sequence and (idx - 1) < len(target_diff_sequence):
                    diff_val = target_diff_sequence[idx - 1]
                q = Question(
                    id=idx,
                    question=item["question"],
                    options=QuestionOption(**item["options"]),
                    correct=item["correct"],
                    explanation=item.get("explanation", ""),
                    duration=item.get("duration", 15),
                    difficulty=diff_val,
                    folder_id=folder_id
                )
                questions.append(q)

            if len(questions) >= 5:
                logger.info(f"Successfully generated {len(questions)} questions using Gemini API!")
                res_questions = questions[:count]
                if target_diff_sequence:
                    for i, q in enumerate(res_questions):
                        if i < len(target_diff_sequence):
                            q.difficulty = target_diff_sequence[i]
                return res_questions
            else:
                logger.warning("Gemini returned fewer questions than expected. Falling back to curated bank.")
                return self.get_default_questions(folder_id, target_diff_sequence)[:count]

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}. Utilizing fallback questions.")
            return self.get_default_questions(folder_id, target_diff_sequence)[:count]
            logger.error(f"Error calling Gemini API: {e}. Utilizing fallback questions.")
            return self.get_default_questions(folder_id)[:count]

gemini_service = GeminiQuestionService()
