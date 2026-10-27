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


def test_env_example_yanlis_pozitif_vermiyor():
    """`.env.example` commit edilmek uzere var; sir sayilmamali."""
    try:
        fx = fixtures.kur("10_sir_sahnelendi")
        ctx = context.topla(fx.depo)
        assert ".env" in ctx.sahnelenen and ".env.example" in ctx.sahnelenen
        assert rules.sir_yollari(ctx) == [".env"]
    finally:
        fixtures.temizle()


def test_bagimlilik_dosya_degil_dizin_donduruyor():
    """node_modules icindeki 2 dosya icin tek bir dizin adi donmeli."""
    try:
        fx = fixtures.kur("09_bagimlilik_sahnelendi")
        ctx = context.topla(fx.depo)
        assert len(ctx.sahnelenen) == 2
        assert rules.bagimlilik_yollari(ctx) == ["node_modules"]
    finally:
        fixtures.temizle()


def test_reddedilen_pushta_geri_sayisi_sifir_gorunuyor():
    """Dogrulanmis bulgu: reddedilen push remote-tracking ref'i guncellemez.

    Bu yuzden senaryo 7 karari `branch.ab` degil hata metni uzerinden verilir.
    Test, birinin ileride ctx.geri'ye dayanan bir kural yazmasini engeller.
    """
    try:
        fx = fixtures.kur("07_push_reddedildi")
        ctx = context.topla(fx.depo)
        assert "! [rejected]" in fx.hata_metni
        assert ctx.geri == 0, "git davranisi degismis, kural yeniden gozden gecirilmeli"
        assert rules.esle(ctx, fx.hata_metni) == "07_push_reddedildi"
        # Hata metni olmadan bu durum tespit EDILEMEZ; bilerek boyle.
        assert rules.esle(ctx, "") != "07_push_reddedildi"
    finally:
        fixtures.temizle()


def test_sahnelenmis_sir_ignore_kontrolu_no_index_kullaniyor():
    """check-ignore --no-index olmadan sahnelenmis yol hep "ignore edilmiyor" cikar."""
    try:
        fx = fixtures.kur("10_sir_sahnelendi")
        with open(os.path.join(fx.depo, ".gitignore"), "w", encoding="utf-8") as f:
            f.write(".env\n")
        ctx = context.topla(fx.depo)
        assert ".env" in ctx.ignore_edilen, (
            "sahnelenmis .env icin kural eslesmesi gorulemedi; --no-index dusmus olabilir"
        )
    finally:
        fixtures.temizle()


def test_negatif_kontroller_hicbir_senaryoya_eslesmiyor():
    """Sorunsuz depo, amend sonrasi ve main'de gonderilmemis commit:
    uc durumun hicbiri bir senaryo degil. Eslesirse yanlis pozitif var."""
    try:
        for v in ("neg_temiz", "neg_amend", "neg_main_ileride"):
            fx = fixtures.kur(v)
            ctx = context.topla(fx.depo)
            assert rules.esle(ctx, fx.hata_metni) is None, (
                "%s yanlis pozitif verdi: %s" % (v, rules.esle(ctx, fx.hata_metni))
            )
    finally:
        fixtures.temizle()


def test_amend_kayip_commit_sayilmiyor():
    """`commit --amend` eski commit'i erisilemez birakir; kayip degil."""
    try:
        fx = fixtures.kur("neg_amend")
        assert context.kayip_commitler(fx.depo) == []
        fx2 = fixtures.kur("12_reset_hard")
        assert len(context.kayip_commitler(fx2.depo)) == 1
    finally:
        fixtures.temizle()


def test_cherry_pick_ve_revert_ayni_senaryo_farkli_komut():
    """Iki varyant ayni senaryoya duser ama onerilen komut farkli olmali."""
    try:
        for varyant, komut in (("04_cherry_pick", "cherry-pick"), ("04_revert", "revert")):
            fx = fixtures.kur(varyant)
            ctx = context.topla(fx.depo)
            assert rules.esle(ctx, fx.hata_metni) == "04_cherry_pick_ortasi"
            metin = explain.anlat("04_cherry_pick_ortasi", ctx)
            assert "git %s --continue" % komut in metin, (
                "%s icin yanlis komut onerildi" % varyant
            )
    finally:
        fixtures.temizle()


def test_korumali_branch_reddi_push_reddinden_ayirt_ediliyor():
    """08 ve 07 ikisi de "failed to push some refs" iceriyor; karismamali."""
    try:
        korumali = fixtures.kur("08_korumali_branch")
        reddedilen = fixtures.kur("07_push_reddedildi")
        assert "[remote rejected]" in korumali.hata_metni
        assert "[remote rejected]" not in reddedilen.hata_metni
        assert rules.esle(context.topla(korumali.depo), korumali.hata_metni) == "08_yanlis_branch"
        assert rules.esle(context.topla(reddedilen.depo), reddedilen.hata_metni) == "07_push_reddedildi"
    finally:
        fixtures.temizle()


def test_senaryo_11_checkout_ve_merge_varyantlari():
    try:
        for v in ("11_checkout_engellendi", "11_merge_engellendi"):
            fx = fixtures.kur(v)
            ctx = context.topla(fx.depo)
            assert ctx.kaydedilmemis == ["a.txt"], "%s: %s" % (v, ctx.kaydedilmemis)
            assert rules.esle(ctx, fx.hata_metni) == "11_yerel_degisiklik_engelliyor"
    finally:
        fixtures.temizle()


