# Hafta 3 El Notu — Tool Tasarımı & MCP Entegrasyonu (Domain 2, %18)

Sınav öncesi hızlı bakış. Task statement sırasıyla; sonda tuzak çiftleri ve karar kuralları.

---

## 1. Tool Description'ları (Task 2.1)

**Temel gerçek: description, modelin tool hakkında gördüğü TEK şeydir.** Kodunu, backend'ini, veritabanını göremez.

Her description için 4 parçalı reçete:
1. **Amaç** — ne yapar, ne döndürür ("kargo durumu, ETA, tutarlar")
2. **Girdi formatı** — kesin biçim: "CUST-XXXX biçiminde müşteri ID'si", "sadece rakam, baştaki # işaretini at"
3. **Örnek sorgular** — "örn. 'where is my package #12345?'" (few-shot'ın en ucuz hali)
4. **Sınır + komşu işareti** — "Hesap soruları için KULLANMA — onlar için get_customer kullan, müşteri 'my account' dese BİLE"

Fakir description'ın belirtileri (canlı ölçtük):
- `auto` modda: model harekete geçmek yerine gereksiz soru sorar (boşa tur)
- `any` modda: yanlış tool seçer VE girdi uydurur (canlı kanıt: `'<UNKNOWN>'`)

**Benzer tool'lar karışıyor — çözüm merdiveni (sınav favorisi):**
1. ÖNCE: description'ları zenginleştir (düşük emek, yüksek kaldıraç) ← "ilk adım" sorusunun doğru cevabı
2. Örtüşmeyi öldürmek için yeniden adlandır (`analyze_content` → `extract_web_results`)
3. Generic tool'u amaca özel tool'lara böl (`analyze_document` → `extract_data_points` / `summarize_content` / `verify_claim_against_source`)
- Few-shot örnekleri, routing katmanı, tool birleştirme = "ilk adım" sorusunda yanlış şıklar

**Gizli tuzak:** SYSTEM PROMPT'taki anahtar kelimeye duyarlı talimatlar iyi description'ı ezebilir ("önce müşteriyi anla" → model get_customer'a kayar). Seçim bozulduğunda system prompt'u da denetle.

input_schema İÇİNDEKİ alan seviyesi description'lar, tool description'ının küçük kardeşi — ikisini de kullan.

---

## 2. Yapılandırılmış Hata Yanıtları (Task 2.2)

**Generic "Operation failed" = anti-pattern.** Ajan, göremediği bilgiyle kurtarma kararı veremez.

Hata zarfı reçetesi:
```json
{"errorCategory": "transient|validation|business|permission",
 "isRetryable": true|false,
 "message": "insan-okur, sonraki adımı da söyleyen mesaj"}
```

| Kategori | Örnek | Doğru ajan tepkisi |
|---|---|---|
| transient | timeout, servis meşgul | retry |
| validation | yanlış girdi formatı | girdiyi düzelt, retry |
| business | iade limiti, kargolanmış sipariş | retry YOK; açıkla / escalate; müşteriye söylenebilir alternatif ekle ("iade öner") |
| permission | kayda erişim yok | retry YOK; escalate |

**EN kritik tuzak ayrımı — "bulunamadı" hata DEĞİLDİR:**
- Erişim arızası (timeout) → `is_error=true`, kategori transient
- Geçerli boş sonuç ("bu numarayla sipariş yok") → `is_error=FALSE` + `{"found": false, "message": "Query succeeded; no order exists"}`
- İkisini karıştırırsan: hiç var olmamış sipariş için müşteriye "sonra tekrar deneyin" denir

**Bilgi ≠ yetki:** `isRetryable: true` tek başına retry ettirmez — model kibarca sorar. Ya:
- system prompt'a retry POLİTİKASI yaz ("transient hatayı sormadan bir kez tekrar dene"), ya da
- daha sağlamı: transient retry'ları KODDA çöz (local recovery), modele sadece çözülemeyeni göster
- Kılavuz ifadesi: "subagents implement local recovery for transient failures, propagating only errors they cannot resolve, with partial results and what was attempted"

MCP'de: tool içinde exception fırlatmak `isError: true` bayrağını otomatik set eder. Yapılandırılmış JSON'u exception mesajının içine göm.

---

## 3. tool_choice — Üç Vites (Task 2.3)

| Vites | Anlamı | Ne zaman |
|---|---|---|
| `{"type": "auto"}` | tool çağırabilir, sadece konuşabilir de | varsayılan, sohbet ajanları |
| `{"type": "any"}` | BİR tool çağırmak ZORUNDA, seçim modelde | "çıktı mutlaka tool çağrısı olmalı ama doğru tool değişken" |
| `{"type": "tool", "name": "X"}` | X'i çağırmak ZORUNDA | deterministik ilk adım (her şeyden önce extract_metadata) |

Karar kuralı (iki soru):
1. Tool çağrısı zorunlu mu? HAYIR → auto. EVET → 2. soru.
2. HANGİ tool olduğu belli mi? EVET → forced. HAYIR → any.

Kritik mekanikler:
- `any`/forced turlarında model text bloğu ÜRETEMEZ — saf tool_use.
- **Zorlama + eksik bilgi = fabrikasyon.** any/forced BİR çağrıyı garanti eder, DOĞRU çağrıyı değil.
- **Turnike deseni:** ilk istekte zorla, sonraki turda auto'ya BIRAK — yoksa model sonsuza dek aynı tool'u çağırmaya mecbur kalır.
- Description'a yazılan sıra talimatı ("company policy: run FIRST") çoğu zaman çalışır ama olasılıksaldır. Garanti gerekiyorsa → forced tool_choice veya hook (kod-kilit).

---

## 4. Tool Dağıtımı (Task 2.3)

- **Ajan başına 4-5 tool = güvenilir seçim; 18 = bozulma.** Her ek tool karar karmaşıklığı ekler.
- Çözüm tool silmek DEĞİL — rollere göre ajanlara dağıtmak.
- **Uzmanlık dışı tool ER GEÇ yanlış kullanılır** (web araması verilen sentez ajanı bir gün arama yapar).
- **Scoped-tool istisnası:** yüksek frekanslı basit ihtiyaç (%85 basit doğrulama) → ajana DAR kapsamlı tool ver (`verify_fact`); karmaşık vakalar (%15) koordinatör üzerinden akmaya devam etsin. Sıfır yetki değil, asgari yetki.
- Generic tool yerine kısıtlı alternatif: `fetch_url` → `load_document` (doküman URL'si doğrular).

---

## 5. MCP Sunucuları & Yapılandırma (Task 2.4)

**MCP = USB-C:** tool'ları standart priz arkasında BİR KEZ yaz; her MCP istemcisi (Claude Code, Agent SDK, Desktop...) takılır. M×N entegrasyon → M+N.

Aktörler: **server** (tool + resource barındırır) / **client-host** (takılır) / **bağlantı anında** istemci, bağlı TÜM sunucuların tool'larını AYNI ANDA keşfeder (tepsi kalabalığı riski burada da geçerli!).

**Scope tablosu (klasik sınav sorusu):**

| Dosya | Scope | Kim görür | Ne için |
|---|---|---|---|
| `.mcp.json` (repo kökü) | proje | clone'layan herkes (git ile taşınır) | takım tool'ları: Jira, şirket DB'si |
| `~/.claude.json` | kullanıcı | sadece sen, tüm projelerinde | kişisel / deneysel sunucular |

Karar sorusu: "Takım arkadaşımın da buna ihtiyacı olur mu?"

**Sırlar:** `"env": {"TOKEN": "${TOKEN}"}` — ortam değişkeni EXPANSION'ı. Dosya commit'lenir; gerçek değer her geliştiricinin kendi ortamında. Düz metin token'ı ASLA commit'leme — repo private olsa bile.

**Tool vs Resource:**
- Tool = AKSİYON ("yap") — lookup, cancel, refund
- Resource = okunacak KATALOG ("oku") — `orders://catalog`
- Amaç: ajana mevcut veriyi keşif amaçlı tool çağrıları YAPTIRMADAN göstermek
- Claude Code'da resource `@server:uri` ile bağlanır

**Topluluk vs custom:** standart entegrasyon (Jira, GitHub) → mevcut topluluk sunucusu. Custom sunucu SADECE takıma özel iş akışları için. "Jira için sıfırdan sunucu yaz" her zaman yanlış şıktır.

Ayrıca:
- İstemci tarafında tool adı: `mcp__<sunucu>__<tool>`
- MCP tool description'larını zenginleştir; yoksa ajan built-in'i (Grep) senin daha yetenekli MCP tool'una tercih edebilir
- Claude Code, proje .mcp.json'ına güvenmeden önce ONAY ister (makinende komut çalıştırıyor)

---

## 6. Built-in Tool'lar (Task 2.5)

| Sorunun şekli | Tool |
|---|---|
| "X'i İÇEREN dosyalar / X'i kim ÇAĞIRIYOR / bu hata mesajı nerede" | **Grep** (içerik) |
| "`**/*.test.tsx` gibi İSİMLİ dosyalar" | **Glob** (yol deseni) |
| dosyayı komple yükle | **Read** |
| dosyayı komple yaz/üzerine yaz | **Write** |
| benzersiz metin eşleşmesiyle hedefli değişiklik | **Edit** |
| bir şey ÇALIŞTIR: test, git, script, kurulum | **Bash** |

**Grep/Glob turnusol testi:** aranan şey dosyanın ADINDA mı, İÇİNDE mi? İçinde → Grep, istisnasız. Tuzak formatı: "processPayment'ı kim çağırıyor" sorusuna yanlış şıkta makul görünen `**/*payment*` glob deseni konur.

**Edit'in Aşil topuğu:** old_string dosyada BENZERSİZ olmalı.
- "matches multiple locations" hatası → çözüm merdiveni:
  1. çapayı genişlet (benzersiz kılan komşu satırları dahil et — örn. `return total * 0.1` çapası)
  2. garantili B planı: **Read + Write** (kılavuzun resmi cevabı)
- Yine de önce Edit: Write tüm dosyayı yeniden yazar → daha çok token + başka yeri yanlışlıkla değiştirme riski. Edit cerrahi, Write organ nakli.

**Bash tuzağı:** "çalışır ama yanlış" — `ls`/`find` dosya listeler, ama sınavda bul/oku/yaz işlerinin doğru cevabı özel amaçlı tool'dur (güvenlik yüzeyi, taşınabilirlik, yapılandırılmış çıktı). Bash'in meşru bölgesi = "yap" fiilleri.

**Keşif stratejisi:** kademeli, asla hepsini-baştan-oku değil. Grep ile giriş noktası → o dosyayı Read → import'ları takip et. Wrapper modül izleme: önce export edilen adları listele, sonra her adı codebase'de Grep'le.

---

## 7. Savunma Derinliği (kesişen konu, sınav bayılır)

Tek business kuralı ($500 iade limiti) için üç katman:
1. **Description uyarısı** ("500 USD üstü yasak — escalate_to_human kullan") → ucuz ön-kontrol; model mahkûm çağrıyı hiç yapmayabilir (canlı gözlendi)
2. **İstemci tarafı hook** (PreToolUse) → çağrı daha çıkmadan bloklar
3. **Sunucu tarafı raise** (business error) → son kale; hook'suz istemci bağlansa bile kural delinmez

Altın formül: description/prompt = olasılığı düşürür; kod-kilit = imkânsızlaştırır. "Description'a yazdık, kod kontrolünü kaldıralım mı?" → cevap her zaman HAYIR.

Escalation handoff yapısı (insanın konuşmaya erişimi YOK):
`customer_summary` (kim/sipariş/tutarlar) + `root_cause` (ajan neden çözemiyor) + `recommended_action` (insan ne yapmalı).

---

## 8. Tuzak Çiftleri — bunları çalış
- **any vs forced** (tool şart ama HANGİSİ değişken → any)
- **Grep vs Glob** (içerik vs dosya adı)
- **transient vs business** (retry vs asla-retry)
- **hata vs geçerli boş sonuç** (is_error true vs false)
- **proje vs kullanıcı scope** (.mcp.json vs ~/.claude.json)
- **tool vs resource** (yap vs oku)
- **description uyarısı vs kod-kilit** (olasılık vs garanti)
- **Edit vs Read+Write** (cerrahi vs garantili B planı)

## 9. Canlı gözlenen incelikler (kılavuzda yok ama gerçek)
- Özetleme çıkarım enjekte edebilir (20dk ×2 → "40 dakika") — handoff fidelity ailesi
- Ajan, sisteminde olmayan seçenekler önerebilir — önerileri tool çıktılarıyla sınırla (system prompt)
- Bayat snapshot: tool state değiştiriyorsa resource/kataloğu senkron tut; ajan çelişkiyi sessizce çözmek yerine (doğru davranışla) işaretler
- macOS: `sed -i ''` (BSD), `python` komutunu venv sağlar, ANTHROPIC_API_KEY claude.ai girişini ezer
