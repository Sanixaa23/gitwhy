# gitwhy

`gitwhy`, bir git komutu başarısız olduğunda hatayı tekrar etmez: deponun o anki durumunu
okur — hangi branch'tesin, kaç commit geride kaldın, hangi dosyalar çakışıyor, yarım kalmış
bir rebase var mı — ve o duruma özel düzeltme komutunu üretir. Eşleştirme deterministik,
LLM değil; ağ olmadan da çalışır. Yıkıcı komutları asla kendiliğinden çalıştırmaz, sadece
ne sileceğini yazarak gösterir. Senaryo eşleşme doğruluğu aşağıdaki tabloda ölçülmüştür.

> **Durum: iskelet.** 12 senaryonun 4'ü çalışıyor. Kalanlar `src/gitwhy/rules.py` içinde
> `TODO` olarak işaretli.

## Kurulum

```
pipx install git+https://github.com/<kullanici>/gitwhy
```

Geliştirme için:

```
pip install -e ".[dev]"
```

## Kullanım

```
gitwhy                           # son başarısız git komutunu açıkla
gitwhy explain --stderr hata.txt # verilen hata çıktısını açıkla (- = stdin)
gitwhy capture -- git push       # komutu koşar, başarısızsa açıklar
gitwhy doctor                    # depo sağlığı: upstream, user.email, sahnelenmiş sır
gitwhy shell-init bash           # git başarısız olunca otomatik devreye giren sarmalayıcı
```

## Senaryolar

| # | Senaryo | Durum | Tespit sinyali |
|---|---|---|---|
| 1 | Detached HEAD | ✅ | `# branch.head (detached)` **ve** sürmekte işlem yok |
| 2 | Merge çakışması | ✅ | `u ` satırları > 0 veya `MERGE_HEAD` |
| 3 | Rebase ortasında kalmış | ✅ | `.git/rebase-merge` veya `rebase-apply` |
| 4 | Cherry-pick / revert ortasında | ⬜ | `CHERRY_PICK_HEAD` / `REVERT_HEAD` |
| 5 | Remote hiç yok | ✅ | `fatal: No configured push destination.` |
| 6 | Remote var, upstream yok | ⬜ | `has no upstream branch` |
| 7 | Push reddedildi (geride kalmış) | ⬜ | `! [rejected]` + `branch.ab -N` |
| 8 | Yanlış branch'e commit | ⬜ | son commit `main`'de ve uzakta yok |
| 9 | `node_modules` sahnelenmiş | ⬜ | staged yol eşleşmesi + `check-ignore` exit 1 |
| 10 | `.env` / anahtar sahnelenmiş | ⬜ | staged dosya adı `.env`, `*.pem`, `id_rsa` |
| 11 | Yerel değişiklik checkout'u engelliyor | ⬜ | `would be overwritten` |
| 12 | Kaybolmuş commit | ⬜ | reflog'da HEAD'den erişilemeyen commit |

Kapsam burada duruyor. "Tüm git hatalarını çözer" diye bir iddia yok.

## Ölçülmüş senaryo doğruluğu

`tests/fixtures.py` her senaryo için **gerçek** bir git deposu kurar ve onu o bozuk duruma
sokar; kural motoru o depoyu okuyarak tahmin eder. Matris `python tests/test_rules.py`
çıktısıdır.

```
gercek \ tahmin     01    02    03    05   yok
01                   1     0     0     0     0
02                   0     1     0     0     0
03                   0     0     1     0     0
05                   0     0     0     1     0

4/4 dogru eslesme (%100)
```

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

## Lisans

MIT
