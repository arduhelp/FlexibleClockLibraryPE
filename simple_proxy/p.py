from flask import Flask, Response
import requests
from bs4 import BeautifulSoup, NavigableString
import sys

app = Flask(__name__)

# --- Тестова сторінка з вашого запиту ---
TEST_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>HTML Test Page</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Тестова сторінка з усіма HTML елементами">
    <meta name="author" content="Test">
    <base href="./">
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }
        section { background: #fff; padding: 15px; margin-bottom: 20px; border-radius: 8px; }
        hr { margin: 20px 0; }
        table, th, td { border: 1px solid #333; border-collapse: collapse; padding: 5px; }
        details { cursor: pointer; }
    </style>
    <script>
        function hello() { alert("Hello HTML!"); }
    </script>
</head>
<body>
<header>
    <h1>HTML Test Page</h1>
    <nav>
        <a href="#">Home</a> |
        <a href="#">About</a> |
        <a href="#">Contact</a>
    </nav>
</header>
<main>
<section>
    <h2>Tekst</h2>
    <p>Це <b>bold</b>, <strong>strong</strong>, <i>italic</i>, <em>em</em>,
       <mark>mark</mark>, <small>small</small>,
       <del>deleted</del>, <ins>inserted</ins>,
       H<sub>2</sub>O, x<sup>2</sup></p>
    <blockquote>Це blockquote</blockquote>
    <q>quote</q>
    <pre>function test() { return true; }</pre>
    <code>console.log("code");</code>
    <abbr title="HyperText Markup Language">HTML</abbr>
    <address>Ukraine</address>
    <cite>--Cytata</cite>
</section>
<section>
    <h2>--Spysok</h2>
    <ul><li>UL item</li><li>UL item</li></ul>
    <ol><li>OL item</li><li>OL item</li></ol>
    <dl><dt>HTML</dt><dd>Mova Rozmitky</dd></dl>
</section>
<section>
    <h2>Posylannia ta knopky</h2>
    <a href="http://example.com" target="_blank">Link</a><br><br>
    <button onclick="hello()">Button</button>
</section>
<section>
    <h2>--Formy</h2>
    <form>
        <label>Text: <input type="text"></label><br>
        <label>Password: <input type="password"></label><br>
        <label>Email: <input type="email"></label><br>
        <label>Number: <input type="number"></label><br>
        <label>Date: <input type="date"></label><br>
        <label>Color: <input type="color"></label><br>
        <label>Range: <input type="range"></label><br>
        <input type="checkbox"> Checkbox<br>
        <input type="radio" name="r"> Radio<br>
        <select><option>Option 1</option><option>Option 2</option></select><br>
        <textarea rows="3" cols="30"></textarea><br>
        <input type="submit"><input type="reset">
    </form>
</section>
<section>
    <h2>--Tablycia</h2>
    <table>
        <caption>Test Table</caption>
        <thead><tr><th>A</th><th>B</th></tr></thead>
        <tbody><tr><td>1</td><td>2</td></tr></tbody>
        <tfoot><tr><td colspan="2">Footer</td></tr></tfoot>
    </table>
</section>
<section>
    <h2>Media</h2>
    <img src="https://via.placeholder.com/150" alt="img"><br><br>
    <audio controls><source src="" type="audio/mpeg"></audio><br><br>
    <video controls width="200"><source src="" type="video/mp4"></video>
</section>
<section>
    <h2>Interactyv</h2>
    <details><summary>Details / Summary</summary>Hidden text</details>
    <dialog open>Dialog</dialog>
    <progress value="50" max="100"></progress><br>
    <meter value="0.7"></meter>
</section>
<section>
    <h2>Vbydovane</h2>
    <iframe src="http://example.com" width="300" height="150"></iframe>
    <embed src="" type=""></object>
</section>
<section>
    <h2>Semantyka</h2>
    <article>Article</article>
    <aside>Aside</aside>
    <figure>
        <img src="https://upload.wikimedia.org/wikipedia/commons/6/63/Icon_Bird_512x512.png">
        <figcaption>Figcaption</figcaption>
    </figure>
    <time datetime="2026-01-01">2026</time>
</section>
</main>
<footer><hr><p>Footer © 2026</p></footer>
</body>
</html>
"""

# --- Логіка очищення та спрощення ---
def simplify_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Видаляємо стилі та скрипти
    for tag in soup(['script', 'style', 'link']):
        # Видаляємо <link>, якщо це CSS
        if tag.name == 'link' and 'stylesheet' not in tag.get('rel', []):
            continue
        tag.decompose()

    # 2. Логіка лічильника посилань
    # Ми проходимо по всіх тегах у порядку їх появи в HTML
    link_counter = 0
    
    # Список тегів, які "розривають" ланцюжок посилань (контентні теги)
    reset_tags = ['p', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                  'img', 'table', 'form', 'section', 'article']

    for tag in soup.find_all(True):
        if tag.name == 'a':
            link_counter += 1
            if link_counter > 3:
                # Видаляємо атрибут href, перетворюючи посилання на текст
                del tag['href']
                # Можна додати стиль або позначку, що це було посилання (опціонально)
                # tag['style'] = "text-decoration: line-through; color: gray;" 
        
        elif tag.name in reset_tags:
            # Якщо зустріли контентний елемент - скидаємо лічильник
            link_counter = 0
        
        # Примітка: div, span, li, ul, ol не скидають лічильник, 
        # бо вони часто є частиною меню навігації.

    return str(soup)

# --- Маршрути ---

@app.route('/f/')
def home():
    return TEST_HTML

@app.route('/f/<path:target_url>')
def proxy(target_url):
    # Додаємо протокол, якщо його немає
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url

    try:
        # Імітуємо звичайний браузер, щоб сайти не блокували запит
        headers = {'User-Agent': 'Mozilla/5.0 (SimpleProxy)'}
        response = requests.get(target_url, headers=headers, timeout=10)
        
        # Обробляємо кодування
        response.encoding = response.apparent_encoding

        # Спрощуємо HTML
        simplified_content = simplify_html(response.text)

        return Response(simplified_content, mimetype='text/html')

    except Exception as e:
        return f"<h1>Error fetching page</h1><p>{str(e)}</p>", 500

if __name__ == '__main__':
    # Запуск сервера на всіх інтерфейсах, порт 80 (потрібен sudo для порту 80)
    # або змініть на 5000
    app.run(host='0.0.0.0', port=8080)
