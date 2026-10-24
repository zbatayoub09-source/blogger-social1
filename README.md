# Blogger Social Publisher — DealZone

This project publishes product posts from `products.csv` to the DealZone Blogger blog.

## Files
- `products.csv`: product source data. Keep the original headers; supported columns include Title, Image, Promotion Url, ProductId, Origin Price, Discount Price, Sales180Day.
- `blogger_publish.py`: Blogger API publisher, basic SEO title/description/hashtags, checkpoint and duplicate avoidance.
- `requirements.txt`: Python dependencies.
- `.github/workflows/blogger-publish.yml`: scheduled/manual GitHub Actions workflow.

## Important setup
Publishing cannot start until Google OAuth is configured. Do not commit `token.json`, client-secret JSON, refresh tokens, or other credentials.

For local use:
1. Install Python 3.11+.
2. Run `py -m pip install -r requirements.txt`.
3. Enable Blogger API in Google Cloud and create OAuth Desktop credentials.
4. Complete OAuth locally to create `token.json` with the Blogger scope.
5. Run `py blogger_publish.py`.

The script expects `token.json` beside the script and uses blog ID `1419305768199826334` by default. Change `BLOGGER_BLOG_ID` if publishing to a different blog.

## GitHub Actions
Add repository secrets `BLOGGER_TOKEN_JSON` (the full contents of a valid authorized token JSON) and `BLOGGER_BLOG_ID`. Workflow writes the token only into the temporary runner and removes it afterward. For stronger security and reliability, use a dedicated OAuth refresh-token flow and rotate credentials if exposed.

The workflow runs every 6 hours and can be started manually. It publishes at most 5 new posts per run. GitHub-hosted runners are temporary, so checkpoint persistence must be configured before relying on scheduled runs for duplicate avoidance; this starter does not commit runtime checkpoint files.

## Notes
- Existing product CSV is retained to avoid losing your data.
- Blogger theme XML cannot be automatically applied by GitHub; upload it manually in Blogger → Theme → Restore.
- Platform APIs impose quotas. If Blogger returns 429/rate-limit errors, stop and retry later.
