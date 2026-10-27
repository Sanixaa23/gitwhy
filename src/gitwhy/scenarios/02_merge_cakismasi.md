## Ne oldu

İki taraf aynı satırları farklı şekilde değiştirdiği için git birleştirmeyi tamamlayamadı.
Merge yarıda durdu: çakışan dosyaların içine `<<<<<<<`, `=======`, `>>>>>>>` işaretleri
yazıldı ve hangisinin kalacağına senin karar vermen gerekiyor.

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}`
- Çakışan dosya ({{cakisan_sayisi}}): {{cakisan}}
- Süren işlem: {{surmekte}}

## Ne yapmalısın

Her çakışan dosyayı aç, işaretli blokları elle düzelt, işaret satırlarını sil. Sonra:

    git add {{cakisan_ilk}}
    git commit

Hangi dosyanın hâlâ çakıştığını görmek için:

    git diff --name-only --diff-filter=U

Merge'den tamamen vazgeçmek istiyorsan:

    git merge --abort

> UYARI: `git merge --abort` komutu merge'i geri alır ve merge başladıktan sonra çakışan
> dosyalarda yaptığın elle düzeltmeleri KALICI olarak siler. gitwhy bu komutu kendiliğinden
> çalıştırmaz.
