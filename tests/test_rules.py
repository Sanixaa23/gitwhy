"""Olculmus senaryo dogrulugu: her senaryo gercek bir depoda kurulur.

Dogrudan da kosar (pytest gerekmez):
    python tests/test_rules.py
Bu bicimde karisiklik matrisini yazdirir; README'deki tablo buradan gelir.
"""
from __future__ import annotations

import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402
from gitwhy import context, explain, rules  # noqa: E402


def _tahmin(fx) -> str:
    ctx = context.topla(fx.depo)
    return rules.esle(ctx, fx.hata_metni) or "(eslesme yok)"


def test_her_senaryo_dogru_eslesiyor():
    """Fixture ile kurulan her durum kendi senaryosuna eslesmeli."""
    try:
        for fx in fixtures.hepsi():
            assert _tahmin(fx) == fx.senaryo_id, (
                "%s yerine %s esleşti" % (fx.senaryo_id, _tahmin(fx))
            )
    finally:
        fixtures.temizle()


def test_rebase_detached_oncesinde_kontrol_ediliyor():
    """Dogrulanmis siralama kurali: rebase ortasindaki depo detached da gorunur.

    Bu test kuralin yanlislikla degistirilmesini yakalar.
    """
    try:
        fx = fixtures.kur("03_rebase_ortasi")
        ctx = context.topla(fx.depo)
        assert ctx.detached, "rebase ortasindaki depo detached gorunmuyor, fixture bozulmus"
        assert "rebase-merge" in ctx.surmekte or "rebase-apply" in ctx.surmekte
        assert rules.esle(ctx, fx.hata_metni) == "03_rebase_ortasi"
    finally:
        fixtures.temizle()


def test_hata_metni_tum_satirlar_taraniyor():
    """Merge cakismasinda ilk satir "Auto-merging"; CONFLICT asagida."""
    try:
        fx = fixtures.kur("02_merge_cakismasi")
        assert "CONFLICT" in fx.hata_metni
        satirlar = rules.hata_satirlari(fx.hata_metni)
        assert satirlar, "karar satiri bulunamadi"
        assert any("CONFLICT" in s for s in satirlar)
    finally:
        fixtures.temizle()


def test_uygulanan_senaryolarin_sablonu_var():
    eksik = [s for s in rules.UYGULANAN if s not in explain.sablonlar()]
    assert not eksik, "sablonu olmayan senaryo: %s" % eksik


def test_bos_hata_metni_cokmuyor():
    try:
        fx = fixtures.kur("01_detached_head")
        ctx = context.topla(fx.depo)
        assert rules.esle(ctx, "") == "01_detached_head"
        assert rules.esle(ctx, None) == "01_detached_head"
    finally:
        fixtures.temizle()


def test_git_deposu_olmayan_dizin():
    import tempfile
    d = tempfile.mkdtemp(prefix="gitwhy_bos_")
    try:
        ctx = context.topla(d)
        assert not ctx.gecerli_depo
        assert rules.esle(ctx, "fatal: not a git repository") is None
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def karisiklik_matrisi():
    """12x12 matrisin su anki 4 senaryoluk hali. gercek satir, tahmin kolon."""
    senaryolar = list(fixtures.SENARYOLAR)
    kolonlar = senaryolar + ["(eslesme yok)"]
    matris = {g: {t: 0 for t in kolonlar} for g in senaryolar}
    try:
        for fx in fixtures.hepsi():
            matris[fx.senaryo_id][_tahmin(fx)] += 1
    finally:
        fixtures.temizle()

    kisa = {s: s.split("_")[0] for s in senaryolar}
    kisa["(eslesme yok)"] = "yok"
    basliklar = [kisa[k] for k in kolonlar]
    print("gercek \\ tahmin   " + "  ".join("%4s" % b for b in basliklar))
    dogru = toplam = 0
    for g in senaryolar:
        satir = "  ".join("%4d" % matris[g][t] for t in kolonlar)
        print("%-17s %s" % (kisa[g], satir))
        dogru += matris[g][g]
        toplam += sum(matris[g].values())
    print("\n%d/%d dogru eslesme (%%%d)" % (dogru, toplam, round(100 * dogru / toplam)))
    return matris


if __name__ == "__main__":
    karisiklik_matrisi()
