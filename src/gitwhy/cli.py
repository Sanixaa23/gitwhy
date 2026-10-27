"""gitwhy komut satiri arayuzu.

    gitwhy                           son basarisiz git komutunu acikla
    gitwhy explain --stderr DOSYA    verilen hata ciktisini acikla (- = stdin)
    gitwhy capture -- git push       komutu kosar, basarisizsa kaydeder
    gitwhy doctor                    depo sagligi
    gitwhy shell-init [bash|zsh]     sarmalayici shell kodunu yazdirir

Hicbir alt komut depoyu degistirmez. `capture` kullanicinin verdigi komutu
oldugu gibi kosar; kendiliginden komut uretmez.
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

from . import __version__, capture, context, explain, rules

# Sarmalayici iki kabukta da ayni isi yapiyor; tek fark boru hattinin
# cikis kodunu okuma bicimi: bash'te ${PIPESTATUS[0]}, zsh'te
# ${pipestatus[1]} (zsh dizileri 1'den basliyor).
_SARMALAYICI_GOVDE = """# gitwhy sarmalayicisi - {dosya} icine ekle
# Kaldirmak icin: unset -f git
#
# Varsayilan: git'in ciktisina dokunulmaz, yalnizca komut ve cikis kodu
# kaydedilir. Bu haliyle 12 senaryodan 10'u bulunabiliyor.
# GITWHY_TEE=1: stderr ayrica bir dosyaya kopyalanir, boylece push reddi
# (senaryo 7 ve 8) de bulunur. Bedeli: stderr artik terminale dogrudan
# bagli olmadigi icin git ilerleme cubuklarini ("Writing objects: ...")
# yazdirmaz. Istersen ac, varsayilan kapali.
git() {{
  command -v gitwhy >/dev/null 2>&1 || {{ command git "$@"; return $?; }}
  local kod
  if [ "${{GITWHY_TEE:-0}}" = "1" ]; then
    local gw_hata="${{TMPDIR:-/tmp}}/gitwhy-stderr.$$"
    {{ command git "$@" 2>&1 1>&3 | tee "$gw_hata" >&2; }} 3>&1
    kod={pipestatus}
    command gitwhy capture-exit "$kod" "git $*" \\
        --stderr-dosyasi "$gw_hata" >/dev/null 2>&1
    rm -f "$gw_hata"
  else
    command git "$@"
    kod=$?
    command gitwhy capture-exit "$kod" "git $*" >/dev/null 2>&1
  fi
  # 130 = Ctrl-C. Kullanici kendisi kesti, aciklanacak bir hata yok.
  if [ "$kod" -ne 0 ] && [ "$kod" -ne 130 ]; then
    command gitwhy
  fi
  return $kod
}}
"""

SARMALAYICI = {
    "bash": _SARMALAYICI_GOVDE.format(
        dosya="~/.bashrc", pipestatus="${PIPESTATUS[0]}"),
    "zsh": _SARMALAYICI_GOVDE.format(
        dosya="~/.zshrc", pipestatus="${pipestatus[1]}"),
}


def _cikti(metin: str) -> None:
    """Windows konsolunda cp1254 hatasi vermeden yazdirir."""
    try:
        sys.stdout.write(metin + "\n")
    except UnicodeEncodeError:
        kodlama = sys.stdout.encoding or "utf-8"
        sys.stdout.write(metin.encode(kodlama, "replace").decode(kodlama) + "\n")


def _acikla(depo: str, hata_metni: str, komut: str = None) -> int:
    ctx = context.topla(depo)
    senaryo = rules.esle(ctx, hata_metni, komut)
    _cikti(explain.anlat(senaryo, ctx))
    return 0 if senaryo else 1


def komut_son_hata(arg) -> int:
    ctx = context.topla(arg.depo)
    kayit = capture.oku()
    # Baska depoya ait ya da bayatlamis kayit kullanilmaz.
    if not capture.gecerli(kayit, ctx.depo):
        kayit = None
    senaryo = rules.esle(ctx, capture.hata_metni(kayit), capture.komut(kayit))
    # Not duyurusu yalnizca gercekten elimizde bir sey yokken: depo durumu
    # tek basina bir senaryoya eslestiyse ozur dileyecek bir sey yok.
    if senaryo is None and kayit is None:
        _cikti(
            "Kayitli bir hata yok. Deponun su anki durumuna bakiliyor.\n"
            "Belirli bir hatayi aciklamak icin:  gitwhy explain --stderr -\n"
        )
    _cikti(explain.anlat(senaryo, ctx))
    return 0 if senaryo else 1


def komut_explain(arg) -> int:
    if arg.stderr == "-":
        metin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace").read()
    else:
        with open(arg.stderr, encoding="utf-8", errors="replace") as f:
            metin = f.read()
    return _acikla(arg.depo, metin)


def komut_capture(arg) -> int:
    """Verilen komutu kosar; basarisiz olursa kaydeder ve aciklar."""
    if not arg.komut:
        _cikti("Kullanim: gitwhy capture -- git push")
        return 2
    p = subprocess.run(arg.komut, capture_output=True)
    out = p.stdout.decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")
    sys.stdout.write(out)
    sys.stderr.write(err)
    if p.returncode == 0:
        return 0
    capture.yaz(" ".join(arg.komut), p.returncode, out, err, arg.depo)
    _cikti("")
    _acikla(arg.depo, err + "\n" + out, " ".join(arg.komut))
    return p.returncode


def komut_capture_exit(arg) -> int:
    """Shell sarmalayicisi icin kayit.

    Varsayilan olarak cikti zaten ekranda kaldigi icin yalnizca komut ve
    cikis kodu kaydedilir; kurallar metinsiz de 5, 6 ve 11'i bulabiliyor.
    GITWHY_TEE=1 ile sarmalayici stderr'i bir dosyaya da yazar ve o dosyayi
    buraya verir; 7 ve 8 ancak o zaman eslesir.
    """
    metin = ""
    if arg.stderr_dosyasi:
        try:
            with open(arg.stderr_dosyasi, encoding="utf-8", errors="replace") as f:
                metin = f.read()
        except OSError:
            metin = ""
    capture.yaz(arg.komut_metni, arg.kod, "", metin, arg.depo)
    return 0


def komut_doctor(arg) -> int:
    ctx = context.topla(arg.depo)
    if not ctx.gecerli_depo:
        _cikti("Burasi bir git deposu degil: %s" % ctx.depo)
        return 1
    satir = ["# gitwhy doctor — %s" % ctx.depo, ""]
    satir.append("branch            : %s" % (ctx.branch or "(detached)"))
    satir.append("upstream          : %s" % (ctx.upstream or "yok"))
    satir.append("ileri / geri      : +%d / -%d" % (ctx.ileri, ctx.geri))
    satir.append("remote            : %s" % (", ".join(ctx.remoteler) or "yok"))
    satir.append("surmekte islem    : %s" % (", ".join(ctx.surmekte) or "yok"))
    satir.append("cakisan dosya     : %d" % len(ctx.cakisan))
    satir.append("kaydedilmemis     : %d" % len(ctx.kaydedilmemis))
    satir.append("erisilemez commit : %s" % (
        ", ".join("%s (%s)" % (s[:8], konu) for s, konu, _ in ctx.kayip) or "yok"))
    satir.append("user.email        : %s" % (ctx.user_email or "TANIMLI DEGIL"))
    gitignore = os.path.exists(os.path.join(ctx.depo, ".gitignore"))
    satir.append(".gitignore        : %s" % ("var" if gitignore else "YOK"))
    riskli = [y for y in ctx.sahnelenen if _riskli_yol(y)]
    satir.append("sahnelenmis sir   : %s" % (", ".join(riskli) or "yok"))
    _cikti("\n".join(satir))
    return 0


_RISKLI = (".env", "id_rsa", "credentials.json", ".pem", ".p12", ".keystore")


def _riskli_yol(yol: str) -> bool:
    ad = yol.replace("\\", "/").split("/")[-1].lower()
    return any(ad == r or ad.endswith(r) for r in _RISKLI)


def komut_shell_init(arg) -> int:
    kod = SARMALAYICI.get(arg.kabuk)
    if kod is None:
        _cikti("Desteklenen kabuklar: bash, zsh. PowerShell kapsam disi.")
        return 2
    sys.stdout.write(kod)
    return 0


def main(argv=None) -> int:
    ayristirici = argparse.ArgumentParser(
        prog="gitwhy",
        description="Git hatalarini deponun durumunu okuyarak aciklar.",
    )
    ayristirici.add_argument("--version", action="version", version="gitwhy " + __version__)
    ayristirici.add_argument("--depo", default=".", help="incelenecek depo (varsayilan: .)")
    alt = ayristirici.add_subparsers(dest="alt_komut")

    p = alt.add_parser("explain", help="verilen hata ciktisini acikla")
    p.add_argument("--stderr", required=True, help="hata ciktisi dosyasi, - = stdin")
    p.add_argument("--depo", default=".")
    p.set_defaults(islev=komut_explain)

    p = alt.add_parser("capture", help="komutu kosar, basarisizsa aciklar")
    p.add_argument("komut", nargs=argparse.REMAINDER)
    p.add_argument("--depo", default=".")
    p.set_defaults(islev=komut_capture)

    p = alt.add_parser("capture-exit", help="shell sarmalayicisi icin kayit")
    p.add_argument("kod", type=int)
    p.add_argument("komut_metni")
    p.add_argument("--stderr-dosyasi", dest="stderr_dosyasi", default=None,
                   help="GITWHY_TEE=1 modunda sarmalayicinin yazdigi hata dosyasi")
    p.add_argument("--depo", default=".")
    p.set_defaults(islev=komut_capture_exit)

    p = alt.add_parser("doctor", help="depo sagligi")
    p.add_argument("--depo", default=".")
    p.set_defaults(islev=komut_doctor)

    p = alt.add_parser("shell-init", help="sarmalayici shell kodunu yazdirir")
    p.add_argument("kabuk", nargs="?", default="bash", choices=["bash", "zsh"])
    p.set_defaults(islev=komut_shell_init)

    arg = ayristirici.parse_args(argv)
    islev = getattr(arg, "islev", komut_son_hata)
    return islev(arg)


if __name__ == "__main__":
    sys.exit(main())
