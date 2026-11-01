# Adding favorite tweets

Every tweet you add goes to the top of **Favorite tweets** on stevenjacobs.com (the newest 6 on the homepage, all of them at stevenjacobs.com/tweets/), about a minute later.

Categories: `auto`, `entrepreneurship`, `marketing` (Marketing / SEO), `ai` (AI & Tech), `funny`, `music`, `sports`, `family`, `watches`.
The old name `business` still works and means Entrepreneurship.

`auto` guesses from the tweet's words. For a smarter guess, add a Claude API key: repo **Settings → Secrets and variables →
Actions → New repository secret**, name `ANTHROPIC_API_KEY`. Then "auto" has Claude read each tweet and pick (a fraction of a
cent per tweet). Picking a category yourself always wins.

## On a computer

1. Open **https://github.com/pageworks-hq/stevenjacobs.com/actions/workflows/add-tweet.yml** (bookmark it).
2. Click **Run workflow** (right side).
3. Paste the tweet link, pick a category, click the green **Run workflow**.

## On iPhone (share sheet)

### 1. Make a key for the shortcut (once, ~2 minutes)

1. Go to **https://github.com/settings/personal-access-tokens/new**
2. Token name: `iPhone tweet shortcut`. Expiration: 1 year (or "No expiration").
3. Resource owner: **pageworks-hq**.
4. Repository access: **Only select repositories** → `stevenjacobs.com`.
5. Permissions → Repository permissions → **Actions: Read and write**. Nothing else.
6. **Generate token** and copy it (starts with `github_pat_`). You only see it once.

This key can only start the "Add favorite tweet" automation on this one site. It can't read your email, other repos or anything else.

### 2. Build the shortcut (once, ~5 minutes)

In the **Shortcuts** app, tap **+** and name it **Add to stevenjacobs.com**. Then:

1. Tap the **ⓘ** (details) → turn on **Show in Share Sheet**. Back on the editor, the top block says
   "Receive **Any** input from **Share Sheet**": tap *Any* and leave only **URLs** and **Text** on.
2. Add **Choose from List**. List items: `auto`, `entrepreneurship`, `marketing`, `ai`, `funny`, `music`, `sports`, `family`, `watches`.
   Prompt: `Category?`
3. Add **Get Contents of URL**:
   - URL: `https://api.github.com/repos/pageworks-hq/stevenjacobs.com/actions/workflows/add-tweet.yml/dispatches`
   - Tap **Show More**. Method: **POST**.
   - Headers: `Authorization` = `Bearer ` followed by your token, and `Accept` = `application/vnd.github+json`
   - Request Body: **JSON**. Add field `ref` (Text) = `main`.
     Add field `inputs` (**Dictionary**) and inside it:
     `url` (Text) = **Shortcut Input** (pick it from the variables bar),
     `category` (Text) = **Chosen Item**.
4. Add **Show Notification**: `Added! Live on stevenjacobs.com in about a minute.`

### 3. Use it

In the X app, on any tweet: **Share** → **Share via…** → **Add to stevenjacobs.com** → pick a category. Done.

## If something goes wrong

- Every add shows up at https://github.com/pageworks-hq/stevenjacobs.com/actions with a ✓ or ✗; tap a run to see why.
- Private, deleted or age-restricted tweets can't be added.
- Adding a tweet that's already there moves it to the top with the new category.
- To remove one, delete its entry in `data/tweets.json` and run `python tools/tweets.py build` (or ask Claude).
