## Ne oldu

Bağımlılık dizini sahnelendi: **{{bagimlilik}}**. Bu dizinler kaynak kod değil, bir
komutla yeniden üretilen dosyalardır (`npm install`, `pip install`). Commit edilirse depo
şişer, her pull çakışır ve kod incelemesi okunamaz hale gelir.

{{ignore_durumu}}

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}`
- Sahnelenmiş bağımlılık dizini: {{bagimlilik_sayisi}} — {{bagimlilik}}
- Sahnelenmiş dosya sayısı: {{sahnelenen_sayisi}}

## Ne yapmalısın

Henüz commit etmediysen, sahneden çıkar ve kuralı yaz:

    git rm -r --cached {{bagimlilik_ilk}}
    echo "{{bagimlilik_ilk}}/" >> .gitignore
    git add .gitignore

Sonra sahnede ne kaldığını kontrol et:

    git diff --cached --name-only

> UYARI: `git rm -r --cached` dosyaları diskten silmez, yalnızca git takibinden çıkarır —
> `--cached` olmadan yazarsan aynı komut dosyaları diskten KALICI olarak siler. Bu dizini
> daha önce commit edip gönderdiysen dosyalar geçmişte kalmaya devam eder; depo boyutunu
> küçültmek geçmişi yeniden yazmayı gerektirir.
