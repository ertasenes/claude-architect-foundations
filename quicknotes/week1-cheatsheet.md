# 📌 Week 1 El Notu — Claude API & Agentic Loop

## 1. API Temelleri
- Messages API: `client.messages.create(model=..., max_tokens=..., system=..., tools=..., messages=[...])`
- `messages` listesinde iki rol dönüşümlü ilerler: `user` ve `assistant`. **System prompt bir mesaj değildir** — ayrı `system` parametresidir.
- `max_tokens` **zorunludur**; cevabın üst sınırını belirler.
- Cevap (`response.content`) bir **blok listesidir**: `text` ve `tool_use` blokları aynı cevapta yan yana olabilir. Asla "cevap = tek metin" varsayma.
- **stop_reason değerleri:** `end_turn` (model bitirdi), `tool_use` (tool çalıştırılması bekleniyor), `max_tokens` (limite takıldı — cevap yarım!), `stop_sequence`. Sınavın kalbi ilk ikisi.

## 2. Tool Tanımı
- Üç parça: `name`, `description`, `input_schema` (JSON Schema: `type`, `properties`, `required`).
- **Description = modelin tool seçme pusulası.** Model tool'u koda bakarak değil, description okuyarak seçer.
- **Model tool'u ÇALIŞTIRMAZ.** Model sadece yapılandırılmış bir istek yazar — "fiş" (ticket). Fişi mutfağa götürüp yemeği pişiren (kodu çalıştıran) SENSİN. Sınavda "Claude executes the tool" içeren her şık otomatik yanlıştır.

## 3. tool_use Round Trip (fişin gidiş-dönüşü)
- `stop_reason == "tool_use"` → cevapta `ToolUseBlock(id, name, input)` var.
- Sonucu geri gönderme formatı:

~~~python
{"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "<fisin_idsi>", "content": sonuc}
]}
~~~

- ⚠️ **EN BÜYÜK SINAV TUZAĞI: tool_result `user` rolüyle gider.** `assistant` değil, `tool` diye bir rol de yok.
- `tool_use_id` eşleşmesi zorunlu: hangi cevabın hangi fişe ait olduğunu bu numara söyler.
- Konuşma zinciri her turda büyür: `assistant(tool_use)` → `user(tool_result)` → API tekrar çağrılır. Tool sonuçları history'ye eklenir ki model sonraki kararını yeni bilgiyle versin.

## 4. Agentic Loop — Doğru Tasarım
- İskelet:

~~~text
döngü:
  cevap = API çağrısı
  history'ye assistant mesajını ekle
  if stop_reason == "end_turn": ÇIK (koşulsuz!)
  tüm tool_use bloklarını çalıştır
  tüm sonuçları TEK user mesajında history'ye ekle
~~~

- **Çıkış SADECE stop_reason'a bağlanır.** Canlı bug'ımız: döngü yalnızca "text bloğu varsa" çıkıyordu → metinsiz bir end_turn cevabında **sessiz sonsuz döngü**. Ders: exit'i içeriğe değil sinyale bağla.
- **Anti-pattern üçlüsü** (sınav bunları şık olarak önüne koyar):
  1. Doğal dil sinyali parse etmek ("task complete" geçiyor mu?)
  2. Keyfi iterasyon limitini **birincil** durdurma mekanizması yapmak (emniyet kemeri olarak `range(N)` OK, ana mantık olarak ASLA)
  3. "Cevapta text bloğu var mı"yı bitiş göstergesi saymak
- Model-driven karar: hangi tool'un ne zaman çağrılacağına **model** karar verir; önceden kodlanmış karar ağacı / sabit tool sırası agentic yaklaşımın zıttıdır.

## 5. Parallel Tool Calls
- **Tek assistant cevabı birden fazla tool_use bloğu içerebilir** ("ORD-1001 ve ORD-1002'yi kontrol et" → iki fiş birden).
- Doğru işlem: **hepsini çalıştır, TÜM sonuçları TEK bir user mesajında** döndür — her biri kendi `tool_use_id`'siyle.
- Yanlışlar: sadece ilkini çalıştırmak; her sonucu ayrı mesajla göndermek; "bir cevapta bir tool olur" diye reddetmek.
- Sonuçların sırası önemli değil — ID eşleşmesi önemli.

## 6. Guidance vs Lock ⭐ (haftanın en önemli ilkesi)
- **System prompt talimatı = rehberlik (probabilistic).** Model %98 uyar ama %2 sapma vardır; para/güvenlikte %2 felakettir.
- **Kod zorlaması = kilit (deterministic).** Örneğimiz: `process_refund`, aynı oturumda `get_customer` ile kimlik doğrulanmadıysa **kodda bloklu** — model ne yazarsa yazsın çalışmaz.
- Sınav kalıbı: "prompt'a kural yazıldı ama ihlaller sürüyor" → doğru şık her zaman **programmatic enforcement** (prerequisite gate, hook).
- **Temperature tuzağı:** temperature **rastgeleliği** kontrol eder, kural uyumunu DEĞİL. "Garanti nasıl sağlanır?" sorusunda `temperature=0` şıkkı **her zaman yanlıştır**.

## 7. Escalation & Handoff
- **Structured handoff:** insana devirde yapılandırılmış özet zorunlu — insan temsilci konuşma dökümünü **göremez**. İçerik: müşteri ID + kök neden + tutar/denenenler + önerilen aksiyon. "Customer needs help, escalating" tek başına anti-pattern.
- **Canlı gözlem (sınav maddesi):** "İnsanla görüşmek istiyorum" → **DERHAL eskale et**, önce araştırmaya kalkma. (Düzeltme: prompt'a açık eskalasyon kriterleri + few-shot örnekler — Week 6 konusu.)
- **close_session deseni:** kapatma **kararı** modelde (close_session tool'u), **infazı** kodda (flag + break). "Authority in the model, enforcement in code."

## 8. Hızlı Tuzak Listesi (sınav öncesi 60 saniyelik tekrar)

| Soru kalıbı | Refleks cevap |
|---|---|
| tool_result hangi rolle gider? | **user** (asla assistant / "tool") |
| Döngü ne zaman durur? | **stop_reason == "end_turn"**, koşulsuz |
| İterasyon limiti / metin kontrolü ile durdurma? | Anti-pattern |
| Tek cevapta çoklu tool_use? | Normal — hepsini çalıştır, tek user mesajında döndür |
| Kim tool çalıştırır? | Bizim kod; model sadece fiş yazar |
| Kural garantisi nasıl? | Kod/kilit; prompt = olasılıksal, temperature=0 = alakasız |
| "Talk to a human" dendi? | Derhal eskale, soru sorma |
| Handoff nasıl? | Yapılandırılmış özet (ID, kök neden, tutar, öneri) |
