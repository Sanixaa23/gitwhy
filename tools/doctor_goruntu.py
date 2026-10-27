"""README icin `gitwhy doctor` ekran goruntusu: docs/doctor.svg + docs/doctor.png

Ekran goruntusu elle alinmiyor: arac gercekten sorunlu bir depo kurup
`gitwhy doctor` kosuyor ve ciktinin kendisini ciziyor. Yani goruntudeki her
satir programin gercek ciktisi.

SVG de uretiliyor cunku GitHub README'de SVG keskin kaliyor ve metin
secilebilir oluyor; PNG baska yerlere yapistirmak icin.

Kullanim:
    python tools/doctor_goruntu.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import shutil
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

from demo import (  # noqa: E402
    DOCS, GITWHY, GIF_RENK, KOK, METIN, ZEMIN, _font, _yaz, kos,
)


def sorunlu_depo():
    """Doctor'un gercekten bulgu uretecegi bir depo kurar.

    Dort ayri sorun: sahnelenmis .env, .gitignore yok, user.email tanimli
    degil, reset --hard ile dusmus bir commit.
    """
    kok = tempfile.mkdtemp(prefix="gitwhy_doctor_")
    depo = os.path.join(kok, "proje")
    os.makedirs(depo)
    kos(depo, ["git", "init", "-q", "-b", "main"])
    _yaz(depo, "app.py", "print('merhaba')\n")
    kos(depo, ["git", "add", "app.py"])
    kos(depo, ["git", "commit", "-qm", "ilk surum"])

    # reset --hard ile dusen commit
    _yaz(depo, "rapor.md", "gece boyu yazilan rapor\n")
    kos(depo, ["git", "add", "rapor.md"])
    kos(depo, ["git", "commit", "-qm", "gece boyu yazilan rapor"])
    kos(depo, ["git", "reset", "--hard", "-q", "HEAD~1"])

    # sahnelenmis .env ve kaydedilmemis degisiklik
    _yaz(depo, ".env", "OPENAI_API_KEY=sahte-demo-degeri\n")
    kos(depo, ["git", "add", ".env"])
    _yaz(depo, "app.py", "print('merhaba dunya')\n")
    return kok, depo


def _doctor_rengi(satir: str) -> str:
    s = satir.strip()
    if s.startswith("# gitwhy"):
        return "baslik"
    if "TANIMLI DEGIL" in satir or ": YOK" in satir:
        return "hata"
    etiket, _, deger = satir.partition(":")
    if etiket.strip() in ("sahnelenmis sir", "erisilemez commit"):
        return "metin" if deger.strip() == "yok" else "hata"
    return "metin"


def svg_yaz(satirlar, yol):
    kw, kh, pad = 8.4, 20.0, 16.0
    en = int(max(len(s) for s in satirlar) * kw + pad * 2)
    boy = int(len(satirlar) * kh + pad * 2)
    kacir = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    renk = {
        "baslik": "#79c0ff", "hata": "#f85149", "metin": "#c9d1d9",
    }
    p = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %d %d" role="img" aria-label="gitwhy doctor ciktisi">'
         % (en, boy, en, boy),
         '<rect width="%d" height="%d" rx="8" fill="#0d1117"/>' % (en, boy),
         '<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
         'font-size="14">']
    for i, s in enumerate(satirlar):
        if not s.strip():
            continue
        y = pad + (i + 1) * kh - 6
        p.append('<text x="%.1f" y="%.1f" fill="%s" xml:space="preserve">%s</text>'
                 % (pad, y, renk[_doctor_rengi(s)], kacir(s)))
    p.append("</g></svg>")
    with open(yol, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(p) + "\n")
    return en, boy


def png_yaz(satirlar, yol):
    from PIL import Image, ImageDraw
    font = _font(15)
    olcu = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    kw = olcu.textlength("M", font=font)
    kh, pad = 20, 16
    en = int(max(len(s) for s in satirlar) * kw + pad * 2)
    boy = len(satirlar) * kh + pad * 2
    renk = {"baslik": GIF_RENK["baslik"], "hata": GIF_RENK["hata"], "metin": METIN}
    img = Image.new("RGB", (en, boy), ZEMIN)
    d = ImageDraw.Draw(img)
    for i, s in enumerate(satirlar):
        d.text((pad, pad + i * kh), s, font=font, fill=renk[_doctor_rengi(s)])
    img.save(yol)
    return en, boy


def main():
    os.makedirs(DOCS, exist_ok=True)
    kok, depo = sorunlu_depo()
    try:
        cikti, kod = kos(depo, GITWHY + ["doctor"])
    finally:
        shutil.rmtree(kok, ignore_errors=True)

    satirlar = cikti.split("\n")
    print(cikti)
    print("\ndoctor exit =", kod)

    svg = os.path.join(DOCS, "doctor.svg")
    png = os.path.join(DOCS, "doctor.png")
    print("doctor.svg  %dx%d  %s" % (*svg_yaz(satirlar, svg), svg))
    print("doctor.png  %dx%d  %s" % (*png_yaz(satirlar, png), png))
    return 0


if __name__ == "__main__":
    sys.exit(main())
