# 🔴 Benchmark Raporu: TokenJar OLMADAN (Standart AI Asistanı)

Bu raporda, TokenJar kullanılmadan standart bir yapay zekâ kodlama asistanının (`view_file`, `cat`, ham terminal) aynı 5 geliştirici görevinde tükettiği **gerçek, doğrulanmış BPE token miktarları** yer almaktadır.

Hesaplama Motoru: `tiktoken (cl100k_base - OpenAI / Claude tokenizer standardı)`

---

## 📊 Özet Tüketim Tablosu

| Görev | İşlem Türü | İncelenen Dosya / Çıktı | Ham BPE Token |
| :--- | :--- | :--- | :---: |
| **Görev 1** | Kilit Dosyası İnceleme | `Cargo.lock` (4.356 satır) | **20,009** |
| **Görev 2** | Büyük Dosyada Fonksiyon İnceleme | `src/tokenjar/hooks/manager.py` (870 satır) | **8,182** |
| **Görev 3** | Birim Test Çalıştırma | `pytest tests/test_config.py -v` (Ham Log) | **267** |
| **Görev 4** | Aynı Oturumda Dosyayı Tekrar Okuma | `pyproject.toml` (2. Okuma) | **564** |
| **Görev 5** | Sembol Arama (Blast Radius) | `filter_output_logic` (Çoklu Dosya) | **591** |
| **TOPLAM** | **5 Temel Geliştirici Görevi** | - | **29,613 Token** |

---

## 📝 Görev Bazlı Ham İçerik Detayları

### Görev 1: Cargo.lock (Ham Okuma)
- **Token Sayısı:** 20,009 BPE token
- **Açıklama:** Standart asistan dosyayı baştan sona bağlam penceresine indirir. Model 4.356 satırlık bağımlılık listesini hafızasına almak zorunda kalır.

### Görev 2: src/tokenjar/hooks/manager.py (Ham Okuma)
- **Token Sayısı:** 8,182 BPE token
- **Açıklama:** Asistan sadece `ensure_in_user_path` fonksiyonunu ararken dosyanın tamamını (870 satır) bağlama yükler.

### Görev 3: pytest test_config.py -v (Ham Çıktı)
- **Token Sayısı:** 267 BPE token
- **Açıklama:** Geçen bütün testlerin tek tek log satırları ve ortam bilgileri ham olarak bağlama aktarılır.

### Görev 4: pyproject.toml (Tekrarlanan Okuma)
- **Token Sayısı:** 564 BPE token
- **Açıklama:** Dosya değişmediği halde asistan aynı dosyanın 80 satırını ikinci kez baştan sona okur.

### Görev 5: filter_output_logic Sembol Araması
- **Token Sayısı:** 591 BPE token
- **Açıklama:** Asistan sembolün nerede tanımlandığını bulmak için birden fazla dosyanın kaba içeriğini tarar.
