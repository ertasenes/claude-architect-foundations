# Week 5 — El Notu: Prompt Engineering & Structured Output
**Domain 4 · Sınavın %20'si · Task Statement 4.1–4.6**

---

## 0. GÜVENİLİRLİK PİRAMİDİ (her şeyin çatısı)

| # | Katman | Ne yapar | Ne YAPMAZ |
|---|---|---|---|
| 1 | **Şema** (tool_use + input_schema) | Sözdizimi ve tipi **garanti eder** | Anlamı denetlemez |
| 2 | **Şema tasarımı** (nullable, enum+other) | Uydurma baskısını **azaltır** | Garanti vermez |
| 3 | **Few-shot** | Belirsiz vakada muhakemeyi **düzeltir** | Eksik bilgiyi yaratmaz |
| 4 | **Validation** (Pydantic) | Semantik hatayı **yakalar** | Onarmaz |
| 5 | **Retry** | Biçim/yapı hatasını **onarır** | Yokluk ve çelişkiyi çözmez |
| 6 | **İnsan incelemesi** | Onarılamayanı **karara bağlar** | — |

> Sınav soruları çoğunlukla "bu arıza hangi katmanın işi" diye sorar. Katmanı yanlış seçmek en sık hata.

**Hangi arıza hangi katman:**
- JSON bozuk / alan eksik / tip yanlış → **Şema**
- Belgede olmayan alan makul değerle doluyor → **Şema tasarımı (nullable)**
- Belirsiz belgelerde tutarsız karar → **Few-shot**
- Kalemler toplama uymuyor / değer yanlış alanda → **Validation + insan**
- Tarih formatı yanlış geliyor → **Retry**
- Kaynak kendisiyle çelişiyor → **Çelişkiyi raporla + insan** (asla retry değil)

---

## 1. TS 4.3 — tool_use ile yapılandırılmış çıktı

### Mekanik
- Hedef veri şeklini bir tool'un `input_schema`'sı olarak tanımla → `tool_choice` ile zorla → veriyi `tool_use.input`'tan oku.
- **Tool asla yürütülmez.** Tool bir "matbu form"dur; formun kendisi veridir.
- Prompt'ta "JSON döndür" demek = **guidance (olasılıksal)**. Şema = **lock (deterministik)**.
- Bloklara **tipe göre** eriş: `next(b for b in resp.content if b.type == "tool_use")`. `content[0]` **yanlıştır** — model önce düşünme metni üretebilir.
- `stop_reason`: prompt-only → `end_turn`; forced tool → `tool_use`.

### Anti-pattern
- Markdown fence'i / önsözü string işlemleriyle **kazımak**. Model bir gün notu fence'in dışına, sonra başa, sonra iki blok halinde koyar. **Yapı istiyorsan yapıyı zorla, sonradan temizlemeye çalışma.**

### tool_choice üç vites (Week 3 tekrarı — sınav tuzağı)
| Mod | Anlamı | Ne zaman |
|---|---|---|
| `"auto"` | Model tool çağırabilir de çağırmayabilir | Yapılandırılmış çıktı garantisi gerekmiyorsa |
| `"any"` | Tool çağırmak **zorunlu**, hangisi **modele ait** | Çok şema var, belge tipi **bilinmiyor** |
| `{"type":"tool","name":"X"}` | **Belirli** tool zorunlu | Tek şema; ya da bir tool'un ilk çalışması şart (ör. `extract_metadata` zenginleştirmeden önce) |

- **Ayrım cümlesi:** *tool zorunlu ama hangisi değişken → `any`. Belirli tool zorunlu → forced.*
- Forced'ı turlar boyunca açık bırakmak → model sonsuz döngüye girer. Desen: **ilk tur forced, sonra `auto`'ya bırak (turnike).**
- Forcing fabrikasyon riskini artırır (model tool çağırmaktan başka çıkış bulamaz).

### Şema neyi garanti EDER / ETMEZ
- ✅ Geçerli JSON, doğru tip, zorunlu anahtarların varlığı
- ❌ **Semantik doğruluk:** kalemler toplama uymaz, değer yanlış alana yazılır, tarih mantıksız olur
- `1250.00` mükemmel geçerli bir `number`'dır — sadece **yanlış** number'dır.
- **Tip değiştirmek semantik hatayı çözmez** (`number` → `integer` klasik yanlış şık).

