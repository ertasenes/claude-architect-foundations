# Week 4 El Notu — Claude Code Yapılandırması ve İş Akışları (Domain 3, ~%20)

Sınav hazırlığı için hızlı başvuru notları. Tüm başlıklar Task Statement 3.1–3.6 ile eşleşir.

---

## 1. CLAUDE.md hafıza hiyerarşisi (TS 3.1)

**Üç seviye:**
- `~/.claude/CLAUDE.md` → **user-level (kişisel ajanda)**: kişiseldir, makinendeki TÜM projelerde geçerlidir, version control'a GİRMEZ, takım arkadaşlarına ASLA gitmez.
- Kök `CLAUDE.md` (veya `.claude/CLAUDE.md`) → **project-level (şirket el kitabı)**: git'e commit'lenir, repoyu klonlayan/pull eden herkese otomatik gelir.
- `altklasor/CLAUDE.md` → **directory-level (departman panosu)**: Claude o klasördeki dosyalarla ÇALIŞIRKEN yüklenir (açılışta DEĞİL).

**Yüklenme davranışı (bu tabloyu ezberle):**

| Mekanizma | Ne zaman yüklenir | Token tasarrufu? |
|---|---|---|
| CLAUDE.md (user/project) | oturum açılışında | — |
| CLAUDE.md içindeki `@import` | oturum açılışında (içerik satır içine açılır) | HAYIR — sadece düzen |
| directory CLAUDE.md | o klasördeki dosyalara dokunulunca | evet (koşullu) |
| `paths:` içeren `.claude/rules/*.md` | desene uyan dosyaya dokunulunca | EVET (asıl amacı bu) |
| `paths:` içermeyen `.claude/rules/*.md` | açılışta, koşulsuz | HAYIR |

**@import gerçekleri:**
- Sözdizimi: `@yol/dosya.md` içeren bir satır; yol, CLAUDE.md'nin konumuna görelidir.
- SADECE düzenleme aracıdır. Import edilen dosyalar da açılışta yüklenir ve context tüketir.

**Teşhis seti:**
- `/memory` → açılış envanteri: şu an hangi hafıza dosyaları yüklü.
- Oturum çıktısındaki `Loaded <dosya>` satırları → koşullu katmanların (directory CLAUDE.md, path rules) tetiklenme kanıtı.
- Koşullu katmanlar açılıştaki `/memory` listesinde GÖRÜNMEZ — yoklukları normaldir.

