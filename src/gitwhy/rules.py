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
    "06_upstream_yok",
    "07_push_reddedildi",
    "09_bagimlilik_sahnelendi",
    "10_sir_sahnelendi",
)

# Senaryo 9: sahnelenmemesi gereken dizin adlari. Yol parcasi olarak eslesir,
# yani "src/node_modules/x" de yakalanir.
BAGIMLILIK_DIZINLERI = frozenset({
    "node_modules", "bower_components", "vendor", "venv", ".venv", "env",
    "__pycache__", "site-packages", "dist", "build", "target", ".next",
    ".nuxt", "out", "pods", ".gradle", ".dart_tool", ".terraform",
})

# Senaryo 10: sir tasiyan dosya adlari ve uzantilari.
SIR_ADLARI = frozenset({
    ".env", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "credentials.json",
    "serviceaccount.json", "service-account.json", "secrets.json",
    ".netrc", ".npmrc", ".pypirc", "terraform.tfvars",
})
SIR_UZANTILARI = (".pem", ".p12", ".pfx", ".key", ".keystore", ".jks", ".ppk")

# Bunlar commit edilmek UZERE var: uyari vermemeli. `.env.example` bir sir
# degil, sablondur. Fixture bu dosyayi da sahneliyor; yanlis pozitif testi.
SIR_MUAF_SONLARI = (".example", ".sample", ".template", ".dist", ".tpl", ".default")

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


def _parcalar(yol: str) -> List[str]:
    return [p for p in yol.replace("\\", "/").split("/") if p]


def bagimlilik_yollari(ctx: Baglam) -> List[str]:
    """Sahnelenmis yollardan bagimlilik dizinlerini dondurur.

    Dosya dosya degil, dizin olarak doner: 400 dosya yerine "node_modules".
    Onerilecek komut da dizin uzerinden calisiyor.
    """
    bulunan: List[str] = []
    for yol in ctx.sahnelenen:
        parca = _parcalar(yol)
        for i, p in enumerate(parca):
            if p.lower() in BAGIMLILIK_DIZINLERI:
                onek = "/".join(parca[:i + 1])
                if onek not in bulunan:
                    bulunan.append(onek)
                break
    return bulunan


def sir_mi(yol: str) -> bool:
    """Yol bir sir dosyasi mi. `.env.example` gibi sablonlar haric."""
    parca = _parcalar(yol)
    if not parca:
        return False
    ad = parca[-1].lower()
    if any(ad.endswith(son) for son in SIR_MUAF_SONLARI):
        return False
    if ad in SIR_ADLARI:
        return True
    if ad.startswith(".env."):          # .env.local, .env.production
        return True
    return any(ad.endswith(uzanti) for uzanti in SIR_UZANTILARI)


def sir_yollari(ctx: Baglam) -> List[str]:
    """Sahnelenmis yollardan sir tasiyanlari dondurur."""
    return [y for y in ctx.sahnelenen if sir_mi(y)]


def esle(ctx: Baglam, hata_metni: Optional[str] = None) -> Optional[str]:
    """Durum ve hata metninden senaryo kimligi uretir; eslesme yoksa None.

    SIRALAMA KURALI (fixture testiyle dogrulandi, degistirmeyin):
    Rebase cakismasinin ortasinda `git status` AYNI ANDA
    `# branch.head (detached)` ve `rebase-merge` gosteriyor. Detached HEAD'i
    once kontrol edersen rebase'in ortasindaki kullaniciya "detached
    HEAD'desin" deyip tamamen yanlis komut onerirsin.
    Dogru sira: surmekte olan islem -> cakisma -> hata metni -> durum
    (sir -> bagimlilik -> detached).
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
    if _metinde(hata_metni, "has no upstream branch", "no upstream configured"):
        return "06_upstream_yok"
    # Reddedilen push'ta ctx.geri'ye GUVENILMEZ: git reddedilen push'tan sonra
    # remote-tracking ref'i guncellemiyor, `branch.ab` hala +N -0 gosteriyor.
    # Gercek "geri" sayisi ancak `git fetch` sonrasi ortaya cikiyor ve
    # context.py fetch yapamaz (salt-okunur). Bu yuzden karar metinden.
    if _metinde(hata_metni, "! [rejected]", "non-fast-forward", "fetch first"):
        return "07_push_reddedildi"
    if _metinde(hata_metni, "would be overwritten"):
        return None  # TODO senaryo 11

    # 4) Durumdan okunan, komuttan bagimsiz durumlar.
    #    Sir once: .env'in commit edilmesi geri alinmasi en pahali hata.
    #    Bu blok metin blogundan SONRA: kullanici bir komutun neden
    #    basarisiz oldugunu sorduysa cevap o komut hakkinda olmali.
    if sir_yollari(ctx):
        return "10_sir_sahnelendi"
    if bagimlilik_yollari(ctx):
        return "09_bagimlilik_sahnelendi"
    if ctx.detached:
        return "01_detached_head"

    # TODO senaryo 04, 08, 11, 12
    return None
