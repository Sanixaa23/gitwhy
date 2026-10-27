## Ne oldu

Bir rebase yarıda kaldı. Git commit'lerini tek tek yeni tabana taşırken bir tanesinde
takıldı. Bu sırada hiçbir branch üzerinde görünmezsin — `git status` "detached" der ama
asıl sorun bu değil, sürmekte olan rebase'dir.

## Neredesin

- Depo: `{{depo}}`
- Süren işlem: {{surmekte}}
- Çakışan dosya ({{cakisan_sayisi}}): {{cakisan}}
- HEAD: `{{oid_kisa}}`

## Ne yapmalısın

Rebase'i bitirmek istiyorsan: çakışan dosyaları düzelt, sonra

    git add .
    git rebase --continue

Bu tek commit'i atlamak istiyorsan:

    git rebase --skip

Rebase'i tamamen geri alıp başladığın yere dönmek istiyorsan:

    git rebase --abort

> UYARI: `git rebase --skip` atladığı commit'in değişikliklerini bırakır; `git rebase --abort`
> ise rebase sırasında yaptığın çakışma düzeltmelerini KALICI olarak siler. İkisi de geri
> alınamaz. gitwhy bu komutları kendiliğinden çalıştırmaz.