**Temel ilke (TÜM domain'lerde tekrar eder):**
- CLAUDE.md **bağlamdır, zorlayıcı değildir**. Prompt/konfigürasyon metni = rehberlik (olasılıksal). Hook'lar, programatik kapılar, CI kontrolleri, `allowed-tools` = kilit (deterministik).
- İçinde "must never / guaranteed / no exceptions" geçen her soru → cevap programatik mekanizmadır, ASLA CLAUDE.md talimatı değildir.

**Sınav tuzakları:**
- "Yeni takım arkadaşı repoyu klonladı ama kuralları almıyor" → kurallar user-level'a yazılmış; project-level'a taşı.
- "Claude oturumdan oturuma tutarsız davranıyor" → ilk adım `/memory`'dir; yeniden kurulum ya da temperature=0 DEĞİL.
- Temperature rastgeleliği kontrol eder, kurala uyumu değil — garanti/uyumluluk sorularında daimi yanlış cevap.
- Konfigürasyon **ileriye işler, geriye değil**: kural eklemek, kuraldan önce yazılmış dosyaları düzeltmez.
- Oturum **ortasında eklenen konfigürasyon** algılanmayabilir → bayat oturum envanteri; çözüm = taze oturum (Week 2'deki bayat bağlam kuralıyla aynı ilke).
- CLAUDE.md'yi kısa tut (≈ 200 satır altı); uzun dosyalar uyumu düşürür.
- **Talimat-gerçeklik kaymasına** dikkat: CLAUDE.md var olmayan şeylere referans veriyorsa (ör. olmayan bir .venv) dosyanın tamamına güven erozyona uğrar.
- Projeye özgü iş akışları (tasks/todo.md gibi dosya yolları) user-level hafızaya YAZILMAZ.

---

## 2. Path-scoped rules (TS 3.3)

**Sözdizimi:**
```markdown
---
paths:
  - "**/*.test.tsx"
  - "terraform/**/*"
---
# Kural içeriği buraya
```

**Glob anlamları:**
- `*` = TEK path seviyesinde herhangi bir şey (`*.py` = yalnızca o klasördeki .py dosyaları).
- `**` = herhangi bir klasör derinliği (`**/*.py` = repodaki tüm .py dosyaları). Bizim testte `**` sıfır ara klasörle de eşleşti.
- Birleşik: `week*/**/*.py` = adı "week" ile başlayan klasörler altındaki tüm .py dosyaları.

**Hangi durumda hangisi:**
- Repoya DAĞILMIŞ bir dosya TİPİ için konvansiyon (test dosyaları, .tf dosyaları) → path-scoped rule. Her klasöre CLAUDE.md kopyalamak DEĞİL (bakım kâbusu = klasik yanlış şık).
- Tek bir klasöre özgü kural → directory CLAUDE.md.
- Evrensel, her zaman geçerli standart → kök CLAUDE.md.

**A/B testiyle kanıtlandı:** `paths: ["week*/**/*.py"]` kuralı .py dosyasında tetiklendi ama AYNI klasördeki .md dosyasında tetiklenmedi → kurallar dosya desenine bağlanır, konuma değil.

**Tanıman gereken sınav ifadesi:** "conventions must apply automatically based on file paths regardless of directory location" → `.claude/rules/` + glob frontmatter.

---

## 3. Custom slash commands ve skills (TS 3.2)

**Commands:**
- `.claude/commands/<isim>.md` dosyası → `/<isim>` olarak çağrılır. DOSYA ADI komutun adıdır.
- `$ARGUMENTS` yer tutucusu, komuttan sonra yazılan her şeyi alır.
- Frontmatter: `description` (ne yapar), `argument-hint` (çağırırken arayüzde görünen "buraya ne yazacağım" ipucu).
- Proje kapsamı `.claude/commands/` = git ile paylaşılır ("takım geneli /review komutu" sorularının cevabı). Kişisel kapsam `~/.claude/commands/` = sadece sen.
- Var olmayan tuzak cevap: `.claude/config.json` içinde commands dizisi. Ayrıca: komutlar CLAUDE.md'nin İÇİNE yazılmaz.

**Skills:**
- `.claude/skills/<isim>/SKILL.md` klasör yapısı, frontmatter:
  - `context: fork` → İZOLE yan bağlamda çalışır; ayrıntılı/gürültülü çıktı orada kalır, ana sohbete yalnızca özet döner. Gürültülü/keşif amaçlı skill'ler için (codebase analizi, beyin fırtınası).
  - `allowed-tools` → skill'in kullanabileceği araçlara sert kısıt. Salt-okunur denetçi: `Read, Grep, Glob`. Bu bir KİLİTTİR, rica değil — listede Write yoksa yazmak fiziken imkânsızdır.
  - `argument-hint` → çağırana parametre ipucu.
- Kapsamlı Bash sözdizimi: `Bash(git status:*)` = Bash'in tamamı değil, yalnızca o komut ailesi.
- Takım skill'inin kişisel varyantı → `~/.claude/skills/` altına FARKLI İSİMLE (aynı isim çakışma/karışıklık yaratır).

**Yerleşim karar tablosu (sürekli sorulur):**

| İhtiyaç | Mekanizma |
|---|---|
| Evrensel standart, her oturum | kök CLAUDE.md |
| Klasöre özgü kural | directory CLAUDE.md |
| Dosya TİPİNE özgü, dağınık dosyalar | .claude/rules + paths |
| İstek üzerine görev/iş akışı | command veya skill |

**Drill maddesi (bir kez kaçırıldı!):**
- `paths` = **yükleme koşulu** (rules): talimatın context'e ne zaman GİRECEĞİNİ kontrol eder.
- `context: fork` = **çıktı izolasyonu** (skills): üretilen ÇIKTININ nereye gideceğini kontrol eder.
- "Skill'in ürettiği ayrıntılı çıktı sohbeti kirletiyor" → `context: fork`; paths DEĞİL.

**İş akışı deseni:** denetle → düzelt → yeniden denetle. Denetçi (salt-okunur skill) bulur; ANA oturum senin onayınla düzeltir; denetçi doğrular. Domain 4'teki validation döngüleriyle aynı aile.

---

## 4. Plan mode vs direct execution (TS 3.4)

**Görev tanımında şunlar varsa PLAN MODE:** büyük ölçekli değişim, 45+ dosya, birden çok geçerli yaklaşım, mimari kararlar, servis sınırları, kütüphane migrasyonu, "entegrasyon yaklaşımları arasında seçim".
**Şunlarda DIRECT EXECUTION:** tek dosya, net stack trace, kapsamı belli küçük değişiklik (tek validation kontrolü, tek bug fix).

**Anahtar gerçekler:**
- Plan mode = salt-okunur keşif + yapılandırılmış plan + ONAY KAPISI. Onaylayana kadar: sıfır dosya değişikliği (Esc/ret → `git status` temiz).
- Melez akış meşrudur ve kılavuz onaylıdır: plan mode ile araştır/tasarla → onayla → direct execution ile uygula.
- CLI'da `Shift+Tab` modlar arasında döner.
- **Explore subagent**: ayrıntılı keşif çıktısını izole eder, ana context'i korumak için özet döndürür; PARALEL çalışabilir (aynı anda birden çok Explore). Keşfeder — DÜZELTMEZ.
- Bilgi eksikken doğru plan-mode davranışı: **blocker olarak işaretle + hedefli sorular sor** — eğitim verisinden UYDURMAK ya da sessizce ikame etmek DEĞİL.

**Katil tuzak (kılavuz örnek Soru 5):** karmaşıklık görevde zaten yazılıyken "direct başla, karmaşıklık çıkarsa plan'a geç" YANLIŞTIR. **Belirtilmiş karmaşıklık girdidir, sürpriz değildir.** Geç keşif = pahalı rework.
- Ayna tuzak: önemsiz tek dosyalık düzeltme için plan mode dayatmak da YANLIŞTIR (gereksiz tören).

---

## 5. Iterative refinement (TS 3.5)

**Dört desen:**
1. **Somut örnek > düzyazı.** Dönüşüm gereksinimlerinde 2–3 girdi→çıktı örneği ver (geçersiz girdi→None/kenar durumu örneği dahil). Düzyazı tarifler tutarsız yorumlanır; düzyazıyı uzatmak genelde çözmez.
2. **Test-driven iterasyon.** ÖNCE testleri yaz (beklenen davranış + kenar durumları), sonra başarısız test çıktısını paylaşarak ilerle. Kırmızı test = nesnel, sayılabilir geri bildirim ("2 test kırmızı") vs öznel ("beğenmedim"). Kırmızı → kök neden → düzeltme → yeşil.
3. **Interview pattern.** Yabancı alanlarda, implementasyondan ÖNCE Claude'a SORU SORDUR (cache invalidation, failure mode'lar = kılavuzun kendi örnekleri). Öngörmediğin tasarım kararlarını yüzeye çıkarır.
4. **Aşçı kuralı (toplu vs sıralı):** ETKİLEŞEN düzeltmeler → tek detaylı mesajda birlikte. BAĞIMSIZ düzeltmeler → sırayla. Önce sınıflandır: "bu sorunlar birbirine değiyor mu?"
   - Örnek: cache anahtarında kullanıcı ID eksik + TTL oturumdan uzun = etkileşiyor (birlikte); değişken adında yazım hatası = bağımsız (ayrı).

**Gözlemlenen ders:** muğlak prompt'lar modelin SESSİZ varsayımlarıyla dolar (ValueError vs None sözleşmesi). Testler gizli varsayımları görünür çatışmaya çevirir.
- Domain 4 köprüsü: başarısız test çıktısını paylaşmak = retry-with-error-feedback (retry prompt'una spesifik hatayı eklemek).

---

## 6. CI/CD'de Claude Code (TS 3.6)

**CLI bayrakları:**
- `-p` / `--print` → etkileşimsiz mod: prompt'u işler, stdout'a basar, ÇIKAR. "CI job'ı girdi bekleyerek askıda kalıyor" sorusunun cevabı (kılavuz örnek Soru 10).
- VAR OLMAYAN sahte bayraklar (klasik çeldiriciler): `CLAUDE_HEADLESS=true`, `--batch`.
- `--output-format json` → makine tarafından ayrıştırılabilir zarf (alanlar: `result`, `structured_output`, `total_cost_usd`, `num_turns`, `session_id`...).
- `--json-schema` → bulguları SENİN şemana zorlar (file/severity/issue/fix → bot PR'a inline yorum basabilir). Dosya yolu DEĞİL, SATIR İÇİ JSON alır: `--json-schema "$(cat schema.json)"`.
- Serbest metin + regex kazıma = yanlış cevap; yapı istiyorsan yapıyı zorla, sonradan kazıma.

**Bağımsız hakem instance'ı (aynı zamanda Domain 4 TS 4.6):**
- Kodu üreten oturum, üretim muhakemesini TAŞIR → kendi kararlarını sorgulamaya daha az meyillidir. Self-review talimatları ve extended thinking bunu ÇÖZMEZ.
- Bağımsız instance (önceki muhakeme bagajı yok) üreticinin kaçırdığını yakalar. Her `claude -p` çağrısı doğal olarak taze bir instance'tır.
- Canlı kanıt: taze hakem, üretici oturumun geride bıraktığı docstring-kod sözleşme boşluğunu + eksik konvansiyon satırlarını yakaladı.
- Meta-ders: rehberlik SESSİZCE başarısız olur; doğrulama katmanları (denetçi skill, bağımsız hakem, pytest, CI) yakalar.

**Bağlam ve tekrar-önleme ilkeleri:**
- CI-Claude takım standartlarını bilir çünkü **CLAUDE.md commit'lidir** — repoyu klonlamak el kitabını getirir. (Review kriterleri, test standartları, fixture'lar → oraya yaz.)
- Yeni commit sonrası yeniden review → ÖNCEKİ BULGULARI ver, yalnızca yeni/çözülmemiş sorunları iste (mükerrer yorum olmasın).
- Test üretimi mükerrer senaryo öneriyorsa → MEVCUT TEST DOSYALARINI ver.
- Tek ilke, iki yüz: **tekrarı önlemek için geçmişi göster.**

**Gerçek dünya notları:**
- `-p` bile yerel hafıza dosyalarını okur (hakemimiz user-level hafıza yüzünden Türkçe cevap verdi!) → CI prompt'unda çıktı dilini/biçimini açıkça sabitle.
- Her review koşusu para harcar (gözlemlenen: $0.44) → ölçeklemeden önce örneklem üzerinde rafine et (Domain 4 batch stratejisine köprü).

---

## 7. Hızlı tuzak listesi (son dakika tekrarı)

- "Guaranteed / must never" → hook/kapı/allowed-tools; asla prompt metni. Temperature asla cevap değildir.
- Yeni takım arkadaşı kuralları almıyor → user-level vs project-level.
- @import token tasarrufu sağlar → YANLIŞ.
- `paths` içermeyen rule'lar → koşulsuz yüklenir.
- `/memory` açılışta directory CLAUDE.md / path rules göstermiyor → normal, onlar koşullu.
- Oturum ortası konfigürasyon değişikliği algılanmıyor → taze oturum.
- Takım /review komutu → repoda `.claude/commands/`. config.json commands dizisi diye bir şey yok.
- Skill yazamamalı → Write içermeyen `allowed-tools` (kilit); "lütfen yazma" cümlesi değil.
- Ayrıntılı skill çıktısı → `context: fork`. Dağınık dosya-tipi konvansiyonları → `paths` glob'ları. Bu ikisini karıştırma.
- Belirtilmiş karmaşıklık → baştan plan mode.
- Explore subagent keşfeder ve özetler; düzeltmez.
- CI askıda → `-p`. Yapılandırılmış CI çıktısı → `--output-format json` + `--json-schema` (satır içi).
- Self-review zayıftır çünkü muhakeme bagajı taşınır → bağımsız instance.
- Mükerrer review yorumu / mükerrer test önerisi → önceki bulguları / mevcut testleri ver.
