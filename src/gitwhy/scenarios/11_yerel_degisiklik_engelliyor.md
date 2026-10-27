## Ne oldu

Kaydedilmemiş değişikliğin var ve yapmak istediğin işlem o dosyaların üzerine yazacaktı.
Git işlemi yapmadı — yani hiçbir şey kaybetmedin. Bu bir koruma, hata değil: git
kaydedilmemiş işin sessizce silinmesine izin vermiyor.

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}`
- Kaydedilmemiş değişiklik ({{kaydedilmemis_sayisi}}): {{kaydedilmemis}}
- Sahnelenmiş dosya: {{sahnelenen_sayisi}}

## Ne yapmalısın

Üç yoldan birini seç.

Değişiklik işine yarıyorsa commit et, sonra işlemi tekrar dene:

    git add {{kaydedilmemis_ilk}}
    git commit -m "yarim kalan is"

Şimdi commit etmek istemiyorsan kenara koy; işlemden sonra geri alırsın:

    git stash push -m "branch degistirmeden once"
    git stash pop

Ne değiştiğini önce görmek istersen:

    git diff {{kaydedilmemis_ilk}}

> UYARI: Üçüncü yol bu değişiklikten vazgeçmek olurdu (`git checkout -- <dosya>` veya
> `git restore <dosya>`). Bu komut dosyayı son commit'teki haline döndürür ve
> kaydedilmemiş işini KALICI olarak siler — stash'e almadıysan geri dönüşü yoktur.
> gitwhy bu komutu kendiliğinden çalıştırmaz ve `git stash push` varken önermez.
