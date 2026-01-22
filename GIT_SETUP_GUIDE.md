# Git Setup Guide - Getting Your Code on GitHub

This guide will help you commit everything and push to GitHub.

## Step 1: Check Current Status

Let's see what we have:

```bash
cd "/Volumes/External HD/masters"
git status
```

This shows:
- ✅ Files that are committed
- ⚠️ Files that need to be committed
- ❌ Files that are ignored (like .env files)

## Step 2: Commit Everything (if needed)

If there are uncommitted changes:

```bash
cd "/Volumes/External HD/masters"
git add -A
git commit -m "Final commit before deployment"
```

## Step 3: Create GitHub Repository

### Option A: Create on GitHub Website
1. Go to https://github.com
2. Sign in (or create account)
3. Click the **"+"** icon → **"New repository"**
4. Fill in:
   - **Repository name**: `eldorado-masters-pool` (or your choice)
   - **Description**: "Eldorado Masters Golf Tournament Pool"
   - **Visibility**: Private (recommended) or Public
   - **DO NOT** check "Initialize with README" (we already have code)
5. Click **"Create repository"**
6. GitHub will show you commands - **don't run them yet!**

### Option B: Use GitHub CLI (if installed)
```bash
gh repo create eldorado-masters-pool --private --source=. --remote=origin --push
```

## Step 4: Connect Local Repository to GitHub

After creating the repository on GitHub, run:

```bash
cd "/Volumes/External HD/masters"

# Add GitHub as remote (replace with your actual GitHub URL)
git remote add origin https://github.com/YOUR_USERNAME/eldorado-masters-pool.git

# Verify it was added
git remote -v
```

**Replace `YOUR_USERNAME` with your actual GitHub username!**

## Step 5: Push to GitHub

```bash
# Make sure you're on main branch
git branch -M main

# Push everything to GitHub
git push -u origin main
```

You'll be prompted for GitHub credentials:
- **Username**: Your GitHub username
- **Password**: Use a Personal Access Token (not your password)

### How to Create Personal Access Token:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name it (e.g., "Masters Pool Deployment")
4. Select scopes: Check `repo` (full control)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)
7. Use this token as your password when pushing

## Step 6: Verify Everything is on GitHub

1. Go to your repository on GitHub
2. You should see all your files:
   - `backend/` folder
   - `frontend/` folder
   - `README.md`
   - All documentation files
   - etc.

## What Should NOT Be on GitHub

These files are in `.gitignore` and won't be pushed:
- ✅ `backend/.env` (contains secrets)
- ✅ `frontend/.env` (contains secrets)
- ✅ `node_modules/` (dependencies)
- ✅ `venv/` (Python virtual environment)
- ✅ `__pycache__/` (Python cache)
- ✅ `.DS_Store` (Mac system files)

**This is correct!** Never commit `.env` files.

## Troubleshooting

### Problem: "remote origin already exists"
```bash
# Remove existing remote
git remote remove origin

# Add new one
git remote add origin https://github.com/YOUR_USERNAME/eldorado-masters-pool.git
```

### Problem: "Authentication failed"
- Make sure you're using a Personal Access Token, not your password
- Check the token has `repo` scope
- Try generating a new token

### Problem: "Permission denied"
- Verify the repository name matches
- Check you have write access to the repository
- Make sure you're using the correct GitHub username

### Problem: "Large files" error
- GitHub has file size limits
- Large files in `Slash Golf Jsons/` might need to be excluded
- Add to `.gitignore` if needed

## Quick Checklist

- [ ] All code committed locally (`git status` shows clean)
- [ ] GitHub repository created
- [ ] Remote added (`git remote -v` shows your repo)
- [ ] Code pushed to GitHub (`git push` succeeded)
- [ ] Verified files on GitHub website
- [ ] `.env` files are NOT on GitHub (good!)

## Next Steps After Git Setup

Once everything is on GitHub:
1. ✅ Proceed with deployment (Railway/Vercel can connect to GitHub)
2. ✅ Your code is backed up
3. ✅ You can deploy from GitHub

---

## Quick Command Reference

```bash
# Check status
git status

# See what's committed
git log --oneline -5

# Add all changes
git add -A

# Commit
git commit -m "Your message here"

# Check remotes
git remote -v

# Add GitHub remote
git remote add origin https://github.com/USERNAME/REPO.git

# Push to GitHub
git push -u origin main
```
