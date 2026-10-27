## Ne oldu

Bir `git {{surmekte_komut}}` yarıda kaldı. Git tek bir commit'in değişikliğini buraya
taşımaya çalıştı, ama aynı satırlar bu tarafta da değişmiş olduğu için karar veremedi ve
durdu. Git'in ilk yazdığı satır `error: could not apply` olur; asıl bilgi daha aşağıdaki
`CONFLICT` satırındadır.

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}`
- Süren işlem: {{surmekte}}
- Çakışan dosya ({{cakisan_sayisi}}): {{cakisan}}

## Ne yapmalısın

Çakışan dosyaları aç, `<<<<<<<` ile `>>>>>>>` arasındaki iki sürümden hangisinin
kalacağına karar ver, işaret satırlarını sil. Sonra:

    git add {{cakisan_ilk}}
    git {{surmekte_komut}} --continue

Bu commit'i taşımaktan vazgeçtiysen, sadece onu atla:

    git {{surmekte_komut}} --skip

İşlemin tamamından vazgeçip başladığın yere dönmek istiyorsan:

    git {{surmekte_komut}} --abort

Nerede kaldığını görmek için:

    git status --short

> UYARI: `git {{surmekte_komut}} --abort` işlemi geri alır ve bu sırada çakışan dosyalarda
> yaptığın elle düzeltmeleri KALICI olarak siler. `--skip` ise o commit'in değişikliğini
> hiç almamış olur. gitwhy bu komutları kendiliğinden çalıştırmaz.
