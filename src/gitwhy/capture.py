"""Son basarisiz git komutunu diske yazar ve geri okur.

Shell sarmalayicisi (`gitwhy shell-init`) basarisiz bir git komutundan sonra
`gitwhy capture` cagirir; `gitwhy` tek basina cagrildiginda bu kayit okunur.
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional


def onbellek_dizini() -> str:
    """Platforma uygun onbellek dizini. Windows'ta LOCALAPPDATA kullanilir."""
    temel = (
        os.environ.get("GITWHY_CACHE")
        or os.environ.get("XDG_CACHE_HOME")
        or os.environ.get("LOCALAPPDATA")
        or os.path.join(os.path.expanduser("~"), ".cache")
    )
    return os.path.join(temel, "gitwhy")


def kayit_yolu() -> str:
    return os.path.join(onbellek_dizini(), "last.json")


def yaz(komut: str, exit_kodu: int, stdout: str, stderr: str, depo: str = ".") -> str:
    """Son basarisiz komutu kaydeder; yazilan dosyanin yolunu dondurur."""
    kayit = {
        "komut": komut,
        "exit": exit_kodu,
        "stdout": stdout,
        "stderr": stderr,
        "depo": os.path.abspath(depo),
        "zaman": time.time(),
    }
    yol = kayit_yolu()
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(kayit, f, ensure_ascii=False, indent=2)
    return yol


def oku() -> Optional[dict]:
    """Son kaydi okur; kayit yoksa veya bozuksa None."""
    try:
        with open(kayit_yolu(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


AZAMI_YAS = 600.0   # saniye


def gecerli(kayit: Optional[dict], depo: str, azami_yas: float = AZAMI_YAS) -> bool:
    """Kayit SU ANKI depoya ve yakin gecmise mi ait.

    Iki koruma: baska bir depoda kalmis kayit buraya uygulanmasin, ve
    saatler once olmus bir hata bugunku komutun cevabi sanilmasin. Komut
    tabanli kurallar bu kontrole guveniyor.
    """
    if not kayit:
        return False
    kayitli = os.path.normcase(os.path.abspath(kayit.get("depo") or ""))
    simdiki = os.path.normcase(os.path.abspath(depo))
    if kayitli != simdiki:
        return False
    try:
        return (time.time() - float(kayit.get("zaman", 0))) <= azami_yas
    except (TypeError, ValueError):
        return False


def komut(kayit: Optional[dict]) -> Optional[str]:
    return (kayit or {}).get("komut") or None


def hata_metni(kayit: Optional[dict]) -> str:
    """Kayittan karar verilecek metni cikarir.

    stdout ve stderr birlikte doner: git bazi hatalari (CONFLICT) stdout'a
    yaziyor. Fixture testinde dogrulandi.
    """
    if not kayit:
        return ""
    return "\n".join(x for x in (kayit.get("stderr"), kayit.get("stdout")) if x)
