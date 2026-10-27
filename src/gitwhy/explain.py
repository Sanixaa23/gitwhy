"""Senaryo kimligi + baglam -> okunabilir metin.

Iki mod:
  - Sablon modu (varsayilan): scenarios/*.md dosyalari, baglam degerleri
    yerlestirilmis. Agsiz, deterministik, aninda.
  - LLM modu (--ai, henuz yok): ayni sablonu kullanicinin seviyesine gore
    yeniden yazar. Karar LLM'de DEGIL; LLM sadece metni yeniden yazar.

Guvenlik: bu modul hicbir komut CALISTIRMAZ. Sadece metin uretir.
"""
from __future__ import annotations

import os
import re
from typing import Dict, Optional

from .context import Baglam

SABLON_DIZINI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios")

# Geri alinamaz veri kaybina yol acabilen komutlar. Sablonlarda bunlardan biri
# geciyorsa sablon UYARI_ISARETI tasimak zorunda; test_safety.py bunu dogrular.
YIKICI_KOMUTLAR = (
    "git reset --hard",
    "git clean -f",
    "git checkout --",
    "git push --force",
    "git push -f",
    "git rebase --abort",
    "git rebase --skip",
    "git merge --abort",
    "git stash drop",
    "git stash clear",
    "git branch -D",
    "git reflog expire",
    "git gc --prune",
    "--discard-changes",
)

# Bir --run secenegi eklenirse YALNIZCA bunlar otomatik calistirilabilir.
# Hepsi geri alinabilir islemler. Bu listeye yikici komut eklenemez.
OTOMATIK_CALISTIRILABILIR = (
    "git switch",
    "git stash push",
    "git branch",
    "git remote -v",
    "git status",
    "git diff",
    "git log",
)

# Sablonlardaki uyari satiri bu isaretle baslar ve KALICI kelimesini tasir.
UYARI_ONEKI = "> UYARI:"
UYARI_ISARETI = "KALICI"

_YER_TUTUCU = re.compile(r"\{\{(\w+)\}\}")


def degerler(ctx: Baglam) -> Dict[str, str]:
    """Sablonlarda kullanilabilen yer tutucular."""
    return {
        "depo": ctx.depo,
        "branch": ctx.branch or "(branch yok)",
        "upstream": ctx.upstream or "(tanimli degil)",
        "ileri": str(ctx.ileri),
        "geri": str(ctx.geri),
        "oid_kisa": ctx.oid_kisa,
        "son_mesaj": ctx.son_mesaj or "(commit yok)",
        "cakisan": ", ".join(ctx.cakisan) or "(yok)",
        "cakisan_ilk": ctx.cakisan[0] if ctx.cakisan else "<dosya>",
        "cakisan_sayisi": str(len(ctx.cakisan)),
        "sahnelenen": ", ".join(ctx.sahnelenen) or "(yok)",
        "sahnelenen_sayisi": str(len(ctx.sahnelenen)),
        "surmekte": ", ".join(ctx.surmekte) or "(yok)",
        "remoteler": ", ".join(ctx.remoteler) or "(yok)",
        "user_email": ctx.user_email or "(tanimli degil)",
    }


def sablon_oku(senaryo_id: str) -> str:
    yol = os.path.join(SABLON_DIZINI, senaryo_id + ".md")
    with open(yol, encoding="utf-8") as f:
        return f.read()


def sablonlar() -> Dict[str, str]:
    """Tum sablonlari {senaryo_id: metin} olarak dondurur (test_safety icin)."""
    if not os.path.isdir(SABLON_DIZINI):
        return {}
    return {
        ad[:-3]: sablon_oku(ad[:-3])
        for ad in sorted(os.listdir(SABLON_DIZINI))
        if ad.endswith(".md")
    }


def doldur(sablon: str, ctx: Baglam) -> str:
    """{{anahtar}} yer tutucularini baglam degerleriyle degistirir.

    Bilinmeyen anahtar oldugu gibi birakilir: sablon yazim hatasi sessizce
    kaybolmasin, ciktida gorunsun.
    """
    d = degerler(ctx)
    return _YER_TUTUCU.sub(lambda m: d.get(m.group(1), m.group(0)), sablon)


def anlat(senaryo_id: Optional[str], ctx: Baglam) -> str:
    """Senaryo metnini uretir. Eslesme yoksa durum dokumu dondurur."""
    if senaryo_id is None:
        return _eslesme_yok(ctx)
    try:
        sablon = sablon_oku(senaryo_id)
    except FileNotFoundError:
        return (
            "Senaryo eslesti ama sablonu yok: %s\n"
            "src/gitwhy/scenarios/%s.md dosyasini yaz.\n" % (senaryo_id, senaryo_id)
        )
    return doldur(sablon, ctx)


def _eslesme_yok(ctx: Baglam) -> str:
    if not ctx.gecerli_depo:
        return (
            "## Ne oldu\n\n"
            "Burasi bir git deposu degil: %s\n\n"
            "## Ne yapmalisin\n\n"
            "    git init\n" % ctx.depo
        )
    d = degerler(ctx)
    return (
        "## Eslesen senaryo yok\n\n"
        "gitwhy su an 12 senaryodan 4'unu tanıyor. Bu durum onlardan biri degil.\n\n"
        "## Neredesin\n\n"
        "- Depo: %(depo)s\n"
        "- Branch: %(branch)s\n"
        "- Upstream: %(upstream)s (ileri %(ileri)s / geri %(geri)s)\n"
        "- Cakisan dosya: %(cakisan)s\n"
        "- Surmekte olan islem: %(surmekte)s\n"
        "- Sahnelenmis dosya: %(sahnelenen_sayisi)s\n" % d
    )


def yikici_mi(metin: str) -> bool:
    """Verilen metinde geri alinamaz bir komut geciyor mu."""
    return any(k in metin for k in YIKICI_KOMUTLAR)


def uyari_tasiyor(metin: str) -> bool:
    """Metinde kurallara uygun bir uyari satiri var mi."""
    for satir in metin.splitlines():
        if satir.strip().startswith(UYARI_ONEKI):
            return True
    return False
