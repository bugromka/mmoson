#!/usr/bin/env bash
# purge_nik_from_history.sh — вычистить папку NIK/ из ВСЕЙ истории git.
#
# ЗАЧЕМ: простое `git rm -r NIK` убирает файлы только из текущего коммита.
# В истории они остаются, и любой, кто склонирует репозиторий, достанет их
# командой `git log --all -- NIK` или `git show <старый коммит>`.
#
# ВАЖНО, ПОНИМАТЬ ДО ЗАПУСКА:
#   1. Скрипт меняет хеши ВСЕХ коммитов после первого, где появился NIK.
#      После этого нужен `git push --force` — это перезапись удалённой main.
#   2. GitHub может ещё какое-то время хранить старые объекты в кэше, а форки
#      и чужие клоны сохранят прежнюю историю навсегда. Перезапись истории
#      НЕ равно «никто и никогда не видел». Если содержимое реально секретно —
#      считай его скомпрометированным и меняй сами секреты (пароли, ключи).
#   3. Скрипт делает резервную копию репозитория рядом, прежде чем что-то трогать.
#
# Запуск (из корня репозитория):
#   bash tools/purge_nik_from_history.sh            # только локально
#   bash tools/purge_nik_from_history.sh --push     # локально + force-push в origin/main
#
# Требуется git-filter-repo:  pip install git-filter-repo

set -euo pipefail

BRANCH="main"
PUSH=0
[[ "${1:-}" == "--push" ]] && PUSH=1

log() { printf '\n\033[1m%s\033[0m\n' "$*"; }
die() { printf '\nОШИБКА: %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null || die "нет git"
command -v git-filter-repo >/dev/null || die \
  "нет git-filter-repo. Установи: pip install git-filter-repo"

[[ -d .git ]] || die "запускать из корня репозитория"
[[ -z "$(git status --porcelain)" ]] || die "рабочее дерево не чистое; сначала закоммить или спрячь изменения"

log "1/5 Резервная копия"
BACKUP="../$(basename "$PWD")-backup-$(date +%Y%m%dT%H%M%S)"
git clone --mirror . "$BACKUP.git"
echo "Полное зеркало сохранено: $BACKUP.git"
echo "(это ваш единственный способ откатить перезапись истории — не удаляйте)"

log "2/5 Проверка, что NIK действительно есть в истории"
if ! git log --all --oneline -- NIK | head -1 | grep -q .; then
  echo "В истории NIK/ не найден. Нечего чистить."
  exit 0
fi
echo "Коммитов, затрагивающих NIK/: $(git log --all --oneline -- NIK | wc -l)"

log "3/5 Перезапись истории (удаление NIK/ из всех коммитов)"
git filter-repo --force --invert-paths --path NIK/

log "4/5 Проверка результата"
if git log --all --oneline -- NIK | head -1 | grep -q .; then
  die "NIK всё ещё в истории — разбирайся вручную"
fi
echo "NIK/ в истории отсутствует. Файлов в дереве: $(git ls-files | wc -l)"
echo "Не забудь: git remote add origin <url>, filter-repo удаляет remote."

log "5/5 Публикация"
if [[ $PUSH -eq 1 ]]; then
  git remote add origin "https://github.com/bugromka/The-O-Neill-Space-Station-Simulation-Module.git" 2>/dev/null || true
  git push --force origin "$BRANCH"
  echo "Force-push выполнен. Старые коммиты в веб-интерфейсе GitHub могут оставаться доступны по прямым ссылкам — запроси у поддержки GitHub очистку кэша, если это критично."
else
  cat <<EOF

Локальная история очищена. Чтобы опубликовать:

  git remote add origin https://github.com/bugromka/The-O-Neill-Space-Station-Simulation-Module.git
  git push --force origin $BRANCH

Или перезапусти этот скрипт с --push (учти: он снова сделает бэкап).
EOF
fi
