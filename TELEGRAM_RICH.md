# Задание агенту: перенести новые возможности Telegram в существующего бота

> Этот файл — самостоятельное техническое задание для coding agent. Передай его агенту вместе с репозиторием старого бота. Если рядом доступен демонстрационный репозиторий `richup-telegram`, используй его как рабочий reference, но не копируй его целиком.

## Роль и цель

Ты — senior Python/Telegram engineer. Твоя задача — изучить существующего бота, безопасно обновить его Telegram-стек и встроить возможности Rich Messages, появившиеся в Telegram Bot API 10.1. Не превращай production-бота в копию демо: сохрани его архитектуру, команды, бизнес-логику, хранилище, middleware, webhook/polling и способ деплоя.

Работай автономно: сначала исследуй репозиторий, затем реализуй перенос, обнови тесты и документацию и выполни доступные проверки. Не ограничивайся планом или примерами кода — внеси законченные изменения. Не трогай несвязанные части проекта и не переписывай пользовательские изменения.

## Версии и границы совместимости

Состояние экосистемы на **5 августа 2026 года**:

- Telegram Bot API 10.1 от 11 июня 2026 года добавил Rich Messages, rich drafts, rich inline content, join-request queries и link media для вариантов опроса.
- Reference-проект проверен на `aiogram==3.29.1` и Python 3.12–3.14.
- `aiogram 3.29.0` использовать нельзя: релиз отозван из PyPI из-за резкого замедления при разборе вложенных `RichBlock`.
- Telegram Bot API 10.2 и `aiogram==3.30.0` уже выпущены. В 10.2 у `InputRichMessage` появились исходящие `blocks` и `media`, а также семейство `InputRichBlock*`.

Сначала выбери и зафиксируй одну стратегию:

1. **Рекомендуемая для актуализируемого aiogram 3.x-проекта:** `aiogram==3.30.0`. Реализуй возможности 10.1 через стабильные `html`/`markdown`; применяй новые `blocks`/`media` 10.2 только там, где это действительно нужно продукту.
2. **Точное воспроизведение reference-проекта:** `aiogram==3.29.1`. У исходящего `InputRichMessage` используй ровно одно из полей `html` или `markdown`; не используй `InputRichBlock*` и поле `blocks` для исходящего сообщения.
3. Если проект на aiogram 2.x, сначала оцени полный переход на aiogram 3.x как отдельную major migration: Executor заменён на `Dispatcher.start_polling`, фильтры и middleware имеют другой интерфейс, параметры бота больше нельзя передавать через старые глобальные подходы. Не делай механическую замену импортов.
4. Если проект не использует aiogram, не внедряй aiogram только ради этой задачи. Используй типы/методы его текущего фреймворка, если тот поддерживает Bot API 10.1+, либо минимальный строго изолированный вызов Bot API. Объясни выбранный путь.

Не используй диапазон зависимости вроде `aiogram>=3.29`: он может молча изменить протокол моделей. Закрепи проверенную точную версию и обнови lock-файл штатным менеджером пакетов проекта.

## Источники истины

При расхождении данных используй такой приоритет:

1. официальная текущая спецификация Telegram Bot API;
2. документация выбранной закреплённой версии aiogram;
3. сериализация реально установленных моделей и методов;
4. reference-реализация;
5. этот документ.

Официальные ссылки:

- Telegram Bot API changelog: <https://core.telegram.org/bots/api-changelog#june-11-2026>
- Rich Message formatting и лимиты: <https://core.telegram.org/bots/api#rich-message-formatting-options>
- Telegram Bot API: <https://core.telegram.org/bots/api>
- aiogram 3.29.1: <https://docs.aiogram.dev/en/v3.29.1/>
- актуальная документация aiogram 3.30.0: <https://docs.aiogram.dev/en/latest/>
- история релизов aiogram: <https://pypi.org/project/aiogram/>

Если у тебя есть доступ в интернет, перед изменением зависимостей проверь эти страницы. Не заменяй официальные сведения статьями и случайными примерами.

## Сначала исследуй старый проект

До редактирования найди и кратко зафиксируй:

- версию Python, Telegram-фреймворк и его версию, Pydantic, менеджер зависимостей и lock-файл;
- точки создания `Bot`/`Dispatcher`, подключения router/handler, startup/shutdown, webhook или polling;
- существующие default `parse_mode`, обёртки отправки/редактирования, retry/rate-limit middleware и обработку Telegram API errors;
- команды, callback protocol, FSM, локализацию и места генерации сообщений;
- catch-all handlers: новый `F.rich_message` не должен быть перехвачен раньше общим handler;
- способ регистрации `allowed_updates`; `chat_join_request` и `inline_query` должны реально доходить до приложения;
- тестовый стек, Docker/CI и ограничения минимальной версии Python;
- используется ли self-hosted Telegram Bot API server и поддерживает ли он требуемую версию.

После исследования составь короткую карту «существующий компонент → место интеграции». Адаптируй имена модулей к проекту. Не создавай параллельную архитектуру, если в проекте уже есть подходящие service/router/content слои.

## Что требуется перенести

### 1. Отправка Rich HTML и Rich Markdown

Базовая отправка:

```python
from aiogram.types import InputRichMessage

await bot.send_rich_message(
    chat_id=message.chat.id,
    message_thread_id=message.message_thread_id,
    rich_message=InputRichMessage(
        html="<h1>Заголовок</h1><p>Структурированный <b>ответ</b>.</p>"
    ),
)
```

Markdown-вариант:

```python
rich_message = InputRichMessage(
    markdown="# Заголовок\n\n| Поле | Значение |\n|---|---|\n| Статус | Готово |"
)
```

Rich Markdown близок к GitHub Flavored Markdown и **не является MarkdownV2**. Не пропускай Rich HTML через старый `parse_mode`, а Rich Markdown — через существующий MarkdownV2 escaper.

В один `InputRichMessage` передавай ровно один формат:

- в aiogram 3.29.1: `html` **или** `markdown`;
- в aiogram 3.30.0: `html`, `markdown` **или** `blocks`.

Вынеси построение сложного контента в чистые builder-функции. Любые динамические значения пользователя в HTML пропускай через `html.escape`, включая имя, title, введённый текст и подписи. URL валидируй отдельно по допустимой схеме.

Минимальный набор, который следует продемонстрировать в подходящей существующей команде или экране: заголовок, параграф, inline formatting, список, таблица, `details`, цитата, ссылка и формула. Не добавляй отдельное демо-меню, если продуктовый интерфейс позволяет показать эти возможности естественно.

Основные ограничения rich-документа:

- до 32 768 UTF-8 символов;
- до 500 блоков с учётом вложенных;
- до 16 уровней вложенности;
- до 50 media attachments;
- до 20 столбцов таблицы;
- media разрешено только отдельным блоком; remote media использует HTTP/HTTPS;
- ячейки таблицы содержат только inline formatting;
- формулы интерпретируются как raw LaTeX;
- `skip_entity_detection=True` отключает автодетект URL, email, mention, hashtag, cashtag, bot command, phone и других поддерживаемых сущностей.

#### Полный справочник Rich HTML

Не путай этот синтаксис с HTML для обычного `sendMessage`: он передаётся только в `InputRichMessage(html=...)`. Telegram принимает только документированные теги.

Inline-форматирование:

| Назначение | Rich HTML | Примечание |
|---|---|---|
| Жирный | `<b>...</b>`, `<strong>...</strong>` | Теги эквивалентны |
| Курсив | `<i>...</i>`, `<em>...</em>` | Теги эквивалентны |
| Подчёркивание | `<u>...</u>`, `<ins>...</ins>` | Теги эквивалентны |
| Зачёркивание | `<s>...</s>`, `<strike>...</strike>`, `<del>...</del>` | Теги эквивалентны |
| Inline code | `<code>...</code>` | Язык у отдельного `code` не задаётся |
| Выделение | `<mark>...</mark>` | Аналог highlight |
| Нижний/верхний индекс | `<sub>...</sub>`, `<sup>...</sup>` | Например H₂O и x² |
| Спойлер | `<tg-spoiler>...</tg-spoiler>` | Скрывается до нажатия |
| Перенос строки | `<br/>` | Внутри текстового блока |
| Inline LaTeX | `<tg-math>x^2+y^2</tg-math>` | Содержимое — raw LaTeX |
| Custom emoji | `<tg-emoji emoji-id="ID">🙂</tg-emoji>` | Текст — fallback/alt |
| Custom emoji, альтернативная форма | `<img src="tg://emoji?id=ID" alt="🙂"/>` | Это inline emoji, не media block |
| Локализованное время | `<tg-time unix="UNIX" format="wDT">fallback</tg-time>` | Формат сверять с date-time entity docs |

Ссылки, anchors и references:

```html
<p>
  <a href="https://example.com/docs">Обычный URL</a><br/>
  <a href="mailto:support@example.com">Email</a><br/>
  <a href="tel:+79990000000">Телефон</a><br/>
  <a href="tg://user?id=123456789">Упоминание по user id</a><br/>
  <a href="#install">Перейти к разделу внутри документа</a><br/>
  <a href="#note-security">Открыть примечание</a>
</p>

<a name="install"></a>
<h2>Установка</h2>
<p>Содержимое раздела.</p>

<tg-reference name="note-security">
  Никогда не вставляйте bot token в сообщение или лог.
</tg-reference>
```

Пустой `<a name="..."></a>` должен быть отдельным элементом и создаёт anchor. `<tg-reference name="...">...</tg-reference>` создаёт текст примечания, на который ссылаются через `href="#..."`. Telegram-клиент показывает подтверждение с полным URL перед открытием внешней inline-ссылки.

Структурные блоки:

| Назначение | Rich HTML |
|---|---|
| Заголовки | `<h1>` … `<h6>` |
| Параграф | `<p>...</p>` |
| Блок кода | `<pre>...</pre>` |
| Блок кода с языком | `<pre><code class="language-python">...</code></pre>` |
| Подвал | `<footer>...</footer>` |
| Разделитель | `<hr/>` |
| Маркированный список | `<ul><li>...</li></ul>` |
| Нумерованный список | `<ol><li>...</li></ol>` |
| Task list | `<ul><li><input type="checkbox" checked>...</li></ul>` |
| Блочная цитата | `<blockquote>...<cite>Автор</cite></blockquote>` |
| Выносная цитата | `<aside>...<cite>Автор</cite></aside>` |
| Раскрываемый блок | `<details><summary>...</summary>...</details>` |
| Открытый details | `<details open><summary>...</summary>...</details>` |
| Блочная формула | `<tg-math-block>...</tg-math-block>` |
| Карта | `<tg-map lat="55.75" long="37.62" zoom="12"/>` |
| Состояние размышления | `<tg-thinking>...</tg-thinking>` — только draft |

Полный пример списков:

```html
<h2>Списки</h2>

<ul>
  <li>Первый пункт</li>
  <li><b>Второй</b> пункт с inline-форматированием</li>
</ul>

<ol start="3" type="a" reversed>
  <li>Нумерация начинается с трёх</li>
  <li value="7" type="i">Явное значение и римский тип</li>
</ol>

<ul>
  <li><input type="checkbox" checked> Выполнено</li>
  <li><input type="checkbox"> Ещё не выполнено</li>
</ul>
```

Для `<ol>` доступны `start`, `type` и `reversed`; для отдельного `<li>` — `value` и `type`. Вложенные списки учитываются в лимит глубины и блоков.

##### Таблицы Rich HTML — полный пример

```python
from aiogram.types import InputRichMessage


def build_report_table() -> InputRichMessage:
    return InputRichMessage(
        html="""
<h2>Отчёт</h2>
<table bordered striped>
  <caption>Результаты за август</caption>
  <tr>
    <th align="left">Метрика</th>
    <th align="center">План</th>
    <th align="right">Факт</th>
  </tr>
  <tr>
    <td align="left">Заявки</td>
    <td align="center">100</td>
    <td align="right"><mark>124</mark></td>
  </tr>
  <tr>
    <td rowspan="2" valign="middle">Качество</td>
    <td>Успешные</td>
    <td align="right"><b>97%</b></td>
  </tr>
  <tr>
    <td colspan="2" align="center">SLA выполнен</td>
  </tr>
</table>
<footer>Не более 20 столбцов; внутри ячеек — только inline formatting.</footer>
""".strip()
    )
```

Поддерживаемые элементы и атрибуты таблицы:

- `<table bordered striped>` включает границы и полосатые строки; флаги можно применять независимо;
- `<caption>` задаёт подпись таблицы;
- `<tr>` создаёт строку, `<th>` — заголовочную ячейку, `<td>` — обычную;
- `colspan="N"` и `rowspan="N"` объединяют ячейки;
- `align="left|center|right"` задаёт горизонтальное выравнивание;
- `valign="top|middle|bottom"` задаёт вертикальное выравнивание;
- ячейка не должна содержать заголовки, списки, другую таблицу или иной block content — только текст и inline formatting.

##### Media, figure, map, collage и slideshow