### Şema açıklamaları = yorum katmanı
- Şema **şekli** zorlar, `description` **yorumu** yönlendirir.
- Normalizasyon kurallarını açıklamaya yaz: `1.250,00 → 1250.00`, ISO 8601 `YYYY-MM-DD`, para birimi ISO 4217.
- Kılavuz becerisi: *format normalization rules in prompts alongside strict output schemas.*

### Gerçek dünya notu (sınav dışı ama bilmek iyi)
- API'de artık **structured outputs** var: `output_config.format` (JSON çıktısı) ve tool tanımında `strict: true` (tool girdisi garantisi). Şemayı bir **gramere derleyip** token üretimini kısıtlar.
- Sınırlar: istek başına 20 strict tool, 24 opsiyonel parametre, 16 union-tipli parametre. Gramer 24 saat cache'lenir.
- Enum **büyük/küçük harfi garanti değil** → karşılaştırmayı case-insensitive yap, sadece harf büyüklüğüyle ayrılan enum değeri kullanma.
- `stop_reason: "refusal"` veya `"max_tokens"` durumunda çıktı şemaya uymayabilir.
- **Sınavda doğru cevap yine tool_use + JSON schema.**

---

## 2. TS 4.3 (devam) — Şemayı halüsinasyona karşı tasarlamak

### `required` gerçekte ne demek
- `required` = **anahtar bulunmalı**. Değerin non-null olması **şart değil**.
- `["string","null"]` + `required` **geçerli ve faydalı** bir kombinasyon: `{"due_date": null}` geçerli, `{}` geçersiz.
- Faydası: downstream kod `data["x"]` yazabilir (KeyError yok) **ve** "alan gelmedi" ile "geldi ama boş" ayrımı korunur.

### Nullable = kaçış kapısı
- Kaçış kapısı yoksa model **uydurmak zorunda kalır**. Uydurma modelin karakterinden değil, **şemanın bıraktığı tek seçenekten** doğar.
- Nullable + açık talimat: *"belge belirtmiyorsa null döndür, tahmin etme, issue_date'i kopyalama."*
- Nullable, veri **mevcutken** çıktıyı bozmaz (kalite kaybı yok).
- **Aşırıya kaçma:** union tipler gramer maliyetlidir. Sadece kaynakta **gerçekten yok olabilecek** alanlar nullable olur.

### enum + "other" + detail
- Kapalı enum, model gerçek dünya değerini **listeye zorla sığdırır** → bilgi kaybı.
- Doğru desen: `enum: [..., "other"]` **+** `*_detail` nullable string (birebir ifade).
- Enum'u sürekli büyütmek **çözüm değil** (koşu bandı). Enum'u tamamen kaldırmak da **çözüm değil** (kategorizasyon ölür).
- **"other" bir kullanım kriteri ile gelmeli**, yoksa çöp kutusuna dönüşür: *"other'ı yalnızca hiçbir kategori işlevsel olarak uymuyorsa kullan — sadece başlık farklı diye değil."*

### Canlı deney kanıtı
| Belge | Katı şema (v1) | Güvenli şema (v2) | Hata sınıfı |
|---|---|---|---|
| Tam belge | ✅ | ✅ | — |
| Vade yok | ❌ **düzenlenme tarihini vade alanına kopyaladı** | ✅ `null` | Değer yanlış alanda (**sessiz semantik**) |
| Liste dışı ödeme ("Papara") | ❌ `bank_transfer` | ✅ `other` + birebir metin | Bilgi kaybı (**sessiz kategori**) |

> İkisinin ortak özelliği: **sessiz.** Hata yok, uyarı yok, şemadan geçiyor. Sınavda "makul ama yanlış değerler geliyor, hiçbir hata almıyoruz" = şema tasarımına bak.

---

## 3. TS 4.2 — Few-shot prompting

