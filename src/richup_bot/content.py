"""Русскоязычные rich-документы для демонстрационных сценариев."""

from __future__ import annotations

from html import escape

from aiogram.types import InputRichMessage

AIROGRAM_DOCS_URL = "https://docs.aiogram.dev/en/v3.29.1/"
BOT_API_DOCS_URL = "https://core.telegram.org/bots/api#rich-messages"


def build_menu_document(*, first_name: str) -> InputRichMessage:
    """Собрать главный экран Rich Messages Demo."""
    safe_name = escape(first_name)
    return _html(
        f"""
<h1>Rich Messages Demo</h1>
<p>Добро пожаловать, <b>{safe_name}</b>! Это демонстрация Rich Messages —
новой возможности <code>aiogram 3.29.1</code> и Bot API 10.1.</p>
<p>Выберите раздел с помощью кнопок ниже, чтобы увидеть примеры.</p>
<hr/>
<p><i>Каждый раздел открывается в этом же сообщении через
<code>editMessageText</code> с параметром <code>rich_message</code>.</i></p>
"""
    )


def build_formatting_showcase() -> InputRichMessage:
    """Показать все основные inline-форматы Rich HTML."""
    return _html(
        """
<h2>Форматирование текста</h2>
<p><b>Жирный текст</b> — тег <code>&lt;b&gt;</code><br/>
<i>Курсивный текст</i> — тег <code>&lt;i&gt;</code><br/>
<u>Подчёркнутый текст</u> — тег <code>&lt;u&gt;</code><br/>
<s>Зачёркнутый текст</s> — тег <code>&lt;s&gt;</code><br/>
<tg-spoiler>Скрытый под спойлером текст</tg-spoiler> — тег
<code>&lt;tg-spoiler&gt;</code><br/>
<code>Моноширинный код</code> — тег <code>&lt;code&gt;</code><br/>
<mark>Выделенный текст</mark> — тег <code>&lt;mark&gt;</code><br/>
H<sub>2</sub>O и x<sup>2</sup> — теги <code>&lt;sub&gt;</code> и
<code>&lt;sup&gt;</code><br/>
<tg-math>x = (-b +/- sqrt(b^2 - 4ac)) / 2a</tg-math> — математическое выражение.</p>
"""
    )


def build_links_showcase(*, user_id: int) -> InputRichMessage:
    """Показать ссылки, упоминания и автоматическое распознавание сущностей."""
    return _html(
        f"""
<h2>Ссылки и сущности</h2>
<p>Ссылка: <a href="https://aiogram.dev">aiogram.dev</a><br/>
Email: <a href="mailto:info@aiogram.dev">info@aiogram.dev</a><br/>
Телефон: <a href="tel:+79001234567">+79001234567</a><br/>
Упоминание пользователя: <a href="tg://user?id={user_id}">текущий пользователь</a><br/>
Хэштег: #aiogram<br/>
Кэштег: $TON<br/>
Команда: /start</p>
<p><i>Автоматическое распознавание отключается через
<code>skip_entity_detection=True</code> в <code>InputRichMessage</code>.</i></p>
"""
    )


def build_structure_showcase() -> InputRichMessage:
    """Показать структурные блоки rich-документа."""
    return _html(
        """
<h1>Заголовок H1 — самый крупный</h1>
<h2>Заголовок H2</h2>
<h3>Заголовок H3</h3>
<h4>Заголовок H4</h4>
<h5>Заголовок H5</h5>
<h6>Заголовок H6 — самый мелкий</h6>
<hr/>
<blockquote><b>Блочная цитата.</b> Применяется для выделения важного фрагмента
текста или цитаты из другого источника.<cite>RichBlockBlockQuotation</cite></blockquote>
<aside>Выносная цитата привлекает внимание к ключевой мысли документа.
<cite>RichBlockPullQuotation</cite></aside>
<footer>Подвал документа — дополнительная информация внизу.</footer>
"""
    )


def build_lists_showcase() -> InputRichMessage:
    """Показать маркированные, нумерованные и task-списки."""
    return _html(
        """
<h2>Списки</h2>
<h3>Маркированный список</h3>
<ul>
  <li>Rich Messages — форматированные документы</li>
  <li>Заголовки H1–H6, разделители и цитаты</li>
  <li>Медиа-блоки прямо внутри сообщения</li>
</ul>
<h3>Нумерованный список</h3>
<ol>
  <li>Установить <code>aiogram 3.29.1</code></li>
  <li>Создать <code>InputRichMessage</code> с HTML или Markdown</li>
  <li>Вызвать <code>send_rich_message()</code></li>
  <li>Радоваться результату</li>
</ol>
<h3>Список задач</h3>
<ul>
  <li><input type="checkbox" checked> Проверить rich-меню</li>
  <li><input type="checkbox" checked> Запустить streaming draft</li>
  <li><input type="checkbox"> Подключить реальную LLM</li>
</ul>
"""
    )


def build_table_showcase() -> InputRichMessage:
    """Показать сравнительную rich-таблицу."""
    return _html(
        """
<h2>Таблица возможностей</h2>
<table bordered striped>
  <tr><th>Возможность</th><th>До 3.29</th><th>aiogram 3.29+</th></tr>
  <tr><td>Жирный, курсив, код</td><td>Да</td><td>Да</td></tr>
  <tr><td>Заголовки H1–H6</td><td>Нет</td><td><mark>Да</mark></td></tr>
  <tr><td>Списки ul / ol</td><td>Нет</td><td><mark>Да</mark></td></tr>
  <tr><td>Таблицы</td><td>Нет</td><td><mark>Да</mark></td></tr>
  <tr><td>Details / Summary</td><td>Нет</td><td><mark>Да</mark></td></tr>
  <tr><td>Streaming Draft</td><td>Нет</td><td><mark>Да</mark></td></tr>
</table>
<footer>До 20 столбцов; table cells поддерживают inline-форматирование.</footer>
"""
    )


