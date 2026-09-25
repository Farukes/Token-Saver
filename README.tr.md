<p align="right">
  <a href="README.md"><b>English</b></a> | <a href="README.tr.md"><b>Türkçe</b></a>
</p>

# 🔋 Token-Saver

[![CI](https://github.com/Farukes/Token-Saver/actions/workflows/ci.yml/badge.svg)](https://github.com/Farukes/Token-Saver/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Zero Telemetry](https://img.shields.io/badge/telemetri-0%25%20(100%25%20yerel)-success.svg)](#-kurumsal-gizlilik-ve-g%C3%BCvenlik-garantisi)

**Yapay zeka kodlama asistanları için işlevsellikten ödün vermeden %70-95 token tasarrufu sağlayan MCP sunucusu.**

Token-Saver, yapay zeka kodlama asistanınız ile kod tabanınız arasında yer alarak kod okumalarını, terminal çıktılarını ve dosya işlemlerini akıllıca sıkıştırır; token tüketimini, bağlam sıkıştırmasını (context compaction) ve gecikmeyi önemli ölçüde azaltır.

**Claude Code**, **Cursor**, **Antigravity (AGY)**, **Windsurf**, **Continue.dev** ve tüm MCP uyumlu yapay zeka asistanlarıyla sorunsuz çalışır.

---

## ✨ Özellikler ve Mimari

| Modül | Ne Yapar | Token Tasarrufu |
|:---|:---|:---|
| 🦴 **Kod İskeleti Çıkarıcı (Code Skeletonizer)** | Tree-sitter AST ile yapısal iskelet (imzalar, tipler, docstring'ler) çıkarır | **%80-95** |
| 📖 **Akıllı Dosya Okuyucu (Smart File Reader)** | L1 RAM + L2 Kalıcı SQLite önbelleği, diferansiyel okuma ve diff başlıkları | **%90-99** |
| 🛡️ **Lockfile ve Statik Varlık Kalkanı** | Devasa kilit dosyalarını ve minify edilmiş paketleri yakalayarak cerrahi sürüm sorgusu (`query="react"`) sunar | **%99** |
| 🎯 **Etki Alanı ve Sembol Analizi** | Anlık global sembol arama ve dosyalar arası referans/çağıran takibi (`find_symbol_references`) | **%85-95** |
| 🖥️ **Terminal Budayıcı (Terminal Pruner)** | Test/derleme/git terminal akışlarını sıkıştırır, hataları ve özet bilgileri korur | **%60-90** |
| 🗺️ **Repo Haritası (Repo Map)** | PageRank ve Graf Merkeziliği algoritmalarıyla özel token bütçelerine sığdırılan kod haritası | **Bütçeye uyarlanmış** |
| 🎨 **İsteğe Bağlı Kontrol Paneli (UI)** | **Sıfır Arka Plan RAM** tüketen hafif bağımsız kontrol paneli (`token-saver ui`) | **Anlık** |
| ⚡ **Tek Tıkla IDE Yapılandırması** | Cursor, Windsurf, Claude, VS Code için otomatik yapılandırma ve zararsız geri alma | **Zahmetsiz** |

### 🛡️ Yerleşik Güvenlik Önlemleri ve Güvenilirlik
- **Lockfile ve Devasa Varlık Kalkanı:** 50.000 satırlık kilit dosyalarının bağlam penceresini yok etmesini engeller; 5 satırlık cerrahi sürüm sorgularını destekler.
- **L1 RAM + L2 SQLite Kalıcı Önbellek:** MCP sunucusu ve IDE yeniden başlatmalarından etkilenmez (`~/.token-saver/cache.db` WAL moduyla çalışır).
- **Güvenli Hata Geri Dönüşü (Fallback Safety Guard):** Test veya komut başarısız olduğunda (`exit_code != 0`), Token-Saver traceback'lerin ve hata bağlamının eksiksiz korunmasını garanti eder.
- **Küçük Dosya Anomali Koruması:** Diff başlığı dosyanın kendisinden daha fazla token tüketecekse, token şişmesini önlemek için dosyanın tam içeriği döndürülür.
- **Kontrolsüz Akış Koruması (Runaway Stream Protection):** Sonsuz döngülerde ham terminal arabelleklerini 2 MB ile sınırlandırarak bellek taşmasını önler.
- **SQLite Veritabanı Şişme Koruması:** 5 MB'tan büyük dosyalar disk alanını şişirmemek için karma referansıyla (hash) önbelleğe alınır.

---

## 🚀 Hızlı Başlangıç

### Kurulum

```bash
git clone https://github.com/Farukes/Token-Saver.git
cd Token-Saver
pip install -e .
```

### Yönlendirme Kurallarını Otomatik Yapılandırma

Token-Saver optimizasyon yönergelerini depo kurallarınıza otomatik olarak ekleyin:

```bash
# Kuralları AGENTS.md, .cursorrules, .windsurfrules ve CLAUDE.md dosyalarına enjekte eder
token-saver init-rules
```

### 🎛️ Çıktı Optimizasyonu Kontrolleri (CLI ve Terminaller)

Kompakt cerrahi diff çıktısı ile varsayılan sınırsız çıktı arasında net komutlarla geçiş yapın:

```bash
# 🟢 Kompakt cerrahi diff'leri ve sıfır kesinti kalite kuralını etkinleştirir
token-saver output on

# ⚪ Yapay zeka asistanını varsayılan kısıtlamasız çıktı ayarlarına döndürür
token-saver output off

# 📊 Mevcut çıktı yapılandırma durumunu görüntüler
token-saver output
```

Yapay zeka asistanınızın sohbet ekranında slash komutları da desteklenir (`/token-saver output on`, `/token-saver output off`).

---

## 🔌 Yapay Zeka Asistanınızla Kurulum

### ⚡ Tek Tıkla Otomatik Kurulum (Önerilen)

Claude Desktop, Cursor, Windsurf, Claude Code ve VS Code ortamlarını otomatik olarak algılar ve otomatik yedeklemeyle Token-Saver MCP sunucusunu yapılandırır:

```bash
# 🟢 Algılanan tüm IDE'leri tek bir komutla yapılandırın
token-saver install-mcp

# ⚪ İstediğiniz zaman güvenle geri alın (eklediğiniz diğer sunucuları aynen korur!)
token-saver uninstall-mcp
```

### Manuel Yapılandırma

Manuel olarak yapılandırmayı veya diğer istemcileri kullanmayı tercih ederseniz:

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add token-saver -- python -m token_saver
```
</details>

<details>
<summary><b>Cursor</b></summary>

`.cursor/mcp.json` dosyasını oluşturun veya güncelleyin:
```json
{
  "mcpServers": {
    "token-saver": {
      "command": "python",
      "args": ["-m", "token_saver"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```
</details>

<details>
<summary><b>Antigravity (AGY)</b></summary>

`~/.gemini/config/mcp_config.json` dosyasına ekleyin:
```json
{
  "mcpServers": {
    "token-saver": {
      "command": "python",
      "args": ["-m", "token_saver"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```
</details>

<details>
<summary><b>Windsurf / Cascade</b></summary>

`~/.codeium/windsurf/mcp_config.json` dosyasına ekleyin:
```json
{
  "mcpServers": {
    "token-saver": {
      "command": "python",
      "args": ["-m", "token_saver"]
    }
  }
}
```
</details>

<details>
<summary><b>Continue.dev</b></summary>

`.continue/config.yaml` dosyasına ekleyin:
```yaml
mcpServers:
  - name: token-saver
    command: python
    args: ["-m", "token_saver"]
```
</details>

---

## 🛠️ Kullanılabilir MCP Araçları

- **`find_symbol_global(query, root_path=".", exact=False)`**: Birden fazla dosyayı okumaya gerek kalmadan kod tabanının tamamında fonksiyon, metot veya sınıfları isme göre arar.
- **`find_symbol_references(symbol_name, root_path=".", max_results=25)`**: Etki alanı (blast radius) referans analizi. Kod düzenlemeden veya yeniden yapılandırmadan (refactor) önce kod tabanındaki tüm çağıranları, import'ları ve kullanımları bulur.
- **`tool_get_code_skeleton(file_path)`**: Bir dosyanın yapısal iskeletini çıkarır — sınıflar, fonksiyon imzaları, docstring'ler ve tip açıklamaları korunur, gövdeler `...` ile değiştirilir. (Python, JS/TS, Go, Rust, Java, C/C++, C#, Ruby, PHP, Kotlin dillerini destekler).
- **`tool_get_symbol(file_path, symbol_name)`**: İskeleti inceledikten sonra belirli bir sınıf veya fonksiyonun tam uygulamasını isme göre getirir.
- **`read_file_smart(file_path, force_full=False, query="")`**: Oturum önbelleği ve Kilit Dosyası Kalkanı (Lockfile Shield) içeren diferansiyel dosya okuyucu. Değişmeyen dosyalarda `[CACHED] unchanged` (~3 token) veya birleşik diff döndürür. Kilit dosyaları (`package-lock.json`, `Cargo.lock` vb.) için 50.000 satır yerine cerrahi 5 satırlık sürüm blokları almak için `query="paket-adi"` parametresini destekler.
- **`run_command_smart(command, cwd=".")`**: Kabuk komutlarını çalıştırır ve pytest, jest, npm, cargo ile git çıktılarındaki gereksiz ayrıntıları budar.
- **`filter_output(output, output_type="auto")`**: Komut çalıştırmadan test çalıştırıcıları, derleme işlem hatları ve sürüm kontrol günlükleri için saf metin filtresi uygular.
- **`get_repo_map_tool(root_path=".", max_tokens=1000)`**: Dosyalar arası import ilişkilerine göre önceliklendirilmiş graf merkeziliği kod tabanı haritası.
- **`get_directory_tree_tool(root_path=".", max_depth=4)`**: `.gitignore` kurallarına uyan ve ikili (binary) dizinleri atlayan hafif dizin ağacı.
- **`cache_stats()`**: Oturum okuma isabetlerini (hit), ıskalamalarını (miss), diff'leri ve toplam token tasarrufunu inceler.

### 📦 MCP Kaynakları ve Komut İstekleri (Prompts)

- **Kaynaklar (Resources):**
  - `token-saver://stats`: Canlı kümülatif token ve maliyet tasarrufu paneli.
  - `token-saver://guide`: Yapay zeka asistanı en iyi uygulama optimizasyon yönergeleri.
  - `token-saver://config`: Etkin proje yapılandırması ve yoksayma ayarları.
- **Komut İstekleri (Prompts):**
  - `optimize_coding_task(task_description)`: Asistanları token verimli iş akışlarına yönlendiren sistem istemi şablonu.

---

## ⚙️ Proje Yapılandırması (`token-saver.toml`)

Hariç tutulacak dosyaları ve bütçeleri özelleştirmek için deponuzun kök dizininde isteğe bağlı bir `token-saver.toml` oluşturun:

```toml
[general]
ignore_patterns = ["tests/fixtures/*", "legacy/*", "*.bak"]
max_cacheable_bytes = 5242880 # 5 MB

[cache]
ttl_days = 30
max_entries = 5000

[repo_map]
default_budget = 1000
```

---

## 💻 CLI Komutları ve Kabuk Kancaları

Token-Saver, geliştiriciler ve yerel kabuk otomasyonu için etkileşimli bir komut satırı aracı olarak da işlev görür:

```bash
# 🎨 İsteğe Bağlı Kontrol Panelini Başlatın (Sıfır Arka Plan RAM Tüketimli UI)
token-saver ui

# 📊 Token-Saver'ın IDE'ler genelindeki kapsamlı canlı çalışma durumunu kontrol edin
token-saver status

# ⚡ Claude Desktop, Cursor, Windsurf, VS Code genelinde MCP'yi tek tıkla otomatik kurun
token-saver install-mcp

# ⚪ Token-Saver MCP yapılandırmasını güvenle kaldırın ve orijinal durumuna geri getirin
token-saver uninstall-mcp

# Kümülatif tasarruf panelini görüntüleyin (tasarruf edilen token, para ve işlem sayısı)
token-saver stats

# Herhangi bir kabuk komutunu akıllı filtreleme ile çalıştırın
token-saver run "pytest tests/ -v"
token-saver run "npm test"

# Geçici devre dışı bırakma: tam günlüklere ihtiyaç duyduğunuzda ham çıktının %100'ünü görün
RAW=1 token-saver run "pytest"
token-saver run "pytest --raw"

# L2 SQLite önbelleğindeki süresi dolmuş veya fazla kayıtları temizleyin
token-saver cache-prune --ttl-days 30 --max-entries 5000

# Şeffaf kabuk kancalarını yükleyin (pytest/npm çıktıları otomatik filtrelenir)
token-saver hook

# Tüm kabuk kancalarını güvenli ve temiz bir şekilde kaldırın
token-saver unhook

# Tüm yapay zeka asistanı yapılandırmalarına yönlendirme kurallarını yükleyin
token-saver init-rules

# AGY CLI ve Claude Code için /token-saver slash komutlarını kurun
token-saver setup-commands

# Metrik sayaçlarını sıfırlayın
token-saver reset-stats
```

---

## 🔒 Kurumsal Gizlilik ve Güvenlik Garantisi

Token-Saver kesinlikle **Sıfır-Telemetri, %100 Localhost** tasarım felsefesiyle geliştirilmiştir:

- **%100 Yerel Yürütme:** Tüm ayrıştırma (Tree-sitter), önbellekleme (SQLite) ve çıktı filtreleme işlemleri yerel olarak işlemcinizde (CPU) gerçekleşir.
- **Sıfır Dış Ağ Çağrısı:** Telemetri sunucusu, analitik izleyici, giden ping veya herhangi bir bulut bağımlılığı kesinlikle yoktur.
- **Air-Gapped / Çevrimdışı Ortamlarla Uyumlu:** Gizli, çevrimdışı veya izole kurumsal şirket ağlarında güvenle çalışır.
- **Yerel Veri İzolasyonu:** Kalıcı önbellek (`~/.token-saver/cache.db`) ve istatistikler (`~/.token-saver/telemetry.json`) yalnızca kullanıcı dizininizde bulunur ve `token-saver reset-stats` ile veya dizin silinerek istenildiği zaman tamamen temizlenebilir.
- **Müdahalesiz Mimari:** Yapay zeka asistanının açık talimatı olmadan proje kodunuzu asla değiştirmez.

---

## 🌍 Desteklenen Diller

Token-Saver, AST ayrıştırma için Tree-sitter kullanır ve kullanıma hazır olarak **130'dan fazla programlama dilini** destekler:

Python · TypeScript · JavaScript · Go · Rust · Java · C# · C / C++ · Ruby · PHP · Swift · Kotlin · Scala · Dart · Lua · Elixir · Haskell · ve daha fazlası.

---

## 🧪 Geliştirme ve Kalite Güvencesi

```bash
# Geliştirme bağımlılıklarıyla yükleyin
pip install -e ".[dev]"

# Tüm test paketini çalıştırın
pytest tests/ -v

# Kod kalitesi ve stil denetimleri
ruff check .
```

---

## 📄 Lisans ve Fikri Mülkiyet

Copyright © 2026 Ömer Faruk Eskitürk. Tüm hakları saklıdır.

Özel mülk yazılımdır. Bu kaynak kodun ve belgelerin izinsiz kopyalanması, tersine mühendisliği, yeniden dağıtılması veya değiştirilmesi kesinlikle yasaktır. Ayrıntılar için [LICENSE](LICENSE) dosyasına bakın.
