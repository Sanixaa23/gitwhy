## Ne oldu

Uzak adres tanımlı (`{{remoteler}}`) ama `{{branch}}` branch'inin hangi uzak branch'i
takip ettiği kayıtlı değil. Git nereye göndereceğini biliyor, hangi branch'e
göndereceğini bilmiyor. Bu, yeni açtığın her branch'te bir kere olur.

Senaryo 5 ile karıştırma: orada hiç remote yoktu. Burada remote var, eşleşme yok.

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}`
- Upstream: {{upstream}}
- Tanımlı remote: {{remoteler}}

## Ne yapmalısın

Branch'i gönder ve takip bağını aynı komutta kur:

    git push -u {{ilk_remote}} {{branch}}

`-u` yalnızca bir kere gerekir. Sonraki gönderimlerde `git push` yeter.

Her yeni branch'te bunu yazmaktan kurtulmak istiyorsan:

    git config --global push.autoSetupRemote true
