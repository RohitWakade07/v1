# Deploy to Railway — 5 Minute Guide

## Prerequisites
- GitHub account
- Railway account (free at railway.app)

## Step 1 — Push to GitHub

```bash
cd "grader system/week1_evaluator/deploy"

git init
git add .
# ⚠️  The private key is in .gitignore — it will NOT be pushed
git commit -m "EEP1 grading server"

# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/eep1-grader.git
git push -u origin main
```

## Step 2 — Deploy on Railway

1. Go to **railway.app** → New Project → Deploy from GitHub
2. Select your `eep1-grader` repo
3. Railway auto-detects Python and deploys

## Step 3 — Set the Private Key

The private key was excluded from git for security. Add it on Railway:

1. In Railway dashboard → your project → **Variables** tab
2. Add variable:
   - Name: `PRIVATE_KEY_CONTENT`
   - Value: paste the entire contents of `keys/instructor_private.pem`

3. Update `app.py` to read from env var — run this one-time patch:

```python
# In app.py, replace the decrypt_eep1 function's key handling:
# Instead of a file path, write the key to a temp file from env var
```

Or use the simpler approach: in Railway Variables, set:
```
PRIVATE_KEY_PATH = /app/keys/instructor_private.pem
```
And add the key file via Railway's file mount (Pro feature), OR use the env var approach below.

## Step 4 — Private Key via Environment Variable (Recommended)

Add this to the top of `app.py` after imports:

```python
# Write private key from env var to temp file at startup
_KEY_CONTENT = os.environ.get("PRIVATE_KEY_CONTENT", "")
if _KEY_CONTENT:
    _key_tmp = Path("/tmp/instructor_private.pem")
    _key_tmp.write_text(_KEY_CONTENT)
    PRIVATE_KEY_PATH = str(_key_tmp)
```

Set in Railway Variables:
- `PRIVATE_KEY_CONTENT` = (paste full PEM content)

## Step 5 — Your live URL

Railway gives you a URL like: `https://eep1-grader-production.up.railway.app`

Update `eep1_verifier.sh` — students will download from:
```
https://your-app.up.railway.app/download/eep1_verifier.sh
```

And upload their `.eep1` to:
```
https://your-app.up.railway.app
```

## That's it!

Railway handles:
- HTTPS automatically (free SSL cert)
- Auto-restart if server crashes
- Logs in the Railway dashboard
- Custom domain (optional, free)
