## Ne oldu

Sır taşıyan dosya sahnelendi: **{{sir}}**. Bu dosya commit edilirse içindeki anahtar
deponun geçmişine girer. Depoyu bir kere gönderdiysen anahtarı sızmış kabul et: silmek
yetmez, geçmişten temizlemek de yetmez — anahtarın kendisi yenilenmelidir.

`.env.example`, `.env.sample` gibi şablon dosyaları uyarı vermez; onlar commit edilmek
üzere vardır.

{{ignore_durumu}}

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}`
- Sahnelenmiş sır dosyası: {{sir_sayisi}} — {{sir}}
- Upstream: {{upstream}} (upstream varsa bu depo daha önce gönderilmiş olabilir)

## Ne yapmalısın

Henüz commit etmediysen, en kolay durum budur:

    git rm --cached {{sir_ilk}}
    echo "{{sir_ilk}}" >> .gitignore
    git add .gitignore

Commit ettiysen ama **göndermediysen**, son commit'i düzelt:

    git rm --cached {{sir_ilk}}
    git commit --amend

Gönderdiysen sıra şu şekilde olmalı. Önce anahtarı sağlayıcısının panelinden iptal edip
yenisini üret; bu adımı geçmişi temizlemeden önce yap, çünkü gönderilmiş bir anahtarın
kopyası artık senin kontrolünde değil. Ardından `git filter-repo` ile dosyayı geçmişten
çıkar ve son olarak deponun kopyasına sahip herkese depolarını yeniden klonlamalarını
söyle.

Dosyanın geçmişte hangi commit'lerde olduğunu görmek için:

    git log --oneline -- {{sir_ilk}}

> UYARI: `git filter-repo` deponun tüm geçmişini yeniden yazar; her commit'in kimliği
> değişir ve eski geçmiş KALICI olarak kaybolur. Açık pull request'ler ve başkalarının
> yerel kopyaları bozulur. gitwhy bu komutu kendiliğinden çalıştırmaz.
