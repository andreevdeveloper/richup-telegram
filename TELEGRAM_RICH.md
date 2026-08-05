# Telegram Rich Messages в Bot API 10.1 и 10.2

Технический справочник по новым возможностям сообщений Telegram и их реализации в `aiogram`. Документ описывает Rich HTML, Rich Markdown, потоковые черновики, редактирование rich-контента, входящий typed AST, rich inline results, ссылки в вариантах опроса и join-request queries. В примерах учтены различия между Bot API 10.1/10.2 и `aiogram` 3.29.1/3.30.0.

Reference-реализация находится в проекте `richup-telegram`. Её основные модули:

| Область | Файл reference-проекта |
|---|---|
| Rich HTML/Markdown builders | `src/richup_bot/content.py` |
| Отправка, streaming, edit, poll, AST | `src/richup_bot/routers/rich.py` |
| Inline result | `src/richup_bot/routers/inline.py` |
| Join-request queries | `src/richup_bot/routers/join_requests.py` |
| Streaming lifecycle | `src/richup_bot/services/streaming.py` |
| Protocol tests | `tests/test_protocol_models.py`, `tests/test_streaming.py` |

## Версии и границы совместимости

Состояние экосистемы на **5 августа 2026 года**:

- Telegram Bot API 10.1 от 11 июня 2026 года добавил Rich Messages, rich drafts, rich inline content, join-request queries и link media для вариантов опроса.
- Reference-проект проверен на `aiogram==3.29.1` и Python 3.12–3.14.
- `aiogram 3.29.0` использовать нельзя: релиз отозван из PyPI из-за резкого замедления при разборе вложенных `RichBlock`.
- Telegram Bot API 10.2 и `aiogram==3.30.0` уже выпущены. В 10.2 у `InputRichMessage` появились исходящие `blocks` и `media`, а также семейство `InputRichBlock*`.

### Варианты совместимости

| Сценарий | Версия | Доступный исходящий формат |
|---|---|---|
| Точное воспроизведение reference-проекта | `aiogram==3.29.1`, Bot API 10.1 | ровно одно из `html` или `markdown` |
| Актуальная ветка aiogram | `aiogram==3.30.0`, Bot API 10.2 | ровно одно из `html`, `markdown` или `blocks`; дополнительно доступно `media` |
| Старый проект на aiogram 2.x | требуется major migration на 3.x | Executor заменён на `Dispatcher.start_polling`; отличаются filters, middleware и lifecycle |
| Другой Telegram framework | зависит от поддержки Bot API 10.1+ | используются эквивалентные типы/методы фреймворка или изолированные raw Bot API calls |

Точная фиксация версии безопаснее диапазона вроде `aiogram>=3.29`, поскольку между 3.29 и 3.30 изменился протокол исходящих моделей Rich Messages. Dependency manifest, lock-файл и runtime image должны указывать совместимые версии.

## Источники истины

При расхождении данных действует следующий приоритет:

1. официальная текущая спецификация Telegram Bot API;
2. документация выбранной закреплённой версии aiogram;
3. сериализация реально установленных моделей и методов;
4. reference-реализация;
5. этот справочник.

Официальные ссылки:

- Telegram Bot API changelog: <https://core.telegram.org/bots/api-changelog#june-11-2026>
- Rich Message formatting и лимиты: <https://core.telegram.org/bots/api#rich-message-formatting-options>
- Telegram Bot API: <https://core.telegram.org/bots/api>
- aiogram 3.29.1: <https://docs.aiogram.dev/en/v3.29.1/>
- актуальная документация aiogram 3.30.0: <https://docs.aiogram.dev/en/latest/>
- история релизов aiogram: <https://pypi.org/project/aiogram/>

Актуальные сведения о версиях следует проверять по официальным страницам. Сторонние статьи не являются источником сигнатур или ограничений API.

## Особенности интеграции в существующий проект

На перенос влияют версия Python и Pydantic, Telegram framework, dependency lock, lifecycle `Bot`/`Dispatcher`, router order, webhook/polling, default `parse_mode`, собственные send/edit wrappers, middleware и обработка Telegram API errors.

Специализированный `F.rich_message` handler располагается раньше catch-all handlers. Для `chat_join_request` и `inline_query` соответствующие update types должны присутствовать в `allowed_updates`. Self-hosted Telegram Bot API server также должен поддерживать нужную версию протокола.

Rich content удобно отделять от Telegram I/O в чистые builder-функции. Streaming относится к service layer, а не к отдельным циклам внутри handlers. При переносе в старый проект обычно сохраняются его существующие router, config, localization, storage, FSM, middleware и deployment boundaries.

## Возможности API и примеры

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

Rich Markdown близок к GitHub Flavored Markdown и **не является MarkdownV2**. Rich HTML не использует старый `parse_mode`, а Rich Markdown не должен обрабатываться существующим MarkdownV2 escaper.

В одном `InputRichMessage` указывается ровно один формат:

- в aiogram 3.29.1: `html` **или** `markdown`;
- в aiogram 3.30.0: `html`, `markdown` **или** `blocks`.

Сложный контент обычно строится в чистых builder-функциях. Любые динамические значения пользователя в HTML проходят через `html.escape`, включая имя, title, введённый текст и подписи. URL отдельно валидируются по допустимой схеме.

Типичный showcase содержит заголовок, параграф, inline formatting, список, таблицу, `details`, цитату, ссылку и формулу. В product-интерфейсе эти элементы могут использоваться независимо без отдельного демо-меню.

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

Этот синтаксис отличается от HTML для обычного `sendMessage` и передаётся только в `InputRichMessage(html=...)`. Telegram принимает только документированные теги.

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

Полный набор исходящих block types 10.2 и их HTML-эквиваленты:

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