### Ne çözer / ne çözmez
| Problem | Few-shot? |
|---|---|
| Belirsiz vakada tutarsız karar | ✅ |
| Yapısal çeşitlilik (satır içi atıf vs bibliyografya) | ✅ |
| False positive / kabul edilebilir deseni hatalı işaretleme | ✅ |
| Çıktı formatı tutarsızlığı (serbest metin alanları) | ✅ |
| JSON bozukluğu / şema uyumu | ❌ → **Şema** |
| Kaynakta olmayan bilgi | ❌ → **Nullable** |

### Kurallar
- **2–4 örnek.** Sayıyı değil, **kapsanan belirsizlik çeşidini** çoğalt. 25 örnek yanlış yaklaşım.
- Örnek **gerekçe taşımalı**: "neden bu karar, neden makul alternatif değil". Böylece model **genelleştirir**, ezberlemez.
- Karar **kuralını** başa yaz: *"Başlığa değil ödeme yükümlülüğüne göre karar ver."*
- Few-shot **ölçülmüş bir tutarsızlığın** çözümüdür, varsayılan ilk hamle değil. (Week 3 sırası: **önce tool açıklamalarını iyileştir**, sonra few-shot.)
- Kaynak belge yapısı çeşitliyse: ön-işleme kodu yazmak yerine **her iki yapıdan doğru çıkarımı gösteren örnek** ver.

### Canlı deney kanıtı
- Güçlü sinyalli belgelerde (belge kendisi "ödeme yükümlülüğü doğurmaz" yazıyor): prose = few-shot, **fark yok**.
- Sınır vakada fark açıldı: "ÖDEME BİLDİRİMİ" başlıklı makbuz → prose 2/2 `"other"` seçti, **kendi gerekçesi** "tahsil edildi + bakiye sıfır" diyordu. Model enum değerlerini **anlamsal kategori** değil **isim etiketi** olarak okudu. Few-shot 2/2 `"receipt"` dedi — **farklı başlıklı** bir örnekten kuralı genelleştirdi.
- Yan etki: few-shot serbest metin alanlarının **ifadesini de sıkılaştırdı** (format tutarlılığı).

> **Tekrarlayan ilke:** Prompt katmanı iyileştirmeleri (few-shot, açık kriter) **belirsizlik varsa** kazanır. Sinyal bariz ise basit prompt da yeter.

---

## 4. TS 4.1 — Açık kriterler ve false positive azaltma

### Temel ayrım
- ❌ **Tutum:** "muhafazakâr ol", "yalnızca yüksek güvenli bulguları raporla", "gereksiz detaya girme"
- ✅ **Spesifikasyon:** kategorik **REPORT listesi** + kategorik **SKIP listesi**

**Neden tutum işe yaramaz:** Sistem şu anda **yanlış bulgulara emin**. Yüksek FP oranı = kalibrasyon bozuk. Bozuk kalibrasyonu filtre olarak kullanamazsın.

### Kriter yazma
- REPORT: sınanabilir koşullar. Örnek: *"yorumun iddia ettiği davranış kodun gerçek davranışıyla çeliştiğinde işaretle"* (≠ "yorumların doğruluğunu kontrol et").
- SKIP listesi **REPORT kadar önemli**: stil, isimlendirme, biçim, bağlamdan anlaşılan sabitler, tip ipuçları, sıcak yolda olmayan performans, kütüphane/idiom tercihleri.
- **Severity için somut tanım + kod örneği**: `critical` = sömürülebilir / veri bozan; `major` = gerçekçi girdide yanlış sonuç veya çökme; `minor` = doğru ama kırılgan.
- Tanımsız severity → aynı kod farklı koşularda farklı seviye → **"critical" etiketi anlamını yitirir** ve merge politikası zar atmaya bağlanır.

### `detected_pattern` alanı
- Bulguyu tetikleyen **kod yapısını** kaydeder (`"f-string in SQL"`, `"unguarded list index"`).
- Amaç: geliştiriciler bulguları reddettiğinde **hangi desenin** sistematik FP ürettiğini **saymak**.
- "3 bulgu reddedildi" işe yaramaz; "reddedilenlerin %80'i şu desenden" eyleme geçirilebilir.
- Kriter listesi yoksa model **her seferinde farklı ifade** uydurur → gruplanamaz → analiz imkânsız.

