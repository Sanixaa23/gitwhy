## Ne oldu

Uzak taraf gönderimi reddetti: `{{branch}}` korumalı bir branch. Commit'ini doğrudan
buraya attın, ama bu depoda değişikliklerin bir özellik branch'i üzerinden pull request
ile girmesi gerekiyor. Commit'in kaybolmadı — sadece henüz doğru yerde değil.

Bu, senaryo 7 ile aynı şey değil: orada git'in kendisi "uzaktakini önce al" diyordu.
Burada gönderim uzak sunucuya ulaştı ve kural gereği geri çevrildi.

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}` → `{{upstream}}`
- Gönderilmeyi bekleyen: {{ileri}} commit
- Son commit: {{son_mesaj}}

## Ne yapmalısın

Commit'lerini bulundukları yerden alıp yeni bir branch'e taşı. Sıra önemli: önce yeni
branch'i aç, sonra `{{branch}}`'i uzaktaki haline geri çek.

Yeni branch'i şu anki haliyle aç ve gönder:

    git switch -c ozellik/{{branch}}-degisikligi
    git push -u {{ilk_remote}} ozellik/{{branch}}-degisikligi

Sonra GitHub'da pull request aç. `{{branch}}`'i temizlemek istersen, önce yeni branch'in
gönderildiğini `git log --oneline {{ilk_remote}}/ozellik/{{branch}}-degisikligi` ile
doğrula, sonra:

    git switch {{branch}}
    git reset --hard {{upstream}}

> UYARI: `git reset --hard {{upstream}}` komutu `{{branch}}` üzerindeki {{ileri}} commit'i
> bu branch'ten atar ve kaydedilmemiş değişikliklerini KALICI olarak siler. Yalnızca yeni
> branch'in gönderildiğini doğruladıktan sonra çalıştır. gitwhy bu komutu kendiliğinden
> çalıştırmaz.