Для inline-форматирования внутри explicit blocks используются `RichText*` response/input-compatible модели: bold, italic, underline, strikethrough, spoiler, date-time, text mention, subscript, superscript, marked, code, custom emoji, mathematical expression, URL, email, phone, bank card, mention, hashtag, cashtag, bot command, anchor/link и reference/link. Сигнатура конкретного конструктора зависит от закреплённой версии и проверяется по её документации и serialization test; именно эта часть API заметнее всего различается между 3.29.1 и 3.30.0.

### 2. Потоковый rich draft

Streaming обычно оформляется отдельным сервисом. Его инварианты:

- `send_rich_message_draft` работает только с числовым `chat_id` обычного private chat;
- `draft_id` должен быть ненулевым;
- все кадры одного ответа используют один `draft_id`, иначе появятся разные drafts;
- draft — временный preview примерно на 30 секунд;
- после кадров **обязательно** вызови `send_rich_message` с полным результатом;
- `<tg-thinking>` допустим только в draft и не должен попадать в постоянный результат;
- прямая загрузка новых файлов в draft не поддерживается;
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

Handler проверяет `message.chat.type == ChatType.PRIVATE` через сравнение значений, которое также корректно работает, когда тип после десериализации представлен строкой. Topics для обычного личного диалога не требуются.

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

`text` и `rich_message` не передаются одновременно. При переключении состояния сохраняется тот же `message_id`. При редактировании inline message нельзя напрямую загрузить новый файл.

### 4. Входящий typed AST

Поле `Message.rich_message` обрабатывается специализированным handler, расположенным раньше catch-all handler:

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
    # payload доступен для бизнес-логики; большой JSON не предназначен для production-ответа.
```

`RichMessage.blocks` — типизированное дерево ответа Telegram. Response-модели `RichBlock*` не используются для формирования исходящего payload в aiogram 3.29.1. Debug preview ограничивается безопасной длиной меньше лимита обычного сообщения и не содержит чувствительные данные.

### 5. Rich content в inline query

Rich content возвращается из inline query через `InputRichMessageContent`:

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

Inline mode предварительно включается через `/setinline` у `@BotFather`. Result использует стабильный уникальный `id` и подходящий cache policy; персональные данные не помещаются в неперсональный кэш.

### 6. Ссылка внутри варианта опроса

```python
from aiogram.types import InputMediaLink, InputPollOption

option = InputPollOption(
    text="Открыть документацию",
    text_parse_mode=None,
    media=InputMediaLink(url="https://core.telegram.org/bots/api"),
)
```

URL должен быть HTTP/HTTPS. Все обычные правила опроса и права чата продолжают действовать. Функция может использоваться независимо от остальных возможностей Rich Messages.

### 7. Join-request queries

Новый flow применяется только когда у `ChatJoinRequest` присутствует `query_id` и бот назначен guard bot. Ответить нужно в течение 10 секунд: показать Web App или вызвать `answerChatJoinRequestQuery`.

```python
@router.chat_join_request()
async def handle_join_request(request: ChatJoinRequest, settings: Settings) -> None:
    if request.query_id is None:
        # Это обычный join request; прежняя политика обработки сохраняется.
        return

    if settings.join_request_mode == "webapp":
        await request.send_webapp(web_app_url=settings.join_request_web_app_url)
        return

    await request.answer_query(result=settings.join_request_mode)
```

Допустимые результаты: `approve`, `decline`, `queue`. Безопасное значение по умолчанию — `queue`, при котором решение остаётся администраторам. Web App URL обязан использовать HTTPS. `send_webapp()` не завершает решение: backend проверяет подписанные Telegram Web App init data, а затем вызывает `answerChatJoinRequestQuery`. Auto-approve без проверки пользовательских данных небезопасен.

Flow зависит от bot/user capability `supports_join_request_queries`, поля `ChatFullInfo.guard_bot`, admin setup и получения соответствующего update. Классический запрос без `query_id` сохраняет прежнее поведение.

## Конфигурация

Для новых функций используются следующие типизированные настройки:

| Переменная | Default | Проверка |
|---|---:|---|
| `STREAM_DELAY_MS` | `350` | целое число `0..5000` |
| `JOIN_REQUEST_MODE` | `queue` | `queue`, `approve`, `decline`, `webapp` |
| `JOIN_REQUEST_WEB_APP_URL` | пусто | обязательный HTTPS URL для `webapp` |

`BOT_TOKEN`, logging и webhook/polling flags остаются частью общей конфигурации приложения. Реальный токен не хранится в репозитории. Способ загрузки secrets определяется окружением и не требует обязательного использования dotenv.

## Проверки совместимости

Unit tests используют моки и не обращаются к реальному Telegram API. Полезный набор проверяемых свойств:

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
- существующая функциональность бота не получает регрессий.

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

## Ручная проверка

Для ручной проверки подходит отдельный тестовый bot token. Production token и накопленные production updates для этого не требуются. Сценарий:

1. rich-документ отображает заголовок, таблицу, details, ссылку и формулу;
2. Rich Markdown не выглядит как сырой MarkdownV2;
3. в личном чате кадры одного draft плавно заменяют друг друга, затем появляется постоянное сообщение;
4. в группе streaming корректно отклонён;
5. rich edit сохраняет `message_id`;
6. пересланное rich message попадает в typed handler (доставка может зависеть от настроек Telegram);
7. inline result появляется после включения inline mode;
8. вариант опроса показывает HTTP link на поддерживаемом клиенте;
9. query-enabled join request обрабатывается выбранной безопасной политикой.

Старый Telegram-клиент может не отрисовать новый UI, даже когда payload и серверный вызов корректны. Protocol tests и логи позволяют отличить ограничение клиента от ошибки Bot API.