### Güven erozyonu
- Yüksek FP üreten kategoriler, **doğru kategorilere olan güveni de** yok eder. 40 maddenin 30'u gereksizse 31. maddedeki gerçek SQL injection da atlanır.
- Kılavuz becerisi: **yüksek FP kategorisini geçici olarak kapat**, prompt'unu iyileştir, sonra geri aç.
- Kendisiyle çelişen bir araç (bazen şikayet eden, bazen susan) tek bir yanlış bulgudan **daha zararlıdır**.

### Canlı deney kanıtı (sınır vakalar, 3 koşu)
| | Belirsiz ("muhafazakâr ol") | Kategorik kriter |
|---|---|---|
| Koşu başına bulgu | 3 / 2 / 3 (**oynak**) | 3 / 3 / 3 (**sabit**) |
| Kontrol (SQL injection) | 3/3 ✅ | 3/3 ✅ |
| Kararsız bulgu | var (2/3, **iki farklı severity**) | yok |
| Sessiz veri bozulması (`return 0.0`) | **0/3 kaçırdı** ❌ | 3/3 yakaladı ✅ |

> **En büyük bulgu:** Açık kriterler yalnızca gürültüyü filtrelemez — **modelin nereye bakacağını belirler.** Kriter listesi bir sansür değil, bir **arama planıdır**. Precision ile birlikte **recall de arttı**.
> Not: tartışmasız kusurlarda iki kol **eşitti** — fark belirsizlikte doğar.

---

## 5. TS 4.4 — Validation, retry ve geri besleme

### Pydantic iki denetçi tipi
- `@field_validator` → **tek alan** (slug biçimi, uzunluk, karakter kümesi)
- `@model_validator(mode="after")` → **alanlar arası** (kalemler toplamı = total, `due_date > issue_date`)
- **Semantik doğrulama burada yaşar** — JSON Schema'nın ifade edemediği kural türü.
- `due_date <= issue_date` reddi, "vade bulunamadı, düzenlenme tarihini kopyaladım" hatasını **suçüstü yakalar**.

### Geri besleme mekaniği
- Gönderilecekler: **orijinal belge + başarısız çıkarım + SPESİFİK doğrulama hataları**.
- ❌ "extraction failed, try again" (spesifik değil) · ❌ yeni oturum açıp sıfırdan gönderme · ❌ hatayı system prompt'a yazma
- Hata metni **`tool_result` olarak** geri gider ve **`role: "user"`** ile taşınır (Week 1 tuzağı, burada gerçek işe yarıyor). Model açısından bu, aracın "girdin geçersiz" demesidir.

### ÜÇ SÜTUN TESTİ (haftanın en kritik ayrımı)
| Durum | Retry? | Doğru davranış |
|---|---|---|
| Bilgi **var**, biçimi bozuk (`"15/03/2026"`, `"<UNKNOWN>"`) | ✅ **EVET** | Spesifik hatayla retry |
| Bilgi **yok** (madde belgede geçmiyor, ek belge sağlanmamış) | ❌ **HAYIR** | Nullable + politika varsayılanı |
| Bilgi **var ama kendisiyle çelişiyor** | ❌ **HAYIR** | Çelişkiyi işaretle → insan |

> **Tek soru:** "Bilgi modelin elinde mi, sadece şekli mi bozuk?"

### Canlı deney kanıtı — retry yanlış hata sınıfına uygulanınca
- **Kaynak çelişkisi** (kalemler 450+300=750, belgede yazan toplam 800): retry 2. denemede **kalem tutarını 300 → 350 yaptı**. Şema uyumlu, doğrulamadan geçti, `total_amount` belgeyle birebir — **tahrif edilmiş kayıt "VALID" olarak kaydedildi.**
- **Bilgi yokluğu** (vade yok) → **teslim olma eğrisi**:
  1. `"<UNKNOWN>"` (dürüst, tip hatasıyla reddedildi)
  2. `issue_date` kopyası (sıralama kuralıyla reddedildi)
  3. `issue_date + 30 gün` **uydurdu** → VALID
- **Ders:** "Düzelt" komutu, düzeltilecek bir şey olmadığında **"uydur" komutuna dönüşür.** Her ret, dürüst cevabın yanlış olduğu sinyalini güçlendirir.