```html
<h2>Медиа</h2>

<img src="https://cdn.example.com/photo.jpg"/>
<video src="https://cdn.example.com/video.mp4"></video>
<audio src="https://cdn.example.com/audio.mp3"></audio>

<figure>
  <img src="https://cdn.example.com/photo.jpg" tg-spoiler/>
  <figcaption>Подпись фотографии<cite>Автор</cite></figcaption>
</figure>

<figure>
  <tg-map lat="55.75" long="37.62" zoom="12"/>
  <figcaption>Точка встречи</figcaption>
</figure>

<tg-collage>
  <img src="https://cdn.example.com/one.jpg"/>
  <video src="https://cdn.example.com/two.mp4"></video>
  <figcaption>Общая подпись коллажа<cite>Редакция</cite></figcaption>
</tg-collage>

<tg-slideshow>
  <img src="https://cdn.example.com/step-1.jpg"/>
  <img src="https://cdn.example.com/step-2.jpg"/>
  <figcaption>Пошаговая инструкция</figcaption>
</tg-slideshow>
```

Media type определяется сервером по MIME type и URL. Фото, видео и аудио задаются отдельными блоками, а не помещаются внутрь `<p>` или ячейки таблицы. `tg-spoiler` скрывает поддерживаемое визуальное media. `<cite>` внутри `<figcaption>` задаёт credit.

#### Полный справочник Rich Markdown

````markdown
# Заголовок H1
## Заголовок H2
### Заголовок H3
#### Заголовок H4
##### Заголовок H5
###### Заголовок H6

**жирный** и __тоже жирный__
*курсив* и _тоже курсив_
~~зачёркнутый~~
==выделенный==
||спойлер||
`inline code`
$x^2 + y^2$

