## Ne oldu

Reflog'da hiçbir branch'ten erişilemeyen {{kayip_sayisi}} commit var. Bunlar git'in
içinde duruyor ama hiçbir dal onlara işaret etmiyor, bu yüzden `git log` çıktısında
görünmüyorlar. Genelde `git reset --hard` ya da silinmiş bir branch'ten sonra olur.

**Commit'ler silinmedi.** Git erişilemeyen nesneleri bir süre (varsayılan 90 gün) tutuyor;
bu süre içinde geri alınabilirler.

## Neredesin

- Depo: `{{depo}}`
- Branch: `{{branch}}`
- Erişilemeyen commit'ler:

{{kayip_listesi}}

Yalnızca reflog'un son 10 girdisine bakılıyor; aylar önce düşmüş bir commit burada
görünmez. Tam listeyi `gitwhy doctor` ya da `git reflog` gösterir.

## Ne yapmalısın

Önce içeriğini gör; doğru commit olduğundan emin ol:

    git show {{kayip_ilk_sha}}

İşini geri almanın en güvenli yolu, o commit'e yeni bir branch vermek. Bulunduğun
branch'e dokunmaz:

    git switch -c kurtarma-{{kayip_ilk_sha}} {{kayip_ilk_sha}}

Sadece o commit'in değişikliğini şu anki branch'e almak istersen:

    git cherry-pick {{kayip_ilk_sha}}

Bu commit'ler gerçekten gereksizse hiçbir şey yapma; git zamanla kendisi temizler.

> UYARI: `git gc --prune=now` ve `git reflog expire --expire=now --all` erişilemeyen
> commit'leri beklemeden siler; bu noktadan sonra geri dönüş yoktur ve iş KALICI olarak
> kaybolur. Kurtarmak istediğin bir şey varken bu komutları çalıştırma. gitwhy ikisini de
> kendiliğinden çalıştırmaz.
