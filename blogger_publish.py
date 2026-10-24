import csv, json, os, re, time
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

ROOT = Path(__file__).resolve().parent
CSV_PATH = Path(os.getenv("PRODUCTS_CSV", ROOT / "products.csv"))
STATE_PATH = ROOT / "blogger_checkpoint.json"
BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "1419305768199826334")
MAX_PER_RUN = int(os.getenv("MAX_PER_RUN", "5"))
DELAY_SECONDS = int(os.getenv("DELAY_SECONDS", "15"))
SCOPES = ["https://www.googleapis.com/auth/blogger"]

def value(row, *names):
    for name in names:
        for key in row:
            if key and key.strip().lower() == name.lower():
                return (row.get(key) or "").strip()
    return ""

def seo_text(title, sales="", price=""):
    title = re.sub(r"\\s+", " ", title).strip()
    desc = f"Explore {title}. View product details, images and the latest offer. "
    if price: desc += f"Listed price: {price}. "
    if sales: desc += f"Popular item with {sales} sales reported. "
    desc += "Check the product page for availability and current pricing."
    tags = ["#Shopping", "#OnlineDeals", "#ProductFinds"]
    words = re.findall(r"[A-Za-z0-9]+", title)
    if words: tags.insert(0, "#" + "".join(w.title() for w in words[:3]))
    return title[:100], desc[:500], " ".join(tags[:5])

def load_state():
    try: return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception: return {"row_index": 0, "published": []}

def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

def main():
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV not found: {CSV_PATH}")
    creds = Credentials.from_authorized_user_file(str(ROOT / "token.json"), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        (ROOT / "token.json").write_text(creds.to_json(), encoding="utf-8")
    service = build("blogger", "v3", credentials=creds, cache_discovery=False)
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=None if False else ","))
    if not rows:
        raise SystemExit("CSV is empty or its delimiter/header is not supported. Check products.csv.")
    state = load_state()
    published = set(state.get("published", []))
    start = int(state.get("row_index", 0))
    count = 0
    for idx in range(start, len(rows)):
        row = rows[idx]
        title = value(row, "Title", "Product Desc", "Product Description", "SEO_Title", "Name")
        image = value(row, "Image", "Image Url", "Image/Video Url", "Image URL")
        link = value(row, "Promotion Url", "Promotion URL", "Product URL", "Link", "URL")
        pid = value(row, "ProductId", "Product ID", "ID") or f"row-{idx}"
        price = value(row, "Origin Price", "Discount Price", "Price")
        sales = value(row, "Sales180Day", "Sales")
        if not title or pid in published:
            state["row_index"] = idx + 1
            save_state(state)
            continue
        seo_title, description, hashtags = seo_text(title, sales, price)
        img_html = f'<p><img src="{image}" alt="{seo_title}" style="max-width:100%;height:auto"></p>' if image.startswith(("http://","https://")) else ""
        price_html = f"<p><strong>Price:</strong> {price}</p>" if price else ""
        link_html = f'<p><a href="{link}" rel="nofollow sponsored">🛒 تسوق الآن</a></p>' if link.startswith(("http://","https://")) else ""
        content = f"{img_html}<h2>{seo_title}</h2><p>{description}</p>{price_html}{link_html}<p>{hashtags}</p><p><small>Prices and availability may change. Check the product page for current details.</small></p>"
        try:
            service.posts().insert(blogId=BLOG_ID, body={"kind":"blogger#post","title":seo_title,"content":content,"labels":[x.strip("#") for x in hashtags.split()]}, isDraft=False).execute()
            published.add(pid)
            state["published"] = sorted(published)
            state["row_index"] = idx + 1
            save_state(state)
            count += 1
            print(f"Published {count}/{MAX_PER_RUN}: {seo_title}")
            if count >= MAX_PER_RUN: break
            time.sleep(DELAY_SECONDS)
        except HttpError as e:
            print(f"ERROR on row {idx+1}: {e}")
            state["row_index"] = idx
            save_state(state)
            raise
    if state.get("row_index", 0) >= len(rows):
        print("All CSV rows have been checked.")
    print(f"Run finished. New posts: {count}. Checkpoint: {state.get('row_index', 0)}")

if __name__ == "__main__":
    main()
