# 📌 Week 2 El Notu — Agent SDK & Multi-Agent Orchestration

## 1. Agent SDK Nedir? (Ham API'den farkı)
- **Ham API (Week 1):** agentic loop'u SEN yazarsın — tam kontrol, tek atımlık çağrılar.
- **Agent SDK:** aynı loop'u SDK yönetir; Claude Code'un motorunun ta kendisi. Hazır tool cephanesi (Read, Write, Bash, Grep, Glob, WebSearch, **Task**), hook'lar, session'lar, subagent orkestrasyonu kutudan çıkar.
- **`query()` vs `ClaudeSDKClient`:** query() = her çağrıda YENİ session, tek atımlık görevler. ClaudeSDKClient = aynı session'da çok turlu konuşma, interrupt desteği. Sınav kalıbı: "one-off task" → query(), "continuing conversation" → client.
- SDK **asenkron** çalışır: `async def` (tanım), `await` (beklerken donma), `asyncio.run(main())` (giriş kapısı), `async for` (akan mesajları teker teker yakala).
- Mesaj akışı tipleri: `SystemMessage(init)` (donanım listesi: tools, agents, model), `AssistantMessage` (content blokları), `UserMessage` (tool_result'lar burada döner — Week 1 kuralı yaşıyor!), `ResultMessage` (özet: stop_reason, num_turns, total_cost_usd, session_id).

## 2. Subagent'lar — Hub-and-Spoke (Şef ve İstasyonlar)
- **Mimari:** koordinatör (hub) tüm iletişimi, hata yönetimini, bilgi akışını yönetir; subagent'lar (spoke) birbirleriyle DOĞRUDAN konuşmaz. Orkestrasyon merkezde kalır.
- **Task tool = spawn mekanizması.** Subagent çağırmak sıradan bir tool çağrısıdır (fiş!). Koordinatörün Task tool'una erişimi yoksa spawn FİZİKSEL olarak imkânsız. Sınav cümlesi: *"allowedTools must include 'Task'."*
- (Saha notu: yeni CLI akışta bu tool'u `Agent` adıyla gösterebilir — mekanizma aynı, sınavda adı **Task**.)
- **Tanım:**

~~~python
subagents = {
    "web-researcher": AgentDefinition(
        description="Ne zaman bana is ver - KOORDINATOR bunu okuyup secer",
        prompt="Subagent'in kendi system prompt'u (kimligi)",
        tools=["WebSearch"],   # [] = hicbir tool; OMIT edersen HEPSINI miras alir!
        model="haiku",         # istasyon basina farkli motor olabilir
    ),
}
options = ClaudeAgentOptions(model="claude-sonnet-4-6", agents=subagents, allowed_tools=["Task"])
~~~

- ⚠️ **AgentDefinition alanları camelCase** (`maxTurns`, `disallowedTools`, `permissionMode`) — ClaudeAgentOptions ise snake_case (`max_turns`). Karıştırırsan TypeError.
- **Koordinatör istasyonu `description`'a bakarak seçer** — tool description kalitesi ilkesinin ajan düzeyindeki karşılığı.

## 3. Context İzolasyonu ⭐ (sınavın en sevdiği gerçek)
- **Subagent, parent'ın konuşma geçmişini OTOMATİK DEVRALMAZ.** İzole bir context'te doğar; evreni Task fişinin `prompt` alanından ibarettir.
- Context tek yolla taşınır: **koordinatör, bilgiyi fişin içine ELLE yazar.** (Canlı kanıtımız: "Enes" ismi ancak koordinatör Task prompt'una yazdığı için subagent'a ulaştı.)
- Belirti eşleştirme (sınav taktiği): rapor/çıktı **tamamen ilgisiz** → context fişe yazılmamış. Çıktı ilgili ama **dağınık** → format/şema sorunu.
- İleri seviye: sadece yazmak yetmez, **yapı** korunmalı → içerik ile metadata'yı (source URL, doküman adı, tarih) ayıran **structured format** kullan; synthesis claim-source eşleşmelerini korumalı. Düz metin yığını = attribution ölür.

## 4. Parallel Spawn
- Tanım: koordinatörün **TEK cevabında birden fazla Task tool çağrısı** emit etmesi. (Thread/subprocess açmak DEĞİL — o hub-and-spoke'u bozar.)
- Sonuçlar `tool_use_id` ile eşleşir (fiş takip numarası). RETURN'ler `UserMessage` içinde `ToolResultBlock` olarak döner.
- Kanıt işaretleri: iki SPAWN art arda (araya RETURN girmeden) = paralel; duration_ms'ler örtüşür → toplam süre ≈ en yavaş olan.
- `parent_tool_use_id`: mesajda kimin konuştuğunu söyler — None = koordinatör, dolu = o fişin doğurduğu subagent.

## 5. Scoped Tools (rol bazlı tool kısıtlama)
- İlke: **her ajana yalnızca rolünün gerektirdiği tool'lar.** Rolü dışında tool'u olan ajan onu YANLIŞ KULLANMAYA meyillidir (klasik örnek: synthesis ajanının kendi başına web araması yapıp doğrulanmamış içerik eklemesi).
- Çözüm sıralaması: prompt'a "arama yapma" yazmak = rica (probabilistic). `tools=[]` = kilit (deterministic). **Yapamadığı şeyi yanlış kullanamaz.**
- Çok tool da zehir: bir ajana 15-18 tool vermek seçim güvenilirliğini düşürür. İdeal: rol başına 4-5.
- Yüksek frekanslı basit ihtiyaç için **scoped cross-role tool** verilebilir (ör. synthesis'e dar bir verify_fact); karmaşık vakalar koordinatör üzerinden.

## 6. Hooks — Mutfaktaki Gıda Müfettişi ⭐
- Hook = SDK loop'unun resmi müdahale noktası; **kodda yaşar, model ikna edemez.** Prompt = rehberlik (probabilistic), hook = kilit (deterministic). Para/güvenlik/compliance → HER ZAMAN kilit.
- **PreToolUse:** fiş yazıldıktan SONRA, çalıştırılmadan ÖNCE tetiklenir. Kullanım: politika ihlalini blokla (ör. $500 üstü iade → deny + insana eskalasyon).
- **PostToolUse:** tool çalıştı, sonuç MODELE ULAŞMADAN önce. Kullanım: heterojen veriyi normalize et (Unix timestamp / ISO 8601 / "07/23/2026" karmaşası → tek format).
- Pre/Post seçim mantığı: "hiç olmamalı" → Pre (önleme); "olsun ama düzelt" → Post (dönüştürme). PostToolUse ile parayı geri almak = telafi, önleme DEĞİL — sınavda yanlış şık.
- Kayıt ve dönüş şekilleri:

~~~python
async def refund_guard(input_data, tool_use_id, context):
    amount = input_data["tool_input"].get("amount", 0)
    if amount > 500:
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Policy: >$500 needs a human. Tell the customer it's escalated.",
        }}
    return {}  # bos dict = itiraz yok, gec

options = ClaudeAgentOptions(hooks={
    "PreToolUse": [HookMatcher(matcher="mcp__support__process_refund", hooks=[refund_guard])],
})
~~~

- **deny reason MODELE GERİ İLETİLİR** → model neden durdurulduğunu öğrenir, müşteriye uygun eskalasyon mesajı yazar. Kilit kodda, iletişim modelde.
- Kendi tool'unu tanımlama (Week 3 fragmanı): `@tool("ad", "description", {"param": tip})` + `create_sdk_mcp_server(name="support", tools=[...])`. Tool adı üç parçalı olur: **`mcp__<sunucu>__<tool>`**.

## 7. Sessions — resume / fork / taze başlangıç ⭐
- Her query() yeni session açar; SDK konuşmayı diske kaydeder (`session_id`).
- **Karar ağacı (ezberle):**
  - Context GEÇERLİ + kaldığın yerden devam → **resume** (`resume=sid`; CLI: `--resume`). Aynı session_id geri gelir, hafıza yerinde.
  - Context GEÇERLİ + aynı temelden FARKLI yönler deneyeceksin → **fork** (`resume=sid, fork_session=True`). YENİ session_id; orijinal bozulmaz. Kullanım: iki stratejiyi bağımsız karşılaştırmak (aynı konuşmada ikisini tartışma — ilki ikincisini kirletir).
  - Context BAYAT (dosyalar değişti, tool sonuçları eski) → **ne resume ne fork**: YENİ session + yapılandırılmış özeti ilk prompt'a enjekte et. Bayat tool sonuçlarına güvenme; "dikkatli ol" uyarısı çözmez.
  - Ölçek nüansı: birkaç belirli dosya değiştiyse resume + "şu dosyaları yeniden analiz et" savunulabilir; büyük refactor (30+ dosya) → taze başlangıç.
- Kalıcı hafıza (CLAUDE.md, memory) session geçmişinden AYRI mekanizmalardır (Week 4 konusu).

## 8. Koordinatör Tasarımı
- Prompt'a **hedef + kalite kriteri** yaz, adım adım reçete DEĞİL. Sabit pipeline ("her zaman search→analysis→synthesis") = basit sorguda israf, karmaşıkta esneklik kaybı. Doğrusu: koordinatör sorguyu analiz edip hangi subagent'ların gerektiğine **dinamik** karar verir.
- **Too-narrow decomposition riski:** koordinatör konuyu dar dilimlere bölerse kapsam delik kalır (örnek: "creative industries" → sadece görsel sanatlar). Kök neden koordinatörde aranır, subagent'larda değil (örnek sınav sorusu 7).
- Karar yetkisini subagent'lara dağıtmak da yanlış — orkestrasyon merkezde.
- **Handoff fidelity:** koordinatör, synthesis çıktısını sunarken süsleyip genişletebilir → doğrulanmamış ekleme riski. Gerekirse "raporu OLDUĞU GİBİ sun" kuralı ekle.
- Structured findings formatı: her bulgu = claim + source_title + source_url + publication_date. Tarihler taşınmalı ki zaman farkları çelişki sanılmasın (Week 6 provenance temeli).

## 9. Maliyet & Prompt Caching (sınavda detay sorulmaz, "var ve ne işe yarar" yeter)
- Ajan altyapısı (system prompt + tool tanımları, ~19K token) ilk çağrıda cache'e YAZILIR (`ephemeral_5m` = 5 dk ömür). Yazma ≈ 1.25x, okuma ≈ 0.1x normal fiyat → 5 dk içinde tekrar ≈ 10x ucuz.
- Prefix'in HERHANGİ bir parçası değişirse (options, tools, model) cache tutmaz.
- Mimari refleks: pahalı model koordine eder (sonnet), ucuz modeller ayak işi yapar (haiku).

## 10. Hızlı Tuzak Listesi (60 saniyelik tekrar)

| Soru kalıbı | Refleks cevap |
|---|---|
| Subagent nasıl spawn edilir? | **Task tool** çağrısıyla; koordinatörde Task erişimi ŞART |
| Koordinatör hiç spawn etmiyor? | ÖNCE mekanik katman: Task tool erişilebilir mi? (description kalitesi sonra) |
| Subagent parent context'i bilir mi? | HAYIR — sadece Task prompt'una yazılanı bilir |
| Paralel subagent nasıl? | TEK cevapta çoklu Task çağrısı (thread değil!) |
| Synthesis kendi başına arama yapıyor? | Tool setini kısıtla (tools=[]) — prompt ricası yetmez |
| $X üstü işlem asla olmamalı? | **PreToolUse hook** ile blokla + eskalasyon (PostToolUse ile geri almak = yanlış) |
| Farklı tarih/veri formatları karışıyor? | **PostToolUse hook** ile modele ulaşmadan normalize et |
| Devam / dallanma / bayat context? | resume / fork_session=True / YENİ session + özet enjeksiyonu |
| Sabit pipeline mı dinamik seçim mi? | Dinamik: koordinatör sorguya göre subagent seçer |
| Rapor kaynaksız/karışık atıflı? | Structured claim-source mapping; içerik-metadata ayrımı |
