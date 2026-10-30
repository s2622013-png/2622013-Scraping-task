import time
import requests
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag

url = 'https://www.musashino-u.ac.jp/'

# サーバーへの負荷を抑えるため、リクエスト前に1秒待機
time.sleep(1)
res = requests.get(url, timeout=30)

print(f"ステータスコード：{res.status_code}")
res.raise_for_status()

# HTMLを解析し、Webページのタイトルを取得
html_soup = BeautifulSoup(res.content, 'html.parser')
title = html_soup.title.string
print(f"タイトル：{title}")

# データを管理する辞書を初期化
pages = {}
pages[url] = title
print(pages)

# 対象を同一サイト内に限定するため、対象ドメインを抽出
domain = urlparse(url).netloc

# ページ内にあるリンク付きタグをすべて抽出
links = html_soup.find_all('a', href=True)
same_domain_urls = []

for link in links:
    # 相対パスを絶対URLの形式に補正
    next_url = urljoin(res.url, link['href'])

    # ページ内アンカーを切り捨てる
    next_url = urldefrag(next_url)[0]

    # URL構造の要素を解析
    parsed_url = urlparse(next_url)

    # 同一ドメインかつHTTP/HTTPS通信のURLのみを重複なしでリストに追加
    if parsed_url.scheme in ('http', 'https') and parsed_url.netloc == domain:
        if next_url not in same_domain_urls:
            same_domain_urls.append(next_url)

for next_url in same_domain_urls:
    print(next_url)

print(f"同一ドメインの重複しないURL数：{len(same_domain_urls)}")

# 検出したURLリストをキューのように順次処理
index = 0
while index < len(same_domain_urls):
    page_url = same_domain_urls[index]
    index += 1
    # 既にタイトル取得済みのURLはスキップ
    if page_url in pages:
        continue

    time.sleep(1)
    try:
        res = requests.get(page_url, timeout=30)
        res.raise_for_status()
    except requests.RequestException as error:
        print(f"取得失敗：{page_url}：{error}")
        continue

    # リダイレクトによって外部ドメインに移動した場合はスキップ
    if urlparse(res.url).netloc != domain:
        continue

    # 画像やPDFなどの非HTMLコンテンツは除外
    content_type = res.headers.get('Content-Type', '').lower()
    if 'text/html' not in content_type:
        continue

    html_soup = BeautifulSoup(res.content, 'html.parser')

    # title要素が存在すればその文字列を取得し、存在しなければ空文字をセット
    if html_soup.title is not None:
        title = html_soup.title.get_text()
    else:
        title = ''

    pages[page_url] = title
    print(f"{page_url} → {title}")
    links = html_soup.find_all('a', href=True)

    for link in links:
        next_url = urljoin(res.url, link['href'])
        next_url = urldefrag(next_url)[0]
        parsed_url = urlparse(next_url)

        if parsed_url.scheme in ('http', 'https') and parsed_url.netloc == domain:
            if next_url not in same_domain_urls:
                same_domain_urls.append(next_url)

print(f"タイトルを保存したページ数：{len(pages)}")
print(f"リンク先も調べた後のURL数：{len(same_domain_urls)}")

# 収集したURLとタイトルのペアをCSV出力
with open('sitemap.csv', 'w', encoding='utf-8-sig', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['URL', 'タイトル'])
    writer.writerows(pages.items())

print('sitemap.csvに保存しました')
