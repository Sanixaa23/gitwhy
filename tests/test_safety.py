"""Guvenlik kurallari testle garanti edilir.

Jurinin onunde soylenebilecek cumle: "yikici komut onerisinin uyari tasidigini
testle garanti ediyoruz." Bu dosya o cumleyi dogrulayan sey.
"""
from __future__ import annotations

import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "src"))

from gitwhy import explain  # noqa: E402


def test_yikici_komut_iceren_her_sablon_uyari_tasiyor():
    kusurlu = [
        ad for ad, metin in explain.sablonlar().items()
        if explain.yikici_mi(metin) and not explain.uyari_tasiyor(metin)
    ]
    assert not kusurlu, "yikici komut iceriyor ama uyarisi yok: %s" % kusurlu


def test_uyari_satiri_kalici_kelimesini_tasiyor():
    """Uyari "ne silinecegini" soylemeli, sadece "dikkat" demeli degil."""
    kusurlu = []
    for ad, metin in explain.sablonlar().items():
        if not explain.yikici_mi(metin):
            continue
        uyarilar = [
            s for s in metin.splitlines()
            if s.strip().startswith(explain.UYARI_ONEKI)
        ]
        # Uyari birden fazla satira sarabilir; blogun tamamina bakilir.
        blok = "\n".join(
            s for s in metin.splitlines() if s.strip().startswith(">")
        )
        if not uyarilar or explain.UYARI_ISARETI not in blok:
            kusurlu.append(ad)
    assert not kusurlu, "uyarisi neyin silinecegini soylemiyor: %s" % kusurlu


def test_otomatik_listesinde_yikici_komut_yok():
    """--run eklenirse otomatik calistirilabilir listesi guvenli kalmali."""
    kusurlu = [
        k for k in explain.OTOMATIK_CALISTIRILABILIR
        if explain.yikici_mi(k)
    ]
    assert not kusurlu, "otomatik listesinde yikici komut: %s" % kusurlu


def test_explain_modulu_komut_calistirmiyor():
    """Anlatici katmani hicbir sey kosmaz: subprocess kullanmamali."""
    yol = os.path.join(KOK, "src", "gitwhy", "explain.py")
    with open(yol, encoding="utf-8") as f:
        kaynak = f.read()
    for yasak in ("subprocess", "os.system", "os.popen"):
        assert yasak not in kaynak, "explain.py icinde %s var" % yasak


def test_context_modulu_depoyu_degistirmiyor():
    """Baglam toplayici salt-okunur: depoyu degistiren komut gecmemeli."""
    yol = os.path.join(KOK, "src", "gitwhy", "context.py")
    with open(yol, encoding="utf-8") as f:
        kaynak = f.read()
    # Yorumlardaki kelimeler degil, komut olarak gecen diziler aranir.
    for yasak in ('"reset"', '"clean"', '"checkout"', '"commit"', '"push"',
                  '"merge"', '"rebase"', '"add"', '"stash"', '"restore"'):
        assert yasak not in kaynak, "context.py depoyu degistirebilir: %s" % yasak
