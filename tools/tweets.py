"""Favorite tweets on the homepage.

  python tools/tweets.py add <tweet url> [category]   fetch a tweet, put it first, rebuild the page
  python tools/tweets.py build                        rebuild the cards in index.html from data/tweets.json

The list lives in data/tweets.json (newest first). Cards are plain HTML so photos and
videos show even where X's embed script is blocked.
"""
import html, io, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'tweets.json')
PAGE = os.path.join(ROOT, 'index.html')

CATS = [('all', 'All'), ('business', 'Business'), ('marketing', 'Marketing'), ('ai', 'AI &amp; Tech'), ('funny', 'Funny'),
        ('music', 'Music'), ('sports', 'Sports'), ('family', 'Family'), ('watches', 'Watches')]
# rough guesses for "auto"; the first category with a hit wins
KEYWORDS = [
    ('watches', r'\b(rolex|watch|patek|omega|audemars|ap royal|gmt|daytona|submariner)\b'),
    ('music', r'\b(dj|song|album|rapper|concert|festival|beat|spotify|music|producer|edm|rave)\b'),
    ('sports', r'\b(nfl|nba|mlb|football|basketball|baseball|soccer|golf|ufc|touchdown|longhorns|qb|quarterback)\b'),
    ('family', r'\b(kids?|son|daughter|baby|toddler|wife|husband|dad|mom|parent|family|children)\b'),
    ('marketing', r'\b(seo|ads?|meta ads|google ads|tiktok|viral|views|youtube|faceless|ugc|creative|funnel|backlinks?|indexed|organic|cpm|cpc|newsletter)\b'),
    ('ai', r'\b(ai|claude|gpt|chatgpt|grok|gemini|llm|openai|anthropic|cursor|replit|vibe.?cod|prompt|agent|model)\b'),
    ('business', r'(\$|\bmrr\b|\barr\b|revenue|profit|startup|founder|business|app store|saas|\bmo\b|/month|million)'),
    ('funny', r'(😂|🤣|😭|lmao|lol|hilarious|funny|meme)'),
]
MON = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
XSVG = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.8 3h3.1l-6.8 7.7L22 21h-6.2l-4.9-6.4L5.3 21H2.2l7.2-8.3L1.8 '
        '3h6.4l4.4 5.8zm-1.1 16.2h1.7L7.3 4.7H5.5z"/></svg>')


def fetch(tweet_id):
    req = urllib.request.Request(f'https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=a',
                                 headers={'User-Agent': 'Mozilla/5.0'})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    if d.get('__typename') != 'Tweet':
        raise SystemExit(f'Could not read tweet {tweet_id} (private, deleted or age-restricted?)')

    def media_of(t):
        out = []
        for x in t.get('mediaDetails', []):
            if x['type'] == 'photo':
                out.append({'type': 'photo', 'src': x['media_url_https'], 'w': x['original_info']['width'], 'h': x['original_info']['height']})
            else:
                v = sorted((y for y in x.get('video_info', {}).get('variants', []) if y.get('content_type') == 'video/mp4'),
                           key=lambda y: y.get('bitrate', 0))
                pick = next((y for y in v if y.get('bitrate', 0) >= 800000), v[-1] if v else None)
                if pick:
                    out.append({'type': 'video', 'poster': x['media_url_https'], 'src': pick['url'],
                                'w': x['original_info']['width'], 'h': x['original_info']['height']})
        return out

    media = media_of(d) or (media_of(d['quoted_tweet']) if d.get('quoted_tweet') else [])
    a, b = d.get('display_text_range', [0, len(d['text'])])
    text = d['text'][a:b]
    for u in d.get('entities', {}).get('urls', []):
        text = text.replace(u['url'], u.get('display_url', u['expanded_url']))
    for x in d.get('entities', {}).get('media', []):
        text = text.replace(x['url'], '')
    # X Articles only carry a link; use the article's title, opening and cover instead
    art = d.get('article')
    if art:
        text = (art.get('title', '') + '\n\n' + art.get('preview_text', '')).strip()
        cover = (art.get('cover_media') or {}).get('media_info') or {}
        if cover.get('original_img_url') and not media:
            media = [{'type': 'photo', 'src': cover['original_img_url'], 'w': cover['original_img_width'], 'h': cover['original_img_height']}]
    return {'id': tweet_id, 'name': d['user']['name'], 'handle': d['user']['screen_name'],
            'avatar': d['user']['profile_image_url_https'], 'verified': d['user'].get('is_blue_verified', False),
            'text': html.unescape(text.strip()), 'date': d['created_at'][:10], 'likes': d.get('favorite_count', 0), 'media': media}


def guess(text):
    t = text.lower()
    for cat, pat in KEYWORDS:
        if re.search(pat, t):
            return cat
    return 'business'


def fmt(n):
    if n >= 1_000_000:
        return f'{n / 1e6:.1f}M'.replace('.0M', 'M')
    return f'{n / 1000:.1f}K'.replace('.0K', 'K') if n >= 1000 else str(n)


