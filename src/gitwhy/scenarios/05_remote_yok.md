## Ne oldu

`git push` çalıştırdın ama bu deponun tanımlı hiçbir uzak adresi yok. Git nereye
göndereceğini bilmiyor. Depoyu `git init` ile kendi makinende oluşturduysan bu normaldir:
GitHub'daki depo ile bağlantıyı henüz kurmadın.

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}`
- Tanımlı remote: yok
- Gönderilmeyi bekleyen commit sayısı: {{ileri}} (upstream tanımlı değilken git bunu sayamaz)

## Ne yapmalısın

GitHub'da boş bir depo aç, sonra adresini buraya bağla ve ilk gönderimi yap:

    git remote add origin https://github.com/<kullanici>/<depo>.git
    git push -u origin {{branch}}

`-u` bir kere gerekir: bu branch'in hangi uzak branch'i takip ettiğini kaydeder. Sonraki
gönderimlerde yalnızca `git push` yeter.

Bağlantının kurulduğunu doğrulamak için:

    git remote -v
