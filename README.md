# Owl Catalog Tools

Отдельный Python-пакет со сборщиком и валидатором каталогов Owl Game.

Пакет основан на `scripts/build_catalog.py` из репозитория русского каталога.
Он сохраняет формат итогового JSON и способ вычисления `contentHash`.

В версии `0.1.1` проверка карт дополнена правилом для RANDOM-слотов локаций:

- шаблоны, указанные в FIXED-слотах, исключаются из случайного выбора;
- для всех RANDOM-слотов должно существовать одновременное распределение по
  уникальным подходящим локациям;
- несколько FIXED-слотов по-прежнему могут ссылаться на одну локацию.

Начиная с версии `0.1.2`, локаль каталога передаётся явно через `--locale`
и записывается в поле `locale` итогового JSON. Для релизных версий проверяется
соответствие локали имени версии: например, `--locale ru` допускает
`catalog-ru-v0.1.4`, но не `catalog-en-v0.1.4` и не старый формат
`catalog-v0.1.4`. Версии разработки вида `dev-<commit>` остаются допустимыми.

Начиная с версии `0.2.0`, строгая проверка может обращаться к публичному
S3-хранилищу:

- проверяет существование каждого уникального `imageKey`;
- проверяет MIME-тип объекта (`.png` должен иметь `image/png`, `.webp` —
  `image/webp` и так далее);
- для мебели сравнивает отношение `width / height` с пиксельным отношением
  сторон изображения;
- повторяет временно неудавшиеся запросы и не загружает один `imageKey`
  несколько раз.

## Требования

- Python 3.11 или новее.
- Доступ к публичному хранилищу изображений — только для проверки с
  `--validate-s3-images`.

Пакет устанавливает Pillow для чтения размеров PNG, WebP и других
поддерживаемых изображений.

## Локальная установка

Из корня репозитория `owl-catalog-tools`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

## Запуск для каталога

Из корня репозитория каталога:

```powershell
python -m owl_catalog_tools `
  --catalog-dir catalog `
  --output build/catalog-release.json `
  --version dev-local `
  --locale ru `
  --commit-sha local
```

Для строгой проверки перед публикацией:

```powershell
python -m owl_catalog_tools `
  --catalog-dir catalog `
  --output build/catalog-release.json `
  --version catalog-ru-v0.1.4 `
  --locale ru `
  --commit-sha local `
  --require-image-keys `
  --validate-s3-images `
  --image-base-url "https://s3.regru.cloud/owlgame/"
```

По умолчанию пропорции мебели могут отличаться от пропорций файла не более
чем на 5%. Порог можно явно изменить, например:

```powershell
--furniture-aspect-ratio-tolerance 0.03
```

Проверяется размер всего изображения, включая прозрачные поля. Поэтому
изображения мебели следует обрезать до тех пропорций, которые должны
использоваться при отрисовке. Обычная проверка без `--validate-s3-images`
остаётся полностью локальной и не требует сети.

После установки доступна эквивалентная команда `owl-catalog`.

## Проверка результата

После сборки проверьте служебные поля итогового файла:

```powershell
python -m owl_catalog_tools `
  --catalog-dir catalog `
  --output build/catalog-release.json `
  --version dev-local `
  --locale ru `
  --commit-sha local

python -c "import json; d=json.load(open('build/catalog-release.json', encoding='utf-8')); print(d['version'], d['locale'], d['contentHash'])"
```

Для указанного примера в конверте должны находиться `version: dev-local` и
`locale: ru`. `contentHash` по-прежнему вычисляется только по содержимому поля
`catalog`, поэтому добавление локали не меняет смысл хеша.

## Тесты

```powershell
python -m unittest discover -s tests -v
```

## Сборка пакета

```powershell
python -m pip install build
python -m build
```

Для подключения из GitHub рекомендуется выпускать тег пакета и фиксировать
его версию в каждом репозитории каталога. Так изменение валидатора не начнёт
влиять на каталоги без явного обновления зависимости.