def test_tum_sablonlarda_dolmayan_yer_tutucu_yok():
    """Her senaryo kendi fixture'inda render edilince {{...}} kalmamali."""
    import re
    eksik = {}
    try:
        for fx in fixtures.hepsi():
            senaryo = _tahmin(fx)
            if senaryo == "(eslesme yok)":
                continue
            metin = explain.anlat(senaryo, context.topla(fx.depo))
            kalan = re.findall(r"\{\{\w+\}\}", metin)
            if kalan:
                eksik[senaryo] = kalan
    finally:
        fixtures.temizle()
    assert not eksik, "dolmayan yer tutucu: %s" % eksik


def test_metin_tabanli_fixturelerin_satirlari_kapiyi_geciyor():
    """HATA_ISARETCILERI bir kapi: uymayan satir esle()'ye hic ulasmaz.

    Metinden karar verilen her senaryonun fixture'inda en az bir karar
    satiri kalmali. Bu testin yoklugunda senaryo 8 sessizce eslesmemisti.
    """
    try:
        for v in ("05_remote_yok", "06_upstream_yok", "07_push_reddedildi",
                  "08_korumali_branch", "11_checkout_engellendi",
                  "11_merge_engellendi"):
            fx = fixtures.kur(v)
            assert rules.hata_satirlari(fx.hata_metni), (
                "%s: hata metni isaretci kapisindan gecmiyor" % v
            )
    finally:
        fixtures.temizle()


def test_git_alt_komut_ayristirma():
    assert rules.git_alt_komut("git push") == "push"
    assert rules.git_alt_komut("git -c user.email=x push -u origin main") == "push"
    assert rules.git_alt_komut("git -C /tmp/depo status --short") == "status"
    assert rules.git_alt_komut("git --no-pager log") == "log"
    assert rules.git_alt_komut("npm install") is None
    assert rules.git_alt_komut("git") is None
    assert rules.git_alt_komut("") is None
    assert rules.git_alt_komut(None) is None


def test_sarmalayici_metinsiz_komuttan_buluyor():
    """Sarmalayici hatayi ekranda biraktigi icin metin yok, komut var.

    Bu blok olmadan 5, 6 ve 11 sarmalayici uzerinden hic eslesmiyordu;
    gercek bir depoda olculdu (bkz. tools/sarmalayici_test.sh).
    """
    try:
        bekleneler = (
            ("05_remote_yok", "git push", "05_remote_yok"),
            ("06_upstream_yok", "git push", "06_upstream_yok"),
            ("11_checkout_engellendi", "git checkout ozellik",
             "11_yerel_degisiklik_engelliyor"),
        )
        for varyant, komut, beklenen in bekleneler:
            fx = fixtures.kur(varyant)
            ctx = context.topla(fx.depo)
            assert rules.esle(ctx, "", komut) == beklenen, (
                "%s: metinsiz eslesme basarisiz" % varyant
            )
    finally:
        fixtures.temizle()


def test_komut_tek_basina_yanlis_pozitif_vermiyor():
    """Remote ve upstream varken basarisiz bir push komut kuralina dusmemeli."""
    try:
        fx = fixtures.kur("neg_main_ileride")
        ctx = context.topla(fx.depo)
        assert ctx.remote_var and ctx.upstream
        assert rules.esle(ctx, "", "git push") is None
        # Temiz depoda checkout basarisizligi da uydurulmamali.
        fx2 = fixtures.kur("neg_temiz")
        ctx2 = context.topla(fx2.depo)
        assert rules.esle(ctx2, "", "git checkout main") is None
    finally:
        fixtures.temizle()


def test_kayit_gecerliligi():
    """Bayat ya da baska depoya ait kayit komut kurallarini tetiklememeli."""
    import time
    from gitwhy import capture
    try:
        fx = fixtures.kur("05_remote_yok")
        taze = {"depo": fx.depo, "zaman": time.time(), "komut": "git push"}
        bayat = {"depo": fx.depo, "zaman": time.time() - 3600, "komut": "git push"}
        baska = {"depo": os.path.join(fx.depo, "baska"), "zaman": time.time(),
                 "komut": "git push"}
        assert capture.gecerli(taze, fx.depo)
        assert not capture.gecerli(bayat, fx.depo)
        assert not capture.gecerli(baska, fx.depo)
        assert not capture.gecerli(None, fx.depo)
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


def _kisa(senaryo_id: str) -> str:
    """Matris basligi icin kisa ad. "yok" satiri negatif kontrolleri tutar."""
    return "yok" if senaryo_id == "(eslesme yok)" else senaryo_id.split("_")[0]


def karisiklik_matrisi():
    """Karisiklik matrisi: gercek satir, tahmin kolon.

    Son satir/kolon negatif kontroller: sorunsuz depo, amend sonrasi,
    main'de gonderilmemis commit. Oradaki kosegen dogru yanlis-pozitif
    vermemek demek.
    """
    senaryolar = list(fixtures.SENARYOLAR)
    matris = {g: {t: 0 for t in senaryolar} for g in senaryolar}
    try:
        for fx in fixtures.hepsi():
            matris[fx.senaryo_id][_tahmin(fx)] += 1
    finally:
        fixtures.temizle()

    basliklar = [_kisa(k) for k in senaryolar]
    print("gercek \\ tahmin   " + " ".join("%4s" % b for b in basliklar))
    dogru = toplam = 0
    for g in senaryolar:
        satir = " ".join("%4d" % matris[g][t] for t in senaryolar)
        print("%-17s %s" % (_kisa(g), satir))
        dogru += matris[g][g]
        toplam += sum(matris[g].values())
    print("\n%d senaryo, %d fixture, %d/%d dogru eslesme (%%%d)" % (
        len(rules.UYGULANAN), len(fixtures.VARYANTLAR),
        dogru, toplam, round(100 * dogru / toplam)))
    return matris


if __name__ == "__main__":
    karisiklik_matrisi()