def body(t):
    t = html.escape(t)
    t = re.sub(r'(?<![\w/])@(\w{1,15})', r'<a href="https://x.com/\1" target="_blank" rel="noopener">@\1</a>', t)
    t = re.sub(r'(?<![\w@/.])((?:[\w-]+\.)+(?:com|io|ai|co|org|net|app|dev)(?:/[^\s<]*)?)',
               r'<a href="https://\1" target="_blank" rel="noopener">\1</a>', t)
    return t.replace('\n', '<br>')


def card(d, label):
    url = f'https://x.com/{d["handle"]}/status/{d["id"]}'
    y, m, dd = d['date'].split('-')
    media = ''
    if d['media']:
        cells = ''
        for x in d['media'][:4]:
            if x['type'] == 'photo':
                cells += (f'<a href="{url}" target="_blank" rel="noopener"><img src="{x["src"]}?name=medium" alt="" loading="lazy" '
                          f'width="{x["w"]}" height="{x["h"]}"></a>')
            else:
                cells += (f'<button type="button" class="tc-vid" data-src="{x["src"]}" aria-label="Play video">'
                          f'<img src="{x["poster"]}?name=medium" alt="" loading="lazy" width="{x["w"]}" height="{x["h"]}"><i></i></button>')
        media = f'<div class="tc-media n{min(len(d["media"]), 4)}">{cells}</div>'
    more = f' <a class="tc-more" href="{url}" target="_blank" rel="noopener">Show more</a>' if len(d['text']) >= 260 else ''
    tick = '<span class="tc-tick" aria-label="Verified">✓</span>' if d['verified'] else ''
    return f'''          <div class="tw" data-cat="{d["cat"]}"><span class="cat">{label}</span>
            <article class="tc">
              <header><img class="tc-av" src="{d["avatar"]}" alt="" width="40" height="40" loading="lazy"><div><b>{html.escape(d["name"])}{tick}</b><span>@{d["handle"]}</span></div><a class="tc-x" href="{url}" target="_blank" rel="noopener" aria-label="View on X">{XSVG}</a></header>
              <p>{body(d["text"])}{more}</p>
              {media}
              <footer><span>{MON[int(m) - 1]} {int(dd)}, {y}</span><span>♥ {fmt(d["likes"])}</span><a href="{url}" target="_blank" rel="noopener">View on X →</a></footer>
            </article>
          </div>
'''


def load():
    with io.open(DATA, encoding='utf-8') as f:
        return json.load(f)


def save(tweets):
    with io.open(DATA, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(tweets, f, ensure_ascii=False, indent=1)
        f.write('\n')


def build(tweets):
    label = dict(CATS)
    with io.open(PAGE, encoding='utf-8') as f:
        s = f.read()
    start = s.index('<div class="tweets" id="tweetGrid">\n') + len('<div class="tweets" id="tweetGrid">\n')
    end = s.index('        </div>\n        <div class="tw-more" id="tweetMore">', start)
    s = s[:start] + ''.join(card(t, label[t['cat']]) for t in tweets) + s[end:]
    counts = {c: sum(1 for t in tweets if t['cat'] == c) for c, _ in CATS}
    counts['all'] = len(tweets)
    tabs = ''.join(f'<button type="button" data-cat="{c}" aria-pressed="{"true" if c == "all" else "false"}">{n}<sup>{counts[c]}</sup></button>'
                   for c, n in CATS if counts[c])
    s = re.sub(r'(<div class="tabs" role="group" aria-label="Filter tweets">).*?(</div></div>)', lambda m: m.group(1) + tabs + m.group(2), s, count=1)
    s = re.sub(r'Show all <span>\d+</span> tweets', f'Show all <span>{len(tweets)}</span> tweets', s)
    with io.open(PAGE, 'w', encoding='utf-8', newline='') as f:
        f.write(s)


def main(argv):
    if len(argv) >= 2 and argv[0] == 'add':
        m = re.search(r'(?:x|twitter)\.com/\w+/status(?:es)?/(\d+)', argv[1])
        if not m:
            raise SystemExit(f'Not a tweet link: {argv[1]}')
        cat = (argv[2] if len(argv) > 2 else 'auto').strip().lower()
        tweets = [t for t in load() if t['id'] != m.group(1)]
        t = fetch(m.group(1))
        t['cat'] = guess(t['text']) if cat in ('', 'auto') else cat
        if t['cat'] not in dict(CATS):
            raise SystemExit(f'Unknown category "{cat}". Use one of: {", ".join(c for c, _ in CATS[1:])} or auto')
        tweets.insert(0, t)
        save(tweets)
        build(tweets)
        print(f'Added @{t["handle"]} to {t["cat"]}: {t["text"][:80]!r}')
    elif argv[:1] == ['build']:
        build(load())
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
