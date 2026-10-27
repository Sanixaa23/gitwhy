"""Bozuk git depolarini program yoluyla kurar.

Her senaryo icin gercek bir depo, gercek bir bozuk durum ve o durumu ureten
komutun GERCEK hata metni. Olculmus senaryo dogrulugu buradan geliyor:
senaryoyu elle anlatmiyoruz, kuruyoruz.

Hepsi tempfile icinde; `temizle()` hepsini siler.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

# Kullanicinin global git ayarlari testi etkilemesin: var olmayan bir dosyaya
# isaret ediyoruz. os.devnull Windows'ta ("nul") git tarafindan kabul edilmiyor.
_AYAR_YOK = os.path.join(tempfile.gettempdir(), "gitwhy_ayar_yok")

ORTAM = dict(
    os.environ,
    GIT_AUTHOR_NAME="gitwhy test",
    GIT_AUTHOR_EMAIL="test@gitwhy.invalid",
    GIT_COMMITTER_NAME="gitwhy test",
    GIT_COMMITTER_EMAIL="test@gitwhy.invalid",
    GIT_CONFIG_GLOBAL=_AYAR_YOK,
    GIT_CONFIG_SYSTEM=_AYAR_YOK,
    LC_ALL="C",
    GIT_TERMINAL_PROMPT="0",
)

_KOKLER: List[str] = []


@dataclass
class Fixture:
    senaryo_id: str
    depo: str
    hata_metni: str     # komutun gercek ciktisi (stderr + stdout)
    exit_kodu: int


def g(depo: str, *arg: str) -> Tuple[str, str, int]:
    p = subprocess.run(["git", "-C", depo, *arg], capture_output=True, env=ORTAM)
    return (
        p.stdout.decode("utf-8", "replace"),
        p.stderr.decode("utf-8", "replace"),
        p.returncode,
    )


def _yaz(depo: str, ad: str, metin: str) -> None:
    yol = os.path.join(depo, ad)
    if os.path.dirname(ad):
        os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin)


def _yeni_depo() -> str:
    kok = tempfile.mkdtemp(prefix="gitwhy_fix_")
    _KOKLER.append(kok)
    depo = os.path.join(kok, "depo")
    os.makedirs(depo)
    g(depo, "init", "-q", "-b", "main")
    g(depo, "config", "commit.gpgsign", "false")
    _yaz(depo, "a.txt", "satir1\n")
    g(depo, "add", "a.txt")
    g(depo, "commit", "-qm", "ilk commit")
    _yaz(depo, "a.txt", "satir1\nsatir2\n")
    g(depo, "commit", "-qam", "ikinci commit")
    return depo


def _birlestir(out: str, err: str) -> str:
    """git CONFLICT satirini stdout'a yaziyor; ikisini birlikte dondur."""
    return "\n".join(x for x in (err.strip(), out.strip()) if x)


# --- senaryo kurucular -----------------------------------------------------

def _kur_detached() -> Fixture:
    depo = _yeni_depo()
    sha, _, _ = g(depo, "rev-parse", "HEAD~1")
    out, err, rc = g(depo, "checkout", "-q", sha.strip())
    # Bu senaryoda komut basarili; kullanici hatayi sonradan fark eder.
    return Fixture("01_detached_head", depo, _birlestir(out, err), rc)


def _kur_merge_cakismasi() -> Fixture:
    depo = _yeni_depo()
    g(depo, "checkout", "-q", "-b", "ozellik")
    _yaz(depo, "a.txt", "satir1\nOZELLIK\n")
    g(depo, "commit", "-qam", "ozellik tarafi")
    g(depo, "checkout", "-q", "main")
    _yaz(depo, "a.txt", "satir1\nMAIN\n")
    g(depo, "commit", "-qam", "main tarafi")
    out, err, rc = g(depo, "merge", "ozellik")
    return Fixture("02_merge_cakismasi", depo, _birlestir(out, err), rc)


def _kur_rebase_ortasi() -> Fixture:
    depo = _yeni_depo()
    g(depo, "checkout", "-q", "-b", "ozellik", "HEAD~1")
    _yaz(depo, "a.txt", "satir1\nOZELLIK\n")
    g(depo, "commit", "-qam", "ozellik tarafi")
    out, err, rc = g(depo, "rebase", "main")
    return Fixture("03_rebase_ortasi", depo, _birlestir(out, err), rc)


def _kur_remote_yok() -> Fixture:
    depo = _yeni_depo()
    out, err, rc = g(depo, "push")
    return Fixture("05_remote_yok", depo, _birlestir(out, err), rc)


KURUCULAR: Dict[str, Callable[[], Fixture]] = {
    "01_detached_head": _kur_detached,
    "02_merge_cakismasi": _kur_merge_cakismasi,
    "03_rebase_ortasi": _kur_rebase_ortasi,
    "05_remote_yok": _kur_remote_yok,
}

SENARYOLAR = tuple(KURUCULAR)


def kur(senaryo_id: str) -> Fixture:
    """Senaryoyu gercek bir depoda kurar."""
    if senaryo_id not in KURUCULAR:
        raise KeyError("fixture yok: " + senaryo_id)
    return KURUCULAR[senaryo_id]()


def hepsi() -> List[Fixture]:
    return [kur(s) for s in SENARYOLAR]


def temizle() -> None:
    """Kurulan tum gecici depolari siler."""
    while _KOKLER:
        shutil.rmtree(_KOKLER.pop(), ignore_errors=True)
