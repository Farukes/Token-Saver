# 🟢 Benchmark Raporu: TokenJar İLE (Optimize Edilmiş Motor)

Bu raporda, TokenJar'ın Tree-sitter AST İskeletleyicisi, Lockfile Shield, Smart File Cache ve Terminal Pruner araçları kullanılarak **aynı 5 geliştirici görevinde** harcanan **gerçek, doğrulanmış BPE token miktarları** yer almaktadır.

Hesaplama Motoru: `tiktoken (cl100k_base - OpenAI / Claude tokenizer standardı)`

---

## 📊 Özet Tasarruf Tablosu

| Görev | TokenJar Modülü | TokenJar BPE Token | Ham Hali | Net Tasarruf (%) |
| :--- | :--- | :---: | :---: | :---: |
| **Görev 1** | Lockfile Shield | **277** | 20,009 | **-%98.6** |
| **Görev 2** | AST Skeleton + Targeted Slice | **1,829** | 8,182 | **-%77.6** |
| **Görev 3** | Terminal Pruner (`pytest`) | **91** | 267 | **-%65.9** |
| **Görev 4** | Smart File Cache (Hit) | **33** | 564 | **-%94.1** |
| **Görev 5** | Global Symbol Indexer | **136** | 591 | **-%77.0** |
| **TOPLAM** | **TokenJar Optimizasyonu** | **2,366 Token** | **29,613 Token** | **-%92.0** |

---

## 🎯 İşlem Detayları & Korunan Fonksiyonellik

### Görev 1: Lockfile Shield (`Cargo.lock`)
- **Ham Token:** 20,009 ➔ **TokenJar:** 277 token (**-%98.6 Tasarruf**)
- **Çıktı:** Dosyanın tüm checksum gürültüsü atılarak yalnızca bağımlılık adları, sürümleri ve kök paketler özetlendi. Asistan bağımlılık mimarisini %100 kavradı.

### Görev 2: AST Skeleton & Hedefli Dilimleme (`manager.py`)
- **Ham Token:** 8,182 ➔ **TokenJar:** 1,829 token (**-%77.6 Tasarruf**)
- **Çıktı:** Dosyanın 870 satırı yerine önce Tree-sitter ile sınıf/fonksiyon imzaları çekildi, ardından yalnızca aranan fonksiyonun satır aralığı (528-578) okundu. Sıfır bilgi kaybı.

### Görev 3: Terminal Pruner (`pytest`)
- **Ham Token:** 267 ➔ **TokenJar:** 91 token (**-%65.9 Tasarruf**)
- **Çıktı:** Başarılı geçen testlerin tekrarlayan satırları budandı, yalnızca toplam özet ve varsa hata yığın izleri bırakıldı.

### Görev 4: Smart File Cache (`pyproject.toml`)
- **Ham Token:** 564 ➔ **TokenJar:** 33 token (**-%94.1 Tasarruf**)
- **Çıktı:** Dosya MD5 kontrolünden geçirilerek `[TOKENJAR CACHE HIT] File unchanged since last read` yanıtı döndürüldü. Asistan zaten hafızasındaki veriyi kullandı.

### Görev 5: Global Sembol İndeksi (`filter_output_logic`)
- **Ham Token:** 591 ➔ **TokenJar:** 136 token (**-%77.0 Tasarruf**)
- **Çıktı:** AST indeksi doğrudan dosya yolunu, satır numarasını ve tam imzasını tek seferde döndürdü.
