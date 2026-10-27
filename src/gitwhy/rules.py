"""Baglam + hata metni -> senaryo kimligi.

Saf fonksiyon: I/O yok, ag yok, LLM yok. Projenin test edilebilirliginin
tamami bu dosyadan geliyor; buraya subprocess veya dosya okuma eklemeyin.
"""
from __future__ import annotations

from typing import List, Optional

from .context import Baglam

# 12 senaryonun tam listesi. Kapsam burada donuyor: fazlasini eklemeyin.
SENARYOLAR = [
    "01_detached_head",
    "02_merge_cakismasi",
    "03_rebase_ortasi",
    "04_cherry_pick_ortasi",
    "05_remote_yok",
    "06_upstream_yok",
    "07_push_reddedildi",
    "08_yanlis_branch",
    "09_bagimlilik_sahnelendi",
    "10_sir_sahnelendi",
    "11_yerel_degisiklik_engelliyor",
    "12_kayip_commit",
]

# Su an gercekten eslestirilen ve sablonu yazilmis senaryolar.
# Yeni senaryo eklerken: fixture -> kural -> sablon, bu sirayla.
UYGULANAN = (
    "01_detached_head",
    "02_merge_cakismasi",
    "03_rebase_ortasi",
    "05_remote_yok",
)

# Fixture testinde dogrulandi: git'in ilk cikti satiri gercek hata olmayabilir.
# Merge cakismasinda ilk satir "Auto-merging a.txt"; CONFLICT asagida.
# Bu yuzden TUM satirlari tariyoruz, ilkini almiyoruz.
HATA_ISARETCILERI = ("CONFLICT", "error:", "fatal:", "! [rejected]", "warning:")


def hata_satirlari(hata_metni: Optional[str]) -> List[str]:
    """Hata metninin icinden karar verilebilir satirlari suzer."""
    if not hata_metni:
        return []
    return [
        s.strip()
        for s in hata_metni.splitlines()
        if any(isaret in s for isaret in HATA_ISARETCILERI)
    ]


def _metinde(hata_metni: Optional[str], *parcalar: str) -> bool:
    """Hata metninin karar satirlarinda verilen parcalardan biri var mi."""
    satirlar = hata_satirlari(hata_metni)
    return any(parca in s for parca in parcalar for s in satirlar)


def esle(ctx: Baglam, hata_metni: Optional[str] = None) -> Optional[str]:
    """Durum ve hata metninden senaryo kimligi uretir; eslesme yoksa None.

    SIRALAMA KURALI (fixture testiyle dogrulandi, degistirmeyin):
    Rebase cakismasinin ortasinda `git status` AYNI ANDA
    `# branch.head (detached)` ve `rebase-merge` gosteriyor. Detached HEAD'i
    once kontrol edersen rebase'in ortasindaki kullaniciya "detached
    HEAD'desin" deyip tamamen yanlis komut onerirsin.
    Dogru sira: surmekte olan islem -> cakisma -> hata metni -> detached.
    """
    if not ctx.gecerli_depo:
        return None

    # 1) Yarim kalmis islemler. En aciliyetli durum ve detached'i maskeler.
    if "rebase-merge" in ctx.surmekte or "rebase-apply" in ctx.surmekte:
        return "03_rebase_ortasi"
    if "CHERRY_PICK_HEAD" in ctx.surmekte or "REVERT_HEAD" in ctx.surmekte:
        return None  # TODO senaryo 04: fixture + sablon yazilacak

    # 2) Cakisma. MERGE_HEAD rebase'de de olur, o yuzden 1. adimdan sonra.
    if ctx.cakisan or "MERGE_HEAD" in ctx.surmekte:
        return "02_merge_cakismasi"

    # 3) Hata metninin kendisi hangi islemin denendigini soyluyor.
    #    Bu yuzden detached kontrolunden once: kullanici push denediyse,
    #    detached oldugunu soylemek sorusuna cevap olmaz.
    if _metinde(hata_metni, "No configured push destination"):
        return "05_remote_yok"
    if _metinde(hata_metni, "has no upstream branch"):
        return None  # TODO senaryo 06
    if _metinde(hata_metni, "! [rejected]", "non-fast-forward"):
        return None  # TODO senaryo 07
    if _metinde(hata_metni, "would be overwritten"):
        return None  # TODO senaryo 11

    # 4) Durumdan okunan, komuttan bagimsiz hatalar.
    if ctx.detached:
        return "01_detached_head"

    # TODO senaryo 08, 09, 10, 12
    return None
