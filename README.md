# Rich Messages Demo

Демонстрационный Telegram-бот для `aiogram 3.29.1` и Telegram Bot API 10.1. Проект показывает не декоративный HTML в обычном `sendMessage`, а новый протокол Rich Messages: структурированные документы до 32 768 символов, потоковые rich drafts, редактирование rich-контента, typed AST входящего сообщения, rich inline results, join-request queries и ссылки внутри вариантов опроса.

Версия `aiogram 3.29.1` зафиксирована намеренно. Релиз `3.29.0` отозван из PyPI из-за экспоненциального замедления при валидации вложенных `RichBlock`; `3.29.1` содержит исправление и остаётся в границах Bot API 10.1. `aiogram 3.30.x` уже соответствует Bot API 10.2 и добавляет другой способ формирования исходящих сообщений через `InputRichBlock`.

## Карта возможностей

| Возможность Bot API 10.1 | Как запустить | Реализация | Ограничения |
|---|---|---|---|
| Rich HTML: headings, lists, tables, details, quotes, anchors, formulas | `/rich` | [`content.py`](src/richup_bot/content.py), [`rich.py`](src/richup_bot/routers/rich.py) | Клиент Telegram должен поддерживать Rich Messages |
| GFM-совместимый Rich Markdown | `/markdown` | `InputRichMessage(markdown=...)` | Это не `MarkdownV2`; синтаксис и лимиты отличаются |
| AI-style streaming | `/stream` или кнопка `Streaming Draft` | `sendRichMessageDraft` с одним `draft_id`, затем `sendRichMessage` | Обычный личный диалог с ботом; topics не нужны; draft живёт около 30 секунд |
| Редактирование документа | `/edit` | `editMessageText(rich_message=...)` | Новый файл напрямую при inline-edit загрузить нельзя |
| Входящий typed AST | `/inspect`, затем переслать rich message | `F.rich_message`, `RichMessage.blocks`, `model_dump()` | Доставка forwarded messages зависит от настроек Telegram |
| Rich inline result | `@bot_username` в любом чате | `InputRichMessageContent` | Сначала включить inline mode через `/setinline` у `@BotFather` |
| Link media в poll option | `/poll_links` | `InputPollOption(media=InputMediaLink(...))` | URL должен быть HTTP/HTTPS |
| Join-request query | Создать query-enabled join request | `answer_query()` или `send_webapp()` | Бот должен быть назначен guard bot; для Web App нужен HTTPS |

## Быстрый запуск

