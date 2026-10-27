#!/usr/bin/env bash
# asciinema ile gercek terminal kaydi almak icin akis.
# Windows'ta asciinema yok; orada `python tools/demo.py` ayni akisi uretiyor.
#
# Kullanim (Linux / macOS / WSL):
#   asciinema rec docs/demo.cast --cols 96 --rows 36 --overwrite \
#       --idle-time-limit 2 -c "bash tools/demo_akis.sh"
#   agg --font-size 15 --theme github-dark docs/demo.cast docs/demo.gif
#
# Depo gecici bir dizinde kuruluyor; senin depona dokunmaz.
set -u

KOK="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$KOK/src"
export PYTHONIOENCODING=utf-8
export GIT_AUTHOR_NAME=ogrenci GIT_AUTHOR_EMAIL=ogrenci@okul.edu
export GIT_COMMITTER_NAME=ogrenci GIT_COMMITTER_EMAIL=ogrenci@okul.edu
export GIT_EDITOR=true
export LC_ALL=C
# Kullanicinin global git ayari kayda karismasin (ornegin core.autocrlf
# uyarilari). Var olmayan bir dosyaya isaret ediyoruz.
export GIT_CONFIG_GLOBAL="${TMPDIR:-/tmp}/gitwhy_demo_ayar_yok"
export GIT_CONFIG_SYSTEM="$GIT_CONFIG_GLOBAL"

ISTEM='ogrenci@hackathon ~/proje (ozellik) $ '
gitwhy() { python -m gitwhy.cli "$@"; }

# Komutu karakter karakter yazar, sonra calistirir.
yaz() {
  printf '%s' "$ISTEM"
  local metin="$1"
  for ((i = 0; i < ${#metin}; i++)); do
    printf '%s' "${metin:i:1}"
    sleep 0.045
  done
  printf '\n'
  sleep 0.5
}

CALISMA="$(mktemp -d)"
trap 'rm -rf "$CALISMA"' EXIT
cd "$CALISMA" || exit 1

# --- kayda girmeyen hazirlik: rebase cakismasina girecek depo -------------
git init -q -b main proje
cd proje || exit 1
printf 'baslik\n' > a.txt
git add a.txt && git commit -qm "ilk commit"
printf 'baslik\nmain tarafindan yazildi\n' > a.txt
git commit -qam "main uzerinde devam"
git checkout -q -b ozellik HEAD~1
printf 'baslik\nozellik branchinde yazildi\n' > a.txt
git commit -qam "ozellik eklendi"
clear

# --- kayit -----------------------------------------------------------------
yaz 'git rebase main'
git rebase main
sleep 3.4

yaz 'gitwhy'
gitwhy
sleep 9.5

yaz 'nano a.txt   # cakismayi coz'
printf 'baslik\nmain tarafindan yazildi\nozellik branchinde yazildi\n' > a.txt
sleep 1.4

yaz 'git add a.txt'
git add a.txt
sleep 0.8

yaz 'git rebase --continue'
git rebase --continue
sleep 3.0

yaz 'gitwhy doctor'
gitwhy doctor
sleep 4.5

printf '%s' "$ISTEM"
sleep 2
