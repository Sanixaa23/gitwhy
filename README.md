# gitwhy

`gitwhy`, bir git komutu başarısız olduğunda hatayı tekrar etmez: deponun o anki durumunu
okur — hangi branch'tesin, kaç commit geride kaldın, hangi dosyalar çakışıyor, yarım kalmış
bir rebase var mı — ve o duruma özel düzeltme komutunu üretir. Eşleştirme deterministik,
LLM değil; ağ olmadan da çalışır. Yıkıcı komutları asla kendiliğinden çalıştırmaz, sadece
ne sileceğini yazarak gösterir. Senaryo eşleşme doğruluğu aşağıdaki tabloda ölçülmüştür.

> **Durum:** 12 senaryonun 12'si çalışıyor, 18 fixture ile ölçüldü. Eksik olan `--ai`
> modu ve `shell-init` doğrulaması.

![gitwhy: rebase çakışması, açıklama, düzeltme](docs/demo.gif)

Yukarıdaki kaydın tamamı gerçek çıktı — `python tools/demo.py` geçici bir depoyu
bozuk duruma sokar, komutları gerçekten koşar ve yakaladığı baytı çizer. Hiçbir satır
elle yazılmadı.

## Kurulum

Tek satır, bağımlılık yok:

```bash
pipx install git+https://github.com/<kullanici>/gitwhy
```

`pipx` yoksa `pip install git+https://github.com/<kullanici>/gitwhy` da çalışır; pipx
aracı kendi ortamına kurduğu için tercih edilir.

Kurulumu doğrula:

```bash
gitwhy --version
gitwhy doctor
```

Gereken: **Python 3.9+** ve **git 2.23+** (`git switch` önerileri bunu istiyor).
Çalıştırmak için başka hiçbir paket gerekmiyor — `pyproject.toml` içinde `dependencies`
boş. Ağ gerekmiyor, hesap gerekmiyor, yapılandırma gerekmiyor.

Kaynaktan geliştirme:

```bash
git clone https://github.com/<kullanici>/gitwhy
cd gitwhy
pip install -e ".[dev]"
python -m pytest -q
python tests/test_rules.py        # karışıklık matrisi
```

Geliştirme ve testler **git 2.28+** istiyor (`git init -b`). Demo GIF'ini üretmek için
ayrıca `pillow` gerekir.

Kurmadan denemek istersen:

```bash
PYTHONPATH=src python -m gitwhy.cli doctor
```

## Kullanım

```
gitwhy                           # son başarısız git komutunu açıkla
gitwhy explain --stderr hata.txt # verilen hata çıktısını açıkla (- = stdin)
gitwhy capture -- git push       # komutu koşar, başarısızsa açıklar
gitwhy doctor                    # depo sağlığı: upstream, user.email, sahnelenmiş sır
gitwhy shell-init bash           # git başarısız olunca otomatik devreye giren sarmalayıcı
```

`gitwhy doctor` tek bakışta deponun sorunlarını sıralar; kırmızı satırlar ele alınması
gerekenler:

![gitwhy doctor çıktısı](docs/doctor.svg)

Bu görüntü de elle alınmadı: `python tools/doctor_goruntu.py` dört ayrı sorunu olan
gerçek bir depo kurup `gitwhy doctor` koşuyor ve çıktının kendisini çiziyor.

## Senaryolar

| # | Senaryo | Durum | Tespit sinyali |
|---|---|---|---|
| 1 | Detached HEAD | ✅ | `# branch.head (detached)` **ve** sürmekte işlem yok |
| 2 | Merge çakışması | ✅ | `u ` satırları > 0 veya `MERGE_HEAD` |
| 3 | Rebase ortasında kalmış | ✅ | `.git/rebase-merge` veya `rebase-apply` |
| 4 | Cherry-pick / revert ortasında | ✅ | `CHERRY_PICK_HEAD` / `REVERT_HEAD` |
| 5 | Remote hiç yok | ✅ | `fatal: No configured push destination.` |
| 6 | Remote var, upstream yok | ✅ | `has no upstream branch` |
| 7 | Push reddedildi (geride kalmış) | ✅ | `! [rejected]` / `fetch first` (**`branch.ab` değil**) |
| 8 | Yanlış branch'e commit | ✅ | `! [remote rejected]` / `pre-receive hook declined` |
| 9 | `node_modules` sahnelenmiş | ✅ | staged yol parçası bağımlılık dizini |
| 10 | `.env` / anahtar sahnelenmiş | ✅ | staged dosya adı `.env`, `*.pem`, `id_rsa` |
| 11 | Yerel değişiklik checkout'u engelliyor | ✅ | `would be overwritten` |
| 12 | Kaybolmuş commit | ✅ | reflog'un son 10 girdisinde, hiçbir ref'ten erişilemeyen commit |

Kapsam burada duruyor. "Tüm git hatalarını çözer" diye bir iddia yok.