### Doğru mimari
1. Şemayı tasarla → çelişki ve yokluk **ifade edilebilir** olsun
2. Doğrulama katmanı → semantik hatayı yakala
3. Retry'ı **SINIRLA** → yalnızca biçim/yapı hataları + **maksimum deneme sayısı**
4. Kalanı insana yönlendir
- **Hata sınıfına göre dallan** (Week 3 `errorCategory`/`isRetryable` deseninin doğrulama sürümü): biçim → retry; semantik çelişki → insan; yokluk → politika.

### Öz-düzeltici şema deseni
- `stated_total` (belgede yazan) **+** `calculated_total` (kalemler toplamı) **+** `conflict_detected` (boolean)
- Çelişki bir **hata** değil, bir **veri noktası** haline gelir. Model çelişkiyi gizlemez çünkü **oturacak yeri var**.
- Bayrağa **ek olarak** kodda aritmetiği de kontrol et: model bayrağı bir **beyan**, aritmetik bir **kanıt** (prompt guidance, kod lock).
- Aynı fikir: `conflict_detected` benzeri bayraklar, tutarsız kaynak verisi için genel desendir.

### Enstrümantasyon dersi
- **Başarı yolunu da logla.** Sadece hata durumunda payload yazdırırsan "yeşil" gördüğün şeyin uydurma olduğunu **fark etmezsin**.

---

## 6. TS 4.6 — Çok-instance ve çok-geçişli inceleme

### Öz-inceleme neden zayıf
- Üreten oturum **üretim gerekçesini taşır**; kendi kararlarını sorgulamaya yatkın değildir.
- ❌ "kendi kodunu titizlikle incele" talimatı · ❌ extended thinking · ❌ aynı oturumda 3 kez inceleme
- ✅ **Bağımsız instance** (üretim bağlamı taşımayan)
- Week 4 canlı kanıtı: bağımsız reviewer, üreten oturumun bıraktığı docstring–kod çelişkisini ve eksik satırları yakaladı.

### Büyük PR'lar (14 dosya vb.)
- Belirti: bazı dosyalarda detaylı bazı dosyalarda yüzeysel yorum; **aynı deseni bir dosyada işaretleyip diğerinde onaylama**; bariz buglar kaçıyor.
- Kök neden: **dikkat dağılması (attention dilution)**.
- Çözüm: **dosya başına yerel geçiş + ayrı bir dosyalar-arası entegrasyon geçişi** (prompt chaining).

### Yanlış şıklar ve nedenleri
| Şık | Neden yanlış |
|---|---|
| Daha büyük context window | Dikkat **kalitesi** problemi, kapasite problemi değil |
| 3 koşu yapıp ≥2'de çıkanı al | Aralıklı yakalanan **gerçek** bugları **bastırır**; tutarlı üretilen **gürültüyü geçirir**. (Kanıt: gürültü 2/3 çıktı → konsensüsü geçerdi; kaçan gerçek kusur 0/3 → asla kurtarılamaz) |
| PR'ı geliştiriciye böldürtmek | Yükü insana atar, sistemi düzeltmez |
| Aynı oturumda tekrar | Dikkat dağılmasını tekrarlar |

> **Genel kural:** "N kez çalıştır, çoğunluğu al" Domain 4'te neredeyse her zaman **yanlıştır**. Tekrar, tasarım hatasını çözmez.

- Ek desen: modelin her bulgu yanında **kendi güvenini bildirmesi**, kalibre edilmiş yönlendirme için kullanılabilir — ama **FP azaltma çözümü olarak değil**.

---

## 7. TS 4.5 — Message Batches API

### Çıplak gerçekler
- **%50 daha ucuz**
- **24 saate kadar** işleme penceresi
- **Gecikme SLA'sı YOK** — "genelde daha hızlı bitiyor" bir güvence değildir
- `custom_id` ile istek/cevap eşleştirme
- Tamamlanma **polling** ile takip edilir
- **Tek istek içinde çok turlu tool çağrısı DESTEKLENMEZ**