def build_details_showcase() -> InputRichMessage:
    """Показать раскрывающиеся блоки details/summary."""
    return _html(
        """
<h2>Раскрываемые блоки — Details</h2>
<p>Нажмите на заголовок блока, чтобы раскрыть содержимое:</p>
<details><summary>Что такое aiogram?</summary>
<p><b>aiogram</b> — асинхронный Python-фреймворк для создания Telegram-ботов,
построенный на asyncio и поддерживающий весь Bot API.</p></details>
<details><summary>Что нового в aiogram 3.29?</summary>
<p>Поддержка Rich Messages: документы с заголовками, списками, таблицами,
цитатами, формулами и streaming drafts.</p></details>
<details open><summary>Этот блок открыт по умолчанию</summary>
<p>В Rich HTML используется атрибут <code>open</code> у тега
<code>&lt;details&gt;</code>.</p></details>
"""
    )


def build_stream_info() -> InputRichMessage:
    """Объяснить настоящий draft streaming и его ограничения."""
    return _html(
        """
<h2>Streaming Draft</h2>
<p>Метод <code>sendRichMessageDraft</code> обновляет частичное rich-сообщение
в реальном времени, пока генерируется ответ.</p>
<ul>
  <li>Подходит для AI-ботов: пользователь видит ответ по мере генерации</li>
  <li>Черновик живёт около 30 секунд и не сохраняется сам</li>
  <li><code>&lt;tg-thinking&gt;</code> показывает состояние «размышления»</li>
  <li>Финальный <code>sendRichMessage</code> сохраняет готовый ответ</li>
</ul>
<blockquote><b>Работает в обычном личном чате с ботом.</b> Topics и
<code>message_thread_id</code> не требуются. Группы Bot API не поддерживает.</blockquote>
<p>Нажмите кнопку ниже для демонстрации.</p>
"""
    )


def build_markdown_showcase() -> InputRichMessage:
    """Собрать русскоязычный Rich Markdown документ."""
    return InputRichMessage(
        markdown=f"""
# Rich Markdown

Один payload объединяет **жирный**, _курсив_, ~~зачёркнутый~~, ==выделенный==,
||скрытый|| текст, `inline code` и формулу $E = mc^2$.

## Инженерный чек-лист

- [x] `InputRichMessage(markdown=...)`
- [x] GFM-таблица
- [x] footnotes и формулы
- [ ] источник токенов от реальной LLM

| Возможность | Bot API | aiogram |
|:--|:--:|--:|
| Rich document | 10.1 | 3.29.1 |
| Animated draft | 10.1 | 3.29.1 |

> Draft — временный preview. Финальный `sendRichMessage` сохраняет результат.

Сноски поддерживаются нативно[^source].

[^source]: [Официальная документация Bot API]({BOT_API_DOCS_URL}).

$$ throughput = useful\\_signal / interaction\\_cost $$

---

[Документация aiogram]({AIROGRAM_DOCS_URL})
""".strip()
    )


def build_draft_frames() -> tuple[InputRichMessage, ...]:
    """Вернуть кадры, имитирующие постепенную генерацию ответа."""
    frames = (
        """
<h2>Генерирую ответ</h2>
<tg-thinking>Анализирую запрос...</tg-thinking>
""",
        """
<h2>Генерирую ответ</h2>
<p>Rich draft использует один ненулевой <code>draft_id</code>.</p>
<tg-thinking>Собираю структуру документа...</tg-thinking>
""",
        """
<h2>Генерирую ответ</h2>
<ul><li>Обычный личный чат</li><li>Плавное обновление одного draft</li>
<li>Финальное сообщение сохраняется отдельно</li></ul>
<tg-thinking>Финализирую...</tg-thinking>
""",
    )
    return tuple(_html(frame) for frame in frames)


def build_stream_result() -> InputRichMessage:
    """Собрать постоянный результат после эфемерных draft-кадров."""
    return _html(
        """
<h1>Ответ готов</h1>
<p>Потоковый draft был временным. Этот документ сохранён отдельным вызовом
<code>sendRichMessage</code>.</p>
<blockquote>Для одного генерируемого ответа используется стабильный ненулевой
<code>draft_id</code>.</blockquote>
"""
    )


def build_edit_revision(revision: int) -> InputRichMessage:
    """Собрать одну из двух ревизий демонстрации editMessageText."""
    if revision == 1:
        body = """
<h2>Редактируемое rich-сообщение</h2>
<p>Ревизия <mark>1</mark>. Кнопка вызывает
<code>editMessageText(rich_message=...)</code>.</p>
<ul><li>Тот же <code>message_id</code></li><li>Без нового сообщения</li></ul>
"""
    elif revision == 2:
        body = """
<h2>Rich-сообщение обновлено</h2>
<p>Ревизия <mark>2</mark>. Структурные блоки заменены атомарно.</p>
<details open><summary>Что произошло?</summary>
<p>Rich-контент и inline-клавиатура изменились одним API-вызовом.</p></details>
"""
    else:
        raise ValueError("revision must be 1 or 2")
    return _html(body)


def build_inline_result() -> InputRichMessage:
    """Собрать rich-контент результата inline query."""
    return _html(
        """
<h2>Inline Rich Message</h2>
<p>Сообщение доставлено через <code>InputRichMessageContent</code>.</p>
<table bordered><tr><th>API</th><th>Состояние</th></tr>
<tr><td>Bot API 10.1</td><td><mark>Работает</mark></td></tr></table>
"""
    )


def _html(document: str) -> InputRichMessage:
    return InputRichMessage(html=document.strip())