**Senaryo 8'in durum tabanlı hali bilerek yok.** "main'de gönderilmemiş commit var"
sinyali, tek başına çalışan birinin tamamen normal halinden ayırt edilemiyor —
`neg_main_ileride` fixture'ı bunu gösteriyor. Bu yüzden senaryo 8 yalnızca uzak tarafın
reddiyle tespit ediliyor. Yanlış pozitif vermemek, kapsamı genişletmekten önce gelir.

## Ölçülmüş senaryo doğruluğu

`tests/fixtures.py` her senaryo için **gerçek** bir git deposu kurar ve onu o bozuk duruma
sokar; kural motoru o depoyu okuyarak tahmin eder. Matris `python tests/test_rules.py`
çıktısıdır.

```
gercek \ tahmin     01   02   03   04   05   06   07   08   09   10   11   12  yok
01                   1    0    0    0    0    0    0    0    0    0    0    0    0
02                   0    1    0    0    0    0    0    0    0    0    0    0    0
03                   0    0    1    0    0    0    0    0    0    0    0    0    0
04                   0    0    0    2    0    0    0    0    0    0    0    0    0
05                   0    0    0    0    1    0    0    0    0    0    0    0    0
06                   0    0    0    0    0    1    0    0    0    0    0    0    0
07                   0    0    0    0    0    0    1    0    0    0    0    0    0
08                   0    0    0    0    0    0    0    1    0    0    0    0    0
09                   0    0    0    0    0    0    0    0    1    0    0    0    0
10                   0    0    0    0    0    0    0    0    0    1    0    0    0
11                   0    0    0    0    0    0    0    0    0    0    2    0    0
12                   0    0    0    0    0    0    0    0    0    0    0    2    0
yok                  0    0    0    0    0    0    0    0    0    0    0    0    3

12 senaryo, 18 fixture, 18/18 dogru eslesme (%100)
```

Son satır ve son kolon **negatif kontroller**: sorunsuz depo, `commit --amend` sonrası ve
main'de gönderilmemiş commit. Bu üçü hiçbir senaryoya eşleşmemeli; o köşegen hücresi
"yanlış pozitif vermedi" demek. Senaryo sayısından çok fixture olması, aynı senaryonun
farklı yollardan oluşmasından geliyor: cherry-pick ve revert aynı satıra düşer, checkout
ve merge engellenmesi aynı satıra düşer, `reset --hard` ve silinmiş branch aynı satıra
düşer.

Her PR'da GitHub Actions bu matrisi yeniden ölçer.

## Güvenlik

1. Araç hiçbir koşulda yıkıcı bir komutu kendiliğinden çalıştırmaz. Komutu ekrana yazar;
   kopyalama kararı kullanıcınındır.
2. `--run` seçeneği eklenirse yıkıcı komutlar listenin dışında kalır. Yalnızca geri
   alınabilir komutlar (`git switch`, `git stash push`, `git branch`) otomatik koşabilir.
3. Her öneri, o komutun neyi **kalıcı olarak** sileceğini açıkça yazar.
4. `tests/test_safety.py` bu kuralı test eder: yıkıcı komut içeren her şablonun uyarı
   satırı taşıdığını ve otomatik çalıştırma listesinde yıkıcı komut olmadığını doğrular.
   `context.py`'nin depoyu değiştiren hiçbir git komutu içermediği de testle garantidir.

## Mimari

```
capture.py   son başarısız komutu diske yazar / okur
context.py   salt-okunur git sorguları -> tek bir Baglam nesnesi
rules.py     (baglam, hata_metni) -> senaryo kimliği. Saf fonksiyon, I/O yok, LLM yok
explain.py   senaryo kimliği + baglam -> metin. scenarios/*.md şablonları
cli.py       argparse, 5 alt komut
```

Bağlamın çoğu tek komuttan gelir:

```
git status --porcelain=v2 --branch
```

Bu tek çağrı `branch.head` (detached ise literal `(detached)`), `branch.upstream`,
`branch.ab +ileri -geri` ve `u ` ile başlayan çakışan dosya satırlarını verir.

### Fixture testlerinde doğrulanan üç kural

**1. Rebase'i detached HEAD'den önce kontrol et.** Rebase çakışmasının ortasında
`git status` aynı anda `(detached)` *ve* `rebase-merge` gösterir. Detached'ı önce
kontrol eden bir motor, rebase'in ortasındaki kullanıcıya tamamen yanlış komut önerir.
Doğru sıra: sürmekte olan işlem → çakışma → hata metni → detached.
`test_rebase_detached_oncesinde_kontrol_ediliyor` bu sıranın bozulmasını yakalar.

**2. Hatanın ilk satırını okumak yetmez.** Merge çakışmasında git'in ilk çıktı satırı
`Auto-merging a.txt`; gerçek hata aşağıdadır. `rules.hata_satirlari()` tüm satırları
`CONFLICT`, `error:`, `fatal:`, `! [rejected]` için tarar.

