## Ne oldu

Hiçbir branch üzerinde değilsin. Git buna "detached HEAD" diyor: `{{oid_kisa}}` commit'ine
doğrudan bakıyorsun. Buradan atacağın commit'ler hiçbir branch'e bağlanmaz ve branch
değiştirdiğin anda kolayca bulunamaz hale gelirler.

## Neredesin

- Depo: `{{depo}}`
- HEAD: `{{oid_kisa}}` — bağlı olduğu branch yok
- Son commit: {{son_mesaj}}
- Sahnelenmiş dosya: {{sahnelenen_sayisi}}

## Ne yapmalısın

Burada iş yaptıysan, önce ona bir branch ver:

    git switch -c kurtarma-{{oid_kisa}}

Hiçbir şey yapmadıysan ve geldiğin yere dönmek istiyorsan:

    git switch -

> UYARI: Kaydedilmemiş değişikliğin varsa `git switch -` komutunu git engeller. Bu engeli
> `--discard-changes` ile aşmak, kaydedilmemiş tüm değişikliklerini KALICI olarak siler.
> gitwhy bu komutu kendiliğinden çalıştırmaz; kararı sen ver.