[Сайт](https://example.com)
[Email](mailto:support@example.com)
[Телефон](tel:+79990000000)
[Пользователь](tg://user?id=123456789)
![🙂](tg://emoji?id=5368324170671202286)
![Локальное время](tg://time?unix=1785949200&format=wDT)

```python
print("code block with language")
```

---

- Маркированный пункт
  - Вложенный пункт
- Ещё один пункт

1. Первый шаг
2. Второй шаг

- [x] Выполненная задача
- [ ] Невыполненная задача

> Блочная цитата
>
> Продолжение цитаты после пустой строки

| Колонка слева | По центру | Справа |
|:--------------|:---------:|-------:|
| alpha         | **42**    | 99.5%  |

Текст со сноской[^security].

[^security]: Секреты должны поступать из безопасного хранилища.

$$
throughput = useful\_result / latency
$$
````

Внутри внешнего Markdown-файла тройные backticks из примера должны быть корректно вложены или вынесены в Python multiline string. Для программной отправки:

```python
from aiogram.types import InputRichMessage

document = """
# Сводка

| Возможность | Статус |
|:------------|-------:|
| Rich table  | **OK** |

- [x] Данные проверены
- [ ] Отчёт подтверждён

Формула: $E = mc^2$.
""".strip()

rich_message = InputRichMessage(markdown=document)
```

Markdown media является отдельным блоком. Необязательный title используется как caption:

```markdown
![](https://cdn.example.com/photo.jpg "Подпись фото")
![](https://cdn.example.com/video.mp4 "Подпись видео")
![](https://cdn.example.com/audio.mp3 "Подпись аудио")
![](https://cdn.example.com/voice.ogg "Подпись voice note")
![](https://cdn.example.com/animation.gif "Подпись анимации")
```

Rich Markdown допускает поддерживаемые Rich HTML-теги для возможностей без собственного Markdown-синтаксиса: `<u>`, `<ins>`, `<sub>`, `<sup>`, anchors, `<aside>`, `<details>`, `<tg-map>`, `<tg-collage>` и `<tg-slideshow>`. Markdown внутри block HTML обычно не разбирается; исключения — содержимое `<details>`, `<tg-collage>` и `<tg-slideshow>`.

#### Полный готовый Rich HTML builder

Этот builder можно адаптировать для smoke test. Все динамические значения экранируются до интерполяции:

```python
from html import escape

from aiogram.types import InputRichMessage


def build_rich_showcase(*, first_name: str, user_id: int) -> InputRichMessage:
    safe_name = escape(first_name)
    return InputRichMessage(
        html=f"""
<a name="top"></a>
<h1>Rich Messages</h1>
<p>Привет, <b>{safe_name}</b>! Здесь есть <i>курсив</i>, <u>подчёркивание</u>,
<s>зачёркивание</s>, <mark>выделение</mark>, H<sub>2</sub>O, x<sup>2</sup>,
<tg-spoiler>спойлер</tg-spoiler> и <code>inline code</code>.</p>

<p><a href="tg://user?id={user_id}">Ваш профиль</a> ·
<a href="#details">Перейти к деталям</a></p>

<h2>Список</h2>
<ul><li>Первый пункт</li><li><b>Второй пункт</b></li></ul>

<h2>Таблица</h2>
<table bordered striped>
  <caption>Состояние функций</caption>
  <tr><th>Функция</th><th align="right">Статус</th></tr>
  <tr><td>Rich HTML</td><td align="right"><mark>Готово</mark></td></tr>
  <tr><td>Streaming</td><td align="right">Готово</td></tr>
</table>

<a name="details"></a>
<details open><summary>Технические детали</summary>
  <p>Rich message допускает структурные блоки и формулу
  <tg-math>x = (-b + sqrt(b^2-4ac)) / 2a</tg-math>.</p>
  <blockquote>Draft нужно завершить постоянным сообщением.<cite>Bot API</cite></blockquote>
</details>

<tg-reference name="limits">Лимит текста — 32 768 UTF-8 символов.</tg-reference>
<p><a href="#limits">Показать ограничения</a> · <a href="#top">Наверх</a></p>
<footer>Сгенерировано ботом</footer>
""".strip()
    )
```

#### Bot API 10.2 / aiogram 3.30.0: локальные media attachments

В 10.2 HTML/Markdown может ссылаться на элементы массива `media` по внутреннему id. Это позволяет использовать Telegram `file_id` или загрузить новый файл, не подставляя публичный HTTP URL:

```python
from aiogram.types import (
    FSInputFile,
    InputMediaPhoto,
    InputRichMessage,
    InputRichMessageMedia,
)

rich_message = InputRichMessage(
    html="""
<h2>Отчёт с вложением</h2>
<figure>
  <img src="tg://photo?id=chart"/>
  <figcaption>График за август</figcaption>
</figure>
""".strip(),
    media=[
        InputRichMessageMedia(
            id="chart",
            media=InputMediaPhoto(media=FSInputFile("artifacts/chart.png")),
        )
    ],
)
```

`InputRichMessageMedia.id` имеет длину 1–64 и использует только `A-Z`, `a-z`, `0-9`, `_`, `-`. В HTML/Markdown доступны ссылки `tg://photo?id=...`, `tg://video?id=...`, `tg://audio?id=...`. Поле `media` дополняет выбранный `html`/`markdown` и не является четвёртым форматом контента. Этот API отсутствует в aiogram 3.29.1.

#### Bot API 10.2 / aiogram 3.30.0: explicit `InputRichBlock*`

Вместо строки HTML/Markdown можно передать `blocks=[...]`. Используй только на `aiogram 3.30.0` и не передавай одновременно `html` или `markdown`:

```python
from aiogram.types import (
    InputRichBlockDetails,
    InputRichBlockDivider,
    InputRichBlockParagraph,
    InputRichBlockSectionHeading,
    InputRichMessage,
)

rich_message = InputRichMessage(
    blocks=[
        InputRichBlockSectionHeading(text="Системный отчёт", size=1),
        InputRichBlockParagraph(text="Сервис работает штатно."),
        InputRichBlockDivider(),
        InputRichBlockDetails(
            summary="Диагностика",
            is_open=True,
            blocks=[
                InputRichBlockParagraph(text="Ошибок за последний час: 0"),
            ],
        ),
    ]
)
```

Таблица через explicit blocks:

```python
from aiogram.types import InputRichBlockTable, InputRichMessage, RichBlockTableCell


def cell(
    text: str,
    *,
    header: bool = False,
    align: str = "left",
    valign: str = "middle",
) -> RichBlockTableCell:
    return RichBlockTableCell(
        text=text,
        is_header=header,
        align=align,
        valign=valign,
    )


rich_table = InputRichMessage(
    blocks=[
        InputRichBlockTable(
            caption="Состояние сервисов",
            is_bordered=True,
            is_striped=True,
            cells=[
                [
                    cell("Сервис", header=True),
                    cell("Latency", header=True, align="right"),
                    cell("Статус", header=True, align="center"),
                ],
                [
                    cell("API"),
                    cell("42 ms", align="right"),
                    cell("OK", align="center"),
                ],
            ],
        )
    ]
)
```

У `RichBlockTableCell` обязательны `align` (`left`, `center`, `right`) и `valign` (`top`, `middle`, `bottom`); доступны `text`, `is_header`, `colspan` и `rowspan`. Даже если HTML-представление проще, serialization test для explicit table обязателен.

Полный набор исходящих block types 10.2, который агент должен знать и сопоставлять с HTML-вариантом:

| `InputRichBlock*` | Эквивалент/назначение |
|---|---|
| `Paragraph` | `<p>` |
| `SectionHeading` | `<h1>` … `<h6>`; `size=1..6` |
| `Preformatted` | `<pre>` |
| `Footer` | `<footer>` |
| `Divider` | `<hr/>` |
| `MathematicalExpression` | `<tg-math-block>` |
| `Anchor` | `<a name="...">` |
| `List` + `ListItem` | `<ul>`/`<ol>` + `<li>`, включая checkbox/value |
| `BlockQuotation` | `<blockquote>` |
| `PullQuotation` | `<aside>` |
| `Collage` | `<tg-collage>` |
| `Slideshow` | `<tg-slideshow>` |
| `Table` | `<table>` |
| `Details` | `<details>` |
| `Map` | `<tg-map>` |
| `Animation` | animation block |
| `Audio` | audio block |
| `Photo` | photo block |
| `Video` | video block |
| `VoiceNote` | voice-note block |
| `Thinking` | `<tg-thinking>`, только draft |

Для inline-форматирования внутри explicit blocks используются `RichText*` response/input-compatible модели: bold, italic, underline, strikethrough, spoiler, date-time, text mention, subscript, superscript, marked, code, custom emoji, mathematical expression, URL, email, phone, bank card, mention, hashtag, cashtag, bot command, anchor/link и reference/link. Перед применением конкретного конструктора сверь его сигнатуру с документацией закреплённой версии и добавь serialization test: это та часть API, которая различается между 3.29.1 и 3.30.0 сильнее всего.

### 2. Потоковый rich draft

Вынеси streaming в сервис, не размазывай цикл по handler. Инварианты:

- `send_rich_message_draft` работает только с числовым `chat_id` обычного private chat;
- `draft_id` должен быть ненулевым;
- все кадры одного ответа используют один `draft_id`, иначе появятся разные drafts;
- draft — временный preview примерно на 30 секунд;
- после кадров **обязательно** вызови `send_rich_message` с полным результатом;
- `<tg-thinking>` допустим только в draft и не должен попадать в постоянный результат;
- прямую загрузку новых файлов в draft не используй;
- отмена задачи, timeout и Telegram API error должны корректно завершать пользовательский flow и логироваться без утечки секретов.

Эталонный сервис:

```python
import asyncio
import secrets
from collections.abc import Sequence

from aiogram import Bot
from aiogram.types import InputRichMessage, Message


async def stream_rich_message(
    bot: Bot,
    *,
    chat_id: int,
    frames: Sequence[InputRichMessage],
    result: InputRichMessage,
    delay_seconds: float,
    message_thread_id: int | None = None,
) -> Message:
    if not frames:
        raise ValueError("at least one draft frame is required")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must not be negative")

    draft_id = secrets.randbelow(2**31 - 1) + 1
    for index, frame in enumerate(frames):
        await bot.send_rich_message_draft(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            draft_id=draft_id,
            rich_message=frame,
        )
        if index < len(frames) - 1 and delay_seconds:
            await asyncio.sleep(delay_seconds)

    return await bot.send_rich_message(
        chat_id=chat_id,
        message_thread_id=message_thread_id,
        rich_message=result,
    )
```

В handler сначала проверяй `message.chat.type == ChatType.PRIVATE` через сравнение значений, которое также корректно работает, когда тип после десериализации представлен строкой. Не требуй topics: они не нужны для обычного личного диалога.

### 3. Редактирование rich-сообщения

Используй существующий `editMessageText`, передавая `rich_message` вместо `text`:

```python
await bot.edit_message_text(
    chat_id=message.chat.id,
    message_id=message.message_id,
    rich_message=InputRichMessage(html="<h2>Новая ревизия</h2>"),
    reply_markup=keyboard,
)
```

Не передавай одновременно `text` и `rich_message`. Проверь, что при переключении состояния сохраняется тот же `message_id`. При редактировании inline message нельзя напрямую загрузить новый файл.

### 4. Входящий typed AST

Добавь обработку поля `Message.rich_message` в подходящий router. Располагай специализированный handler раньше catch-all handler:

```python
import json
from aiogram import F, Router
from aiogram.types import Message

router = Router()


@router.message(F.rich_message)
async def handle_rich_message(message: Message) -> None:
    if message.rich_message is None:
        return
    payload = message.rich_message.model_dump(mode="json", exclude_none=True)
    # Используй payload в бизнес-логике. Не отправляй большой JSON пользователю в production.
```

`RichMessage.blocks` — типизированное дерево ответа Telegram. Не переиспользуй response-модели `RichBlock*` для формирования исходящего payload в aiogram 3.29.1. Если нужен debug preview, ограничь его безопасной длиной меньше лимита обычного сообщения и не включай чувствительные данные.

### 5. Rich content в inline query

Если inline mode уже используется или нужен продукту, верни `InputRichMessageContent`:

```python
from aiogram.types import InlineQueryResultArticle, InputRichMessage, InputRichMessageContent

result = InlineQueryResultArticle(
    id="stable-rich-result-id",
    title="Rich result",
    input_message_content=InputRichMessageContent(
        rich_message=InputRichMessage(markdown="# Результат")
    ),
)
await query.answer([result], cache_time=1, is_personal=True)
```

Inline mode предварительно включается через `/setinline` у `@BotFather`. Выбирай стабильный уникальный `id`, разумный cache policy и не возвращай персональные данные в неперсональном кэше.

### 6. Ссылка внутри варианта опроса

```python
from aiogram.types import InputMediaLink, InputPollOption

option = InputPollOption(
    text="Открыть документацию",
    text_parse_mode=None,
    media=InputMediaLink(url="https://core.telegram.org/bots/api"),
)
```

URL должен быть HTTP/HTTPS. Сохрани все существующие правила опроса и права чата. Если функция не нужна продукту, добавь изолированный пример/тест только когда пользователь действительно просил перенести весь showcase; не засоряй основной UX.

### 7. Join-request queries

Новый flow применяется только когда у `ChatJoinRequest` присутствует `query_id` и бот назначен guard bot. Ответить нужно в течение 10 секунд: показать Web App или вызвать `answerChatJoinRequestQuery`.

```python
@router.chat_join_request()
async def handle_join_request(request: ChatJoinRequest, settings: Settings) -> None:
    if request.query_id is None:
        # Это обычный join request; не меняй прежнюю политику обработки.
        return

    if settings.join_request_mode == "webapp":
        await request.send_webapp(web_app_url=settings.join_request_web_app_url)
        return

    await request.answer_query(result=settings.join_request_mode)
```

Допустимые результаты: `approve`, `decline`, `queue`. Безопасное значение по умолчанию — `queue`, чтобы решение осталось администраторам. Web App URL обязан использовать HTTPS. `send_webapp()` не завершает решение: backend должен проверить подписанные Telegram Web App init data и затем вызвать `answerChatJoinRequestQuery`. Не имитируй успешную проверку init data и не включай auto-approve без явного требования владельца проекта.

Убедись, что bot/user capability `supports_join_request_queries`, `ChatFullInfo.guard_bot`, admin setup и получение update этого типа соответствуют окружению. Для классического запроса без `query_id` сохрани прежнее поведение.

## Конфигурация

Интегрируй настройки в существующую config-систему. Если аналога нет, добавь типизированные значения:

| Переменная | Default | Проверка |
|---|---:|---|
| `STREAM_DELAY_MS` | `350` | целое число `0..5000` |
| `JOIN_REQUEST_MODE` | `queue` | `queue`, `approve`, `decline`, `webapp` |
| `JOIN_REQUEST_WEB_APP_URL` | пусто | обязательный HTTPS URL для `webapp` |

Не дублируй `BOT_TOKEN`, logging и webhook/polling flags, если они уже существуют. Не коммить реальный токен. Не добавляй dotenv-зависимость, если проект получает secrets другим способом.

## Порядок реализации

1. Исследуй проект и зафиксируй выбранную версию/стратегию.
2. Обнови dependency manifest и lock-файл, не ломая поддерживаемый Python runtime.
3. Добавь чистые builders Rich HTML/Markdown и unit tests для них.
4. Интегрируй `send_rich_message` и rich edit в существующие product handlers.
5. Добавь streaming service и private-chat guard.
6. Добавь входящий `F.rich_message`, проверив порядок router/handler.
7. Добавь inline, poll-link и join-request функции только в согласованном продуктовом месте; если переносится весь showcase — перенеси все три.
8. Обнови команды/меню/README/env example/deployment config только там, где это требуется фактической реализацией.
9. Добавь тесты сериализации новых aiogram types и methods.
10. Запусти formatter, linter, type checker, unit/integration tests и build, предусмотренные репозиторием.

## Обязательные тесты

Используй тестовый стек проекта и моки — unit tests не должны обращаться к реальному Telegram API.

Проверь как минимум:

- закреплена разрешённая версия aiogram, а `3.29.0` отсутствует;
- builder экранирует `<`, `>`, `&` и кавычки в динамическом HTML;
- каждый `InputRichMessage` использует только один источник контента;
- `SendRichMessage.__api_method__ == "sendRichMessage"`;
- `SendRichMessageDraft.__api_method__ == "sendRichMessageDraft"`;
- rich edit сериализуется без `text`;
- все draft frames используют один ненулевой `draft_id`;
- после последнего draft вызывается постоянный `send_rich_message`;
- `<tg-thinking>` присутствует только во временных frames;
- streaming отклоняется вне private chat и допускает raw-значение `"private"` после update parsing;
- пустой список frames и отрицательная задержка отклоняются;
- `F.rich_message` сериализует typed AST и не падает на `None`;
- inline result содержит `InputRichMessageContent`;
- `InputPollOption.media` сериализуется как `{"type": "link", "url": "https://..."}`;
- join request без `query_id` не затрагивается;
- `approve`, `decline`, `queue` вызывают query answer, а `webapp` требует HTTPS URL;
- существующие тесты старого бота по-прежнему проходят.

Пример protocol-level smoke test для aiogram:

```python
from aiogram.methods import EditMessageText, SendRichMessage, SendRichMessageDraft
from aiogram.types import InputRichMessage

rich = InputRichMessage(html="<h1>Demo</h1>")
assert SendRichMessage(chat_id=42, rich_message=rich).__api_method__ == "sendRichMessage"
assert SendRichMessageDraft(
    chat_id=42, draft_id=7, rich_message=rich
).__api_method__ == "sendRichMessageDraft"

edit = EditMessageText(chat_id=42, message_id=9, rich_message=rich)
assert edit.text is None
```

## Ручная приёмка

Если доступен тестовый bot token, не используй production token и не удаляй накопленные updates без явной причины. Проверь:

1. rich-документ отображает заголовок, таблицу, details, ссылку и формулу;
2. Rich Markdown не выглядит как сырой MarkdownV2;
3. в личном чате кадры одного draft плавно заменяют друг друга, затем появляется постоянное сообщение;
4. в группе streaming корректно отклонён;
5. rich edit сохраняет `message_id`;
6. пересланное rich message попадает в typed handler (доставка может зависеть от настроек Telegram);
7. inline result появляется после включения inline mode;
8. вариант опроса показывает HTTP link на поддерживаемом клиенте;
9. query-enabled join request обрабатывается выбранной безопасной политикой.

Учитывай, что старый Telegram-клиент может не отрисовать новый UI, даже когда payload и серверный вызов корректны. Отделяй ошибку клиента от ошибки Bot API с помощью protocol tests и логов.

## Критерии готовности

Работа завершена, когда:

- выбранная версия и причина выбора явно описаны;
- dependency/lock/deployment согласованы между собой;
- новые функции встроены в архитектуру старого бота без регрессий;
- динамический HTML экранируется, URL и Web App настройки валидируются;
- streaming всегда пытается сохранить финальный ответ и не создаёт несколько draft из-за смены id;
- join-request flow не включает небезопасный auto-approve по умолчанию;
- все релевантные автоматические проверки проходят;
- README содержит команды запуска, переменные окружения, ограничения клиентов и короткий smoke-test сценарий;
- нет токенов, временных файлов, debug dumps и случайных изменений.

## Формат итогового отчёта

В конце сообщи владельцу:

1. какую версию Python, Telegram Bot API и фреймворка выбрал и почему;
2. какие файлы и функции изменил;
3. какие возможности реально интегрированы, а какие сознательно не добавлены и почему;
4. результаты formatter/linter/type checker/tests/build;
5. что требует внешней настройки в `@BotFather`, правах чата, guard bot, Web App или Telegram client;
6. оставшиеся риски и конкретный ручной сценарий проверки.

Не объявляй работу готовой, если ты только написал план, не обновил lock-файл, не запускал доступные проверки или скрыл их ошибки.
