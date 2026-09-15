# Owl Catalog Tools

Отдельный Python-пакет со сборщиком и валидатором каталогов Owl Game.

Он сохраняет формат итогового JSON и способ вычисления `contentHash`.

## Требования

- Python 3.11 или новее.

Сторонних runtime-зависимостей нет.

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
  --commit-sha local
```

Для строгой проверки перед публикацией:

```powershell
python -m owl_catalog_tools `
  --catalog-dir catalog `
  --output build/catalog-release.json `
  --version catalog-v0.1.4 `
  --commit-sha local `
  --require-image-keys
```

После установки доступна эквивалентная команда `owl-catalog`.

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