### Karar kuralı: **biri bekliyor mu?**
| İş yükü | Cevap | API |
|---|---|---|
| Merge öncesi zorunlu kontrol | Geliştirici bekliyor | **Senkron** |
| Gece çalışan teknik borç raporu | Kimse beklemiyor | **Batch** |
| Canlı müşteri destek ajanı | Müşteri hatta | **Senkron** |
| Haftalık uyum denetimi | — | **Batch** |
| 5.000 belgelik ilk yükleme | — | **Batch** |
| Kullanıcı ekranda belge yüklüyor | Bekliyor | **Senkron** |

### Batch içinde ne yapılır / yapılmaz
| Yapılabilir | Yapılamaz |
|---|---|
| Tek turlu `tool_use` ile extraction (tool **yürütülmüyor**, form dolduruluyor) | Agentic loop (çok turlu tool yürütme) |
| Sınıflandırma, özetleme, çeviri | Subagent orkestrasyonu |
| Yapılandırılmış çıktı + şema | **Tek istek içinde** validation-retry döngüsü |

- **Doğrulama ve retry batch'in DIŞINDA yaşar:** batch dön → doğrula → başarısızları **ikinci bir batch**'te gönder.

### Hata yönetimi
- Sonuçlar **sırasız** gelir → `custom_id` ile eşleştir. *"Sırasız geldiği için batch kullanamayız" şıkkı YANLIŞTIR.*
- **Tüm batch'i asla yeniden gönderme.** Başarısız `custom_id`'leri tespit et, **gerekli değişiklikle** yeniden gönder (ör. `max_tokens`'a takılan / context limitini aşan belgeyi **parçala**).
- `stop_reason: "max_tokens"` = kesilmiş çıktı → parçalayıp yeniden gönder.

### SLA ARİTMETİĞİ (mutlaka ezberle)
- kuyruk bütçesi = SLA − 24 saat (en kötü işleme süresi)
- gönderim aralığı ≤ kuyruk bütçesi
- **İki bacak var: bekleme + işleme.** Kuyruk bacağını unutmak en sık hata.
- Her zaman **en kötü durumu** (24s) kullan, ortalamayı değil.

| SLA | Kuyruk bütçesi | Sonuç |
|---|---|---|
| 30 saat | 6 saat | 6 saatte bir (veya daha sık) gönder |
| 28 saat | 4 saat | 4 saatte bir gönder |
| 26 saat | 2 saat | 2 saatte bir gönder |
| 24 saat | 0 | **Batch bu SLA'yı KARŞILAYAMAZ** |

- Kontrol yöntemi: *"24 saatte bir gönderirsem, batch'ten hemen sonra gelen belge 24s bekler + 24s işlenir = 48s."*

### Ölçekleme öncesi
- Büyük hacme geçmeden **küçük bir örneklemde (ör. 50 belge) senkron API ile** şemayı ve few-shot'ları oturt.
- Aksi halde: 5.000 belgenin parası + 18 saat kayıp + baştan başlama.
- Week 4 aynı ders: bağımsız reviewer koşusu $0,44 → *"refine on samples before scaling"*.

---

## 8. SINAV TUZAKLARI — KIRMIZI BAYRAKLAR

### Neredeyse her zaman YANLIŞ olan şıklar
1. **Modelin kendi güvenini süzmesine dayanan her şey:** "self-reported confidence score", "only report high-confidence findings", "be conservative". → *Kalibrasyon bozuk olduğu için problem var; bozuk kalibrasyon filtre olamaz.*
2. **"Retry ekle"** — kök neden **yokluk** veya **kaynak çelişkisi** olduğunda.
3. **"N kez çalıştır, çoğunlukta olanı al"** (konsensüs filtresi).
4. **"Daha büyük context window'lu modele geç"** — dikkat kalitesi problemlerinde.
5. **`temperature=0`** — garanti/uyum tipi sorularda "kalıcı yanlış cevap".
6. **Tip değiştirmek** (`number`→`integer`) — semantik hatalarda.
7. **Sentiment analizi / duygu tabanlı yönlendirme** — karmaşıklık göstergesi değildir.
8. **Aşırı mühendislik:** prompt optimizasyonu denenmeden ML sınıflandırıcı, routing katmanı, ayrı model eğitimi.
9. **Yükü kullanıcıya/geliştiriciye atmak** ("PR'ı sen böl") — sistem düzelmiyor.
10. **`enum`'ı tamamen kaldırmak** — kategorizasyonu yok eder.
11. **Talimatı büyük harfle/daha sert yazmak** — guidance guidance kalır.
12. **String işlemleriyle çıktıyı temizlemek** — yapıyı zorlamak yerine kazımak.

### "İlk adım" soruları
- "En etkili **ilk** adım" = **en düşük efor / en yüksek kaldıraç** olan kök-neden müdahalesi.
- Sıra: **açıklama/kriter iyileştirme → few-shot → şema/mimari değişikliği → ek altyapı.**
- Week 3 örneği: benzer tool'lar karışıyorsa **ilk adım açıklamaları zenginleştirmek**, few-shot değil.

### Soru kalıbı → cevap yönü
| İfade | Bakılacak yer |
|---|---|
| "Şema uyumu %100 ama değerler yanlış" | Semantik → validation / şema tasarımı |
| "Makul ama belgede olmayan değerler, hata yok" | `required` + nullable eksikliği |
| "Belirsiz belgelerde tutarsız karar" | Few-shot |
| "FP yüksek, ekip güvenini yitirdi" | Kategorik REPORT/SKIP + FP kategorisini geçici kapatma |
| "Tek geçişte 14 dosya, çelişkili bulgular" | Dosya başına geçiş + entegrasyon geçişi |
| "Kendi ürettiği kodu inceliyor" | Bağımsız instance |
| "Maliyeti düşür" + "gece çalışıyor" | Batch |
| "Maliyeti düşür" + "bloke ediyor" | Senkron kalsın |
| "X saat SLA + batch" | Kuyruk bütçesi = SLA − 24 |

---

## 9. MULTIPLE-RESPONSE PROSEDÜRÜ (kişisel zayıflık — 4 hata)

Sınav her soruda kaç cevap isteneceğini **yazar**. Kısmi puan **yok**.

1. Soruyu okumaya **son satırdan başla** → "(İki cevap seçin)" var mı?
2. Her şıkkı **ayrı ayrı** doğru/yanlış işaretle (kafanda "en iyi ikisi"ni arama).
3. Doğru işaretlediklerini **say**, istenen sayıyla karşılaştır.
4. Fazlaysa: hangisi kriteri **tam olarak** karşılıyor diye ayıkla.
5. Aynı şıkkı iki kez yazma.

---

## 10. HAFTALAR ARASI BAĞLANTILAR

| Bu haftanın konusu | Nereden geliyor |
|---|---|
| `tool_result` → `role: "user"` (retry geri beslemesi) | Week 1 agentic loop |
| Prompt = guidance, kod/şema = lock | Week 1–2 (hook vs prompt) |
| `tool_choice` üç vites + turnike deseni | Week 3 |
| Hata sınıfına göre dallanma (`errorCategory`, `isRetryable`) | Week 3 MCP hata yanıtları |
| "Önce açıklamaları iyileştir, sonra few-shot" | Week 3 tool description |
| Test-first iterasyon = validation-retry döngüsü | Week 4 (pytest) |
| Bağımsız reviewer instance | Week 4 lesson 4.6 (canlı kanıt) |
| `-p`, `--output-format json`, `--json-schema` (CI'da yapılandırılmış çıktı) | Week 4 lesson 4.6 |
| Örneklemle rafine et, sonra ölçekle | Week 4 ($0,44 reviewer koşusu) |
| `conflict_detected`, çelişkiyi atıflı raporlama | **Week 6'ya köprü** (provenance, insan incelemesi) |

---

## 11. TEK CÜMLELİK ÖZLER

- Model bir bilgiyi **ifade edemiyorsa**, onun yerine ifade edebileceği bir şey söyler. Şema tasarımı, modelin **doğruyu söyleyebilmesi için gereken kelime dağarcığını** vermektir.
- Şema **kutucukları çizer**; kutuya hangi sayının yazıldığını denetlemez.
- "Düzelt" komutu, düzeltilecek bir şey olmadığında **"uydur" komutuna dönüşür**.
- Kriter listesi bir sansür değil, bir **arama planıdır**.
- Prompt katmanı iyileştirmeleri **belirsizlikte** kazanır; bariz sinyal yardım istemez.
- Batch: **biri bekliyorsa senkron, kimse beklemiyorsa batch.**