**3. "Upstream yok" tek hata değil, iki ayrı durum.** Remote hiç tanımlı değilse git
`fatal: No configured push destination.` verir (senaryo 5); remote var ama branch'in
upstream'i yoksa farklı mesaj ve farklı çözüm (senaryo 6, `git push -u origin <branch>`).

**4. Reddedilen push'tan sonra "geride kaldın" sinyali YOK.** Git reddedilen bir push'tan
sonra uzak takip referansını güncellemiyor: `branch.ab` hâlâ `+1 -0` gösteriyor. Gerçek
geri sayısı ancak `git fetch` sonrası `-1` oluyor ve `context.py` fetch yapamaz (salt-okunur).
Bu yüzden senaryo 7 tek istisnadır: kararı durumdan değil hata metninden verir.
`test_reddedilen_pushta_geri_sayisi_sifir_gorunuyor` bunu kayıt altında tutuyor.

**5. `git check-ignore` sahnelenmiş yolda `--no-index` olmadan işe yaramaz.** Varsayılan
olarak check-ignore index'e bakar ve index'te olan bir yolu, kural eşleşse bile "ignore
edilmiyor" sayar. Senaryo 9 ve 10 tam olarak sahnelenmiş yolları sorguluyor; bu bayrak
olmadan sonuç her zaman boş çıkar ve "`.gitignore` kuralı var ama dosya yine de
sahnelenmiş" durumu hiç görülmez.

**6. Hata işaretçisi listesi bir kapı.** `rules.hata_satirlari()` yalnızca
`HATA_ISARETCILERI` içindeki bir parçayı taşıyan satırları geçirir; geçmeyen satırı
`esle()` hiç görmez. Korumalı branch reddinin satırı `! [remote rejected]`, ve bu ne
`"! [rejected]"` ne de `"[rejected]"` işaretçisine uyuyor — araya `remote ` giriyor. Kural
doğru yazılmış olmasına rağmen senaryo 8 sessizce hiç eşleşmedi. Kural: **işaretçiler en
gevşek parça olmalı (`rejected`), senaryo desenleri dar.**
`test_metin_tabanli_fixturelerin_satirlari_kapiyi_geciyor` bu sınıf hatayı yakalar.

**7. Erişilemeyen commit'i bulmanın salt-okunur yolu `rev-list --no-walk`.**
`git fsck --lost-found` `.git/lost-found` dizinini yazar, yani depoyu değiştirir.
`git rev-list --no-walk <shalar> --not --all` tek çağrıda, hiçbir şey yazmadan,
sınır koymadan aynı cevabı verir: listelenen commit'lerden hiçbir ref'ten
erişilemeyenler. `commit --amend` de eski commit'i erişilemez bırakır, ama bu kasıtlı
bir işlemdir — reflog'da bir üstteki girdi `commit (amend)` ise atlanıyor
(`neg_amend` fixture'ı bunu doğruluyor).

## Demo kaydını yeniden üretmek

GIF ve ekran görüntüleri depoda duruyor; değiştirmek istersen iki yol var.

**Windows dahil her yerde — kayıt programı (önerilen).** Adımlar
[tools/demo.py](tools/demo.py) içindeki `ADIMLAR` listesinde; beklemeleri oradan
ayarla.

```bash
pip install pillow
python tools/demo.py              # docs/demo.gif + docs/demo.cast
python tools/doctor_goruntu.py    # docs/doctor.svg + docs/doctor.png
```

Araç toplam süreyi yazdırır ve 20–30 saniye dışına çıkarsa uyarır. `--sadece-cast`
Pillow olmadan yalnızca asciicast üretir.

**Linux / macOS / WSL — gerçek terminal kaydı.** `asciinema`'nın Windows sürümü yok,
bu yüzden bu yol yalnızca orada çalışır:

```bash
asciinema rec docs/demo.cast --cols 96 --rows 36 --overwrite \
    --idle-time-limit 2 -c "bash tools/demo_akis.sh"
agg --font-size 15 --theme github-dark docs/demo.cast docs/demo.gif
```

[tools/demo_akis.sh](tools/demo_akis.sh) akışı kendisi yazdığı için kaydı gözetimsiz
alabilirsin; yazım hatası ve yeniden çekim yok. İkisi de geçici bir dizinde çalışır,
senin deponu değiştirmez.

Kaydedilen akış, 29,7 saniye:

| Saniye | Ne görünüyor |
|---|---|
| 0–4 | `git rebase main` → `CONFLICT` ve `error: could not apply` |
| 4–14 | `gitwhy` → ne olduğu, deponun durumu, üç seçenek ve yıkıcı olanın uyarısı |
| 14–17 | çakışma çözülür, `git add a.txt` |
| 17–21 | `git rebase --continue` → `Successfully rebased and updated refs/heads/ozellik.` |
| 21–30 | `gitwhy doctor` → temiz depo |

## Lisans

MIT
