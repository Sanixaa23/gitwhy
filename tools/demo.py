"""README demo kaydini uretir: docs/demo.gif ve docs/demo.cast.

Neden kayit programi, neden elle cekim degil:

- asciinema'nin Windows surumu yok. Bu depo Windows'ta gelistiriliyor.
- Elle cekimde yazim hatasi, duraklama ve yeniden cekim var. Burada akis
  sabit: her calistirmada ayni GIF cikiyor.
- Ciktinin tamami GERCEK. Bu arac geçici bir depo kurar, komutlari
  gercekten kosar ve yakaladigi bayti oldugu gibi ciziyor. Hicbir satir
  elle yazilmiyor; yoksa GIF bir iddia degil, bir resim olurdu.

Kullanim:
    python tools/demo.py                 # docs/demo.gif + docs/demo.cast
    python tools/demo.py --sadece-cast   # GIF uretmeden .cast

GIF icin Pillow gerekiyor (`pip install pillow`). .cast her durumda uretilir
ve `agg demo.cast demo.gif` ile de GIF'e cevrilebilir.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import shutil
import time

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(KOK, "src")
DOCS = os.path.join(KOK, "docs")

SUTUN, SATIR = 96, 36
ISTEM = "ogrenci@hackathon ~/proje (ozellik) $ "

ORTAM_TEMEL = dict(
    os.environ,
    GIT_AUTHOR_NAME="ogrenci",
    GIT_AUTHOR_EMAIL="ogrenci@okul.edu",
    GIT_COMMITTER_NAME="ogrenci",
    GIT_COMMITTER_EMAIL="ogrenci@okul.edu",
    GIT_CONFIG_GLOBAL=os.path.join(tempfile.gettempdir(), "gitwhy_demo_ayar_yok"),
    GIT_CONFIG_SYSTEM=os.path.join(tempfile.gettempdir(), "gitwhy_demo_ayar_yok"),
    LC_ALL="C",
    GIT_TERMINAL_PROMPT="0",
    PYTHONPATH=SRC,
    PYTHONIOENCODING="utf-8",
    # rebase --continue normalde editor acar; kayitta editor yok.
    GIT_EDITOR="true",
)


def kos(depo, argv):
    """Komutu kosar, terminalde gorunecek sirayla ciktiyi dondurur.

    Gercek terminalde git once stdout'a (Auto-merging, CONFLICT), sonra
    stderr'e (error:, hint:) yaziyor. Yaklasim bu sirayi izliyor.
    """
    p = subprocess.run(argv, cwd=depo, capture_output=True, env=ORTAM_TEMEL)
    out = _temizle(p.stdout.decode("utf-8", "replace"))
    err = _temizle(p.stderr.decode("utf-8", "replace"))
    # stdout satir sonu ile bitmiyorsa araya newline: git ilerleme satirini
    # ("Rebasing (1/1)") satir sonu olmadan yaziyor ve stderr ona yapisiyor.
    if out and err and not out.endswith("\n"):
        out += "\n"
    return (out + err).rstrip("\n"), p.returncode


def _temizle(metin):
    """CR ile ustune yazilan ilerleme ciktisini terminal gibi sadelestirir."""
    metin = metin.replace("\r\n", "\n")
    return "\n".join(s.split("\r")[-1] for s in metin.split("\n"))


def _yaz(depo, ad, metin):
    with open(os.path.join(depo, ad), "w", encoding="utf-8", newline="\n") as f:
        f.write(metin)


def depo_kur():
    """Rebase cakismasina girecek gercek bir depo kurar. Kayitta gorunmez."""
    kok = tempfile.mkdtemp(prefix="gitwhy_demo_")
    depo = os.path.join(kok, "proje")
    os.makedirs(depo)
    kos(depo, ["git", "init", "-q", "-b", "main"])
    _yaz(depo, "a.txt", "baslik\n")
    kos(depo, ["git", "add", "a.txt"])
    kos(depo, ["git", "commit", "-qm", "ilk commit"])
    _yaz(depo, "a.txt", "baslik\nmain tarafindan yazildi\n")
    kos(depo, ["git", "commit", "-qam", "main uzerinde devam"])
    kos(depo, ["git", "checkout", "-q", "-b", "ozellik", "HEAD~1"])
    _yaz(depo, "a.txt", "baslik\nozellik branchinde yazildi\n")
    kos(depo, ["git", "commit", "-qam", "ozellik eklendi"])
    return kok, depo


def cozumu_yaz(depo):
    """Cakismayi kullanicinin yerine cozer: iki tarafi birlestirir."""
    _yaz(depo, "a.txt", "baslik\nmain tarafindan yazildi\nozellik branchinde yazildi\n")
    return "", 0


PY = sys.executable
GITWHY = [PY, "-m", "gitwhy.cli"]

# (ekranda gorunen komut, ne kosulacak, cikti sonrasi bekleme saniyesi)
ADIMLAR = [
    ("git rebase main", ["git", "rebase", "main"], 3.4),
    ("gitwhy", GITWHY, 9.5),
    ("nano a.txt   # cakismayi coz", cozumu_yaz, 1.4),
    ("git add a.txt", ["git", "add", "a.txt"], 0.8),
    ("git rebase --continue", ["git", "rebase", "--continue"], 3.0),
    ("gitwhy doctor", GITWHY + ["doctor"], 4.5),
]

YAZMA_HIZI = 0.045      # saniye/karakter, .cast icin
ISTEM_BEKLEME = 0.75    # komut gorundukten sonra cikti gelene kadar


def kaydi_topla():
    """Adimlari kosar; (istem+komut, cikti) ciftleri ve beklemeleri dondurur."""
    kok, depo = depo_kur()
    kayit = []
    try:
        for goster, is_, bekle in ADIMLAR:
            if callable(is_):
                cikti, _ = is_(depo)
            else:
                cikti, _ = kos(depo, is_)
            kayit.append({"komut": goster, "cikti": cikti, "bekle": bekle})
    finally:
        shutil.rmtree(kok, ignore_errors=True)
    return kayit


# --- asciicast v2 ---------------------------------------------------------

RENK = {
    "istem": "\x1b[32m",
    "komut": "\x1b[97m",
    "hata": "\x1b[31m",
    "ipucu": "\x1b[90m",
    "uyari": "\x1b[33m",
    "baslik": "\x1b[96m",
    "sifirla": "\x1b[0m",
}


def _satir_rengi(satir):
    s = satir.lstrip()
    if s.startswith(("error:", "fatal:", "CONFLICT")):
        return "hata"
    if s.startswith("hint:"):
        return "ipucu"
    if s.startswith("> UYARI"):
        return "uyari"
    if s.startswith("##") or s.startswith("# gitwhy"):
        return "baslik"
    return None


def cast_yaz(kayit, yol):
    olaylar = []
    t = 0.3
    for adim in kayit:
        olaylar.append([round(t, 3), "o", RENK["istem"] + ISTEM + RENK["sifirla"]])
        for ch in adim["komut"]:
            t += YAZMA_HIZI
            olaylar.append([round(t, 3), "o", RENK["komut"] + ch + RENK["sifirla"]])
        t += ISTEM_BEKLEME
        olaylar.append([round(t, 3), "o", "\r\n"])
        if adim["cikti"]:
            for satir in adim["cikti"].split("\n"):
                renk = _satir_rengi(satir)
                metin = (RENK[renk] + satir + RENK["sifirla"]) if renk else satir
                t += 0.03
                olaylar.append([round(t, 3), "o", metin + "\r\n"])
        t += adim["bekle"]
    olaylar.append([round(t, 3), "o", RENK["istem"] + ISTEM + RENK["sifirla"]])

    cast_basligi = {
        "version": 2,
        "width": SUTUN,
        "height": SATIR,
        "timestamp": int(time.time()),
        "title": "gitwhy — rebase cakismasi",
        "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
    }
    with open(yol, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(cast_basligi, ensure_ascii=False) + "\n")
        for o in olaylar:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    return t


# --- GIF ------------------------------------------------------------------

ZEMIN = (13, 17, 23)
METIN = (201, 209, 217)
GIF_RENK = {
    "istem": (63, 185, 80),
    "komut": (230, 237, 243),
    "hata": (248, 81, 73),
    "ipucu": (110, 118, 129),
    "uyari": (210, 153, 34),
    "baslik": (121, 192, 255),
}

FONT_YOLLARI = (
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\lucon.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Menlo.ttc",
)


def _font(boyut=15):
    from PIL import ImageFont
    for yol in FONT_YOLLARI:
        if os.path.exists(yol):
            return ImageFont.truetype(yol, boyut)
    raise SystemExit(
        "Tek genislikli font bulunamadi. Su yollardan birini saglayin:\n  "
        + "\n  ".join(FONT_YOLLARI)
    )


def _sar(satir, genislik):
    """Uzun satiri terminal gibi sarar."""
    if len(satir) <= genislik:
        return [satir]
    parca = []
    while satir:
        parca.append(satir[:genislik])
        satir = satir[genislik:]
    return parca


def gif_yaz(kayit, yol):
    """Her adim icin iki kare: komut gorunur, sonra cikti. Bekleme kare
    suresiyle veriliyor, bu yuzden GIF 20 kareden kucuk kaliyor."""
    from PIL import Image, ImageDraw

    font = _font(15)
    olcu = Image.new("RGB", (10, 10))
    kalem = ImageDraw.Draw(olcu)
    kw = kalem.textlength("M", font=font)
    kh = 20
    pad = 14
    en = int(SUTUN * kw) + pad * 2
    boy = SATIR * kh + pad * 2

    ekran = []   # (metin, renk_adi|None)

    def kare(sure, imlec=False):
        gorunur = ekran[-SATIR:]
        img = Image.new("RGB", (en, boy), ZEMIN)
        d = ImageDraw.Draw(img)
        for i, (metin, renk) in enumerate(gorunur):
            y = pad + i * kh
            if renk == "istem_komut":
                d.text((pad, y), ISTEM, font=font, fill=GIF_RENK["istem"])
                d.text((pad + kw * len(ISTEM), y), metin, font=font,
                       fill=GIF_RENK["komut"])
                if imlec and i == len(gorunur) - 1:
                    x = pad + kw * (len(ISTEM) + len(metin))
                    d.rectangle([x, y + 2, x + kw, y + kh - 4],
                                fill=GIF_RENK["komut"])
            else:
                d.text((pad, y), metin, font=font,
                       fill=GIF_RENK.get(renk, METIN))
        kareler.append(img)
        sureler.append(int(sure * 1000))

    kareler, sureler = [], []
    kare(0.6)
    for adim in kayit:
        ekran.append((adim["komut"], "istem_komut"))
        kare(ISTEM_BEKLEME, imlec=True)
        if adim["cikti"]:
            for satir in adim["cikti"].split("\n"):
                renk = _satir_rengi(satir)
                for p in _sar(satir, SUTUN):
                    ekran.append((p, renk))
        ekran.append(("", None))
        kare(adim["bekle"])
    kare(2.0)

    kareler[0].save(
        yol, save_all=True, append_images=kareler[1:],
        duration=sureler, loop=0, optimize=True, disposal=2,
    )
    return sum(sureler) / 1000.0, len(kareler)


def main():
    ap = argparse.ArgumentParser(description="README demo kaydini uretir")
    ap.add_argument("--sadece-cast", action="store_true")
    arg = ap.parse_args()

    os.makedirs(DOCS, exist_ok=True)
    kayit = kaydi_topla()

    cast_yolu = os.path.join(DOCS, "demo.cast")
    sure = cast_yaz(kayit, cast_yolu)
    print("demo.cast  %6.1f s  %s" % (sure, cast_yolu))

    if arg.sadece_cast:
        return 0
    gif_yolu = os.path.join(DOCS, "demo.gif")
    gif_sure, kare_sayisi = gif_yaz(kayit, gif_yolu)
    print("demo.gif   %6.1f s  %d kare  %.0f KB  %s" % (
        gif_sure, kare_sayisi, os.path.getsize(gif_yolu) / 1024, gif_yolu))
    if not 20 <= gif_sure <= 30:
        print("UYARI: hedef 20-30 s, suan %.1f s. ADIMLAR'daki beklemeleri ayarla."
              % gif_sure)
    return 0


if __name__ == "__main__":
    sys.exit(main())
