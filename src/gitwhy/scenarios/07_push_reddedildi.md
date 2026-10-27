## Ne oldu

Uzaktaki `{{upstream}}` branch'inde sende olmayan commit'ler var. Senin gönderdiğin
commit onların üstüne doğrudan oturmadığı için git göndermeyi reddetti. Genelde takım
arkadaşın aynı branch'e senden önce gönderdiği için olur.

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}` → `{{upstream}}`
- Gönderilmeyi bekleyen: {{ileri}} commit
- Geride: {{geri}} commit

> Bu "geride" sayısı reddedilen push'tan hemen sonra **0 görünür**: git reddedilen bir
> push'tan sonra uzak takip referansını güncellemiyor. Gerçek sayı `git fetch` sonrası
> ortaya çıkar. gitwhy fetch çalıştırmaz, o yüzden kararı hata metninden verir.

## Ne yapmalısın

Önce onların işini kendi üstüne al, sonra gönder:

    git pull --rebase {{ilk_remote}} {{branch}}
    git push

`--rebase` senin commit'lerini onların üstüne taşır, gereksiz merge commit'i oluşmaz.
Bu sırada çakışma çıkarsa `gitwhy` tekrar çalıştır: senaryo 2 devreye girer.

Ne olduğunu önce görmek istersen:

    git fetch {{ilk_remote}}
    git log --oneline --graph HEAD...{{upstream}}

> UYARI: `git push --force` bu hatayı susturur ama uzaktaki commit'leri KALICI olarak
> siler — takım arkadaşının işi kaybolur. gitwhy bu komutu kendiliğinden çalıştırmaz ve
> paylaşılan bir branch'te önermez.