Требования: Python `3.12–3.14`, [uv](https://docs.astral.sh/uv/) и токен нового бота от `@BotFather`.

```bash
uv sync --extra dev
```

PowerShell:

```powershell
$env:BOT_TOKEN = "123456789:real-token-from-botfather"
uv run richup-bot
```

Bash:

```bash
export BOT_TOKEN='123456789:real-token-from-botfather'
uv run richup-bot
```

Бот удаляет активный webhook без удаления накопленных updates, регистрирует команды и запускает long polling. Чтобы отбросить старую очередь на старте, установи `DROP_PENDING_UPDATES=true`.

Для локального `.env` можно скопировать `.env.example`, но приложение намеренно не читает dotenv-файлы: токен должен попасть в process environment через shell, IDE, Docker/Kubernetes secret или менеджер секретов. Это убирает лишнюю зависимость и не создаёт ложного ощущения, что `.env` безопасен сам по себе.

## Docker Compose

Требования: Docker Engine или Docker Desktop с Compose v2+.

PowerShell:

```powershell
$env:BOT_TOKEN = "123456789:real-token-from-botfather"
docker compose build
docker compose up -d
```

Bash:

```bash
export BOT_TOKEN='123456789:real-token-from-botfather'
docker compose build
docker compose up -d
```

Compose собирает multi-stage image `richup-telegram:local` и создаёт отдельную именованную bridge-сеть `richup_telegram_net`. Порты на host не публикуются: бот инициирует только исходящие HTTPS-запросы к Telegram. Сеть намеренно не помечена `internal`, иначе Docker заблокирует необходимый egress к Bot API.

Проверка контейнера и сети:

```bash
docker compose ps
docker compose logs --tail=100 -f bot
docker network inspect richup_telegram_net
```

Остановка и удаление контейнера вместе с Compose-сетью:

```bash
docker compose down --remove-orphans
```

Runtime-контейнер запускается от UID/GID `10001`, с read-only root filesystem, `no-new-privileges`, пустым набором Linux capabilities и лимитами `0.5 CPU`, `256 MiB RAM`, `128 PIDs`. Запись разрешена только во временный `tmpfs` `/tmp`; исходники, компиляторы и build-зависимости в runtime layer не копируются.

Compose автоматически читает локальный `.env`, если он есть. Такой способ удобен для разработки, но production token лучше подавать из внешнего secrets manager: environment контейнера доступен пользователю с правами на Docker daemon.

## Сценарий проверки за несколько минут

1. Отправь `/start` и последовательно открой русские разделы меню: каждый раздел заменяет содержимое того же сообщения через `editMessageText(rich_message=...)`.
2. Открой `Rich Markdown`: сравни GFM table, task list, footnote и block formula с обычным MarkdownV2.
3. В обычном личном диалоге нажми `Streaming Draft`, затем `Запустить стриминг`. Topics и `message_thread_id` не требуются: три состояния черновика должны сменить друг друга, после чего появится постоянное итоговое сообщение.
4. Нажми `Редактирование` и переключай ревизии: `message_id` остаётся тем же.
5. Запусти `/poll_links`: у вариантов опроса должны появиться HTTP links.
6. Включи inline mode через `@BotFather`, затем выбери результат `@bot_username` в другом чате.
7. Перешли rich message боту: handler покажет JSON-представление типизированного дерева `RichMessage.blocks`.

## Конфигурация

| Переменная | По умолчанию | Назначение |
|---|---:|---|
| `BOT_TOKEN` | нет | Обязательный BotFather token |
| `STREAM_DELAY_MS` | `350` | Пауза между draft frames, `0..5000` мс |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `DROP_PENDING_UPDATES` | `false` | Удалить накопленные updates при снятии webhook |
| `JOIN_REQUEST_MODE` | `queue` | `queue`, `approve`, `decline` или `webapp` |
| `JOIN_REQUEST_WEB_APP_URL` | пусто | HTTPS URL, обязателен для режима `webapp` |

`queue` — безопасная политика: решение остаётся другим администраторам. `approve` и `decline` автоматически разрешают query-enabled запрос. `webapp` показывает Mini App, но окончательный результат всё равно должен быть отправлен через `answerChatJoinRequestQuery` после проверки подписанных Web App init data; этот backend намеренно не подделан в демо.

## Архитектура

```text
src/richup_bot/
├── __main__.py              CLI и fail-fast конфигурация
├── app.py                   Bot/Dispatcher lifecycle, commands, polling
├── config.py                typed env boundary без global mutable state
├── content.py               чистые builders Rich HTML/Markdown
├── callbacks.py             типизированный CallbackData protocol
├── keyboards.py             UI без бизнес-логики
├── routers/
│   ├── common.py            /start, /help, /menu
│   ├── rich.py              send, stream, edit, poll, AST inspection
│   ├── inline.py            InputRichMessageContent
│   └── join_requests.py     join-request query policy
└── services/
    └── streaming.py         draft lifecycle и финальная персистенция
```

Container boundary задают [`Dockerfile`](Dockerfile), [`.dockerignore`](.dockerignore) и [`compose.yaml`](compose.yaml). Compose не разделяет network namespace с default bridge или другими проектами: сервис подключён только к `richup_telegram_net`.

Контент отделён от Telegram I/O, поэтому сложный markup тестируется без сети. `Dispatcher` создаётся фабрикой, конфигурация immutable, роутеры feature-oriented, callback payload валидируется `CallbackData`. Демо не хранит пользовательское состояние: revision закодирован в кнопке, а каждый stream получает криптографически случайный ненулевой 31-bit `draft_id`.

## Ключевые фрагменты API

Отправка документа:

```python
await bot.send_rich_message(
    chat_id=message.chat.id,
    rich_message=InputRichMessage(html=document),
)
```

Потоковая генерация обязана закончиться постоянным сообщением:

```python
for partial in frames:
    await bot.send_rich_message_draft(
        chat_id=user_id,
        draft_id=draft_id,
        rich_message=InputRichMessage(html=partial),
    )

await bot.send_rich_message(
    chat_id=user_id,
    rich_message=InputRichMessage(html=final_document),
)
```

Rich content в inline query:

```python
InlineQueryResultArticle(
    id="rich-message-10-1",
    title="Rich Messages Demo",
    input_message_content=InputRichMessageContent(
        rich_message=InputRichMessage(markdown="# Result"),
    ),
)
```

В `3.29.x` исходящий `InputRichMessage` задаётся ровно одним полем `html` или `markdown`. Типы `RichBlock*` нужны для разбора ответа Telegram. Поле `blocks` для исходящего payload появляется только в Bot API 10.2 / aiogram 3.30; смешивать эти версии — получить красивый Pydantic error вместо демо.

## Лимиты и эксплуатационные детали

- До 32 768 UTF-8 символов, 500 блоков, 16 уровней вложенности, 50 media attachments и 20 столбцов таблицы.
- `sendRichMessageDraft` принимает только числовой `chat_id` private chat и ненулевой `draft_id`; одинаковый id анимирует изменения одного draft.
- Draft — временный preview примерно на 30 секунд. Без финального `sendRichMessage` пользователь потеряет ответ.
- `<tg-thinking>` допустим только в draft. В итоговый документ он не переносится.
- Автодетект URL, email, mention, hashtag, cashtag, command, phone и bank card включён по умолчанию; `skip_entity_detection=True` его отключает.
- Rich HTML принимает только документированные tags. Пользовательские значения перед вставкой должны проходить `html.escape`; builder делает это для имени пользователя.
- Inline links показывают пользователю confirmation dialog с полным URL.
- Poll link media и remote rich media требуют HTTP/HTTPS URL. Права на отправку соответствующего media по-прежнему проверяет Telegram.

## Проверки

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest -v
uv run pytest -v --cov=src --cov-report=term-missing
```

Тесты не вызывают Telegram API. Они проверяют env boundary, экранирование динамического HTML, exclusive HTML/Markdown payloads, draft lifecycle, callback protocol и фактическую сериализацию новых моделей/методов `aiogram 3.29.1`.

## Диагностика

| Симптом | Причина | Проверка |
|---|---|---|
| `method not found` | Установлен `aiogram < 3.29` или старый local Bot API server | `uv run python -c "import aiogram; print(aiogram.__version__)"` |
| Rich content выглядит обычным текстом | Старый Telegram client | Обновить desktop/mobile client и повторить `/rich` |
| `/stream` отклонён даже в личном диалоге | Запущен старый контейнер с проверкой типа чата через identity | Выполнить `docker compose build --no-cache`, затем `docker compose up -d --force-recreate` |
| `/stream` отклонён в группе | `sendRichMessageDraft` принимает только private chat | Открыть обычный личный диалог с ботом; topics не нужны |
| Inline result не появляется | Inline mode не включён | Выполнить `/setinline` у `@BotFather` |
| Join request handler молчит | У request нет `query_id` или бот не guard bot | Включить query-enabled flow и проверить admin setup |
| Poll option без ссылки | Клиент не поддерживает Bot API 10.1 UI | Обновить клиент; payload проверить тестом `test_protocol_models.py` |
| Polling сообщает об активном webhook | Процесс не смог выполнить `deleteWebhook` | Проверить token, сеть и права локального Bot API endpoint |
| Compose останавливается до build/up | `BOT_TOKEN` не задан | Передать переменную в shell или локальный `.env` |
| Контейнер перезапускается | Telegram недоступен, token неверен или конфигурация невалидна | `docker compose logs --tail=100 bot` |
| `richup_telegram_net` отсутствует | Compose stack не запущен или уже удалён | `docker compose up -d`, затем `docker network inspect richup_telegram_net` |

## Официальные источники

- [Telegram Bot API 10.1 changelog](https://core.telegram.org/bots/api-changelog#june-11-2026)
- [Rich Message formatting and limits](https://core.telegram.org/bots/api#rich-message-formatting-options)
- [aiogram 3.29.1 documentation](https://docs.aiogram.dev/en/v3.29.1/)
- [aiogram changelog: 3.29.0 and 3.29.1](https://docs.aiogram.dev/en/v3.29.1/changelog.html)
- [aiogram package history on PyPI](https://pypi.org/project/aiogram/)
