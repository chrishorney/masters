# Quick Guide: Push to GitHub

## Current Status ✅
- ✅ All code is committed locally
- ✅ You're on `main` branch
- ✅ 10+ commits ready to push
- ⚠️ Need to create GitHub repository and push

## Step-by-Step: Get Your Code on GitHub

### Step 1: Create GitHub Repository

1. **Go to GitHub**: https://github.com
2. **Sign in** (or create account if needed)
3. **Click the "+" icon** (top right) → **"New repository"**
4. **Fill in:**
   - **Repository name**: `eldorado-masters-pool` (or your choice)
   - **Description**: "Eldorado Masters Golf Tournament Pool"
   - **Visibility**: 
     - ✅ **Private** (recommended - keeps your code secure)
     - Or Public (if you want it open)
   - **DO NOT** check any boxes (no README, no .gitignore, no license)
5. **Click "Create repository"**

### Step 2: Copy Your Repository URL

After creating, GitHub will show you a page with setup instructions. You'll see a URL like:
```
https://github.com/YOUR_USERNAME/eldorado-masters-pool.git
```

**Copy this URL** - you'll need it in the next step!

### Step 3: Connect and Push

Run these commands (replace `YOUR_USERNAME` and `REPO_NAME` with your actual values):

```bash
cd "/Volumes/External HD/masters"

# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Verify it was added
git remote -v

# Push everything to GitHub
git push -u origin main
```

### Step 4: Authenticate

When you run `git push`, you'll be prompted:
- **Username**: Your GitHub username
- **Password**: Use a **Personal Access Token** (NOT your GitHub password)

#### How to Create Personal Access Token:

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Fill in:
   - **Note**: "Masters Pool Deployment"
   - **Expiration**: Choose (90 days is good)
   - **Scopes**: Check **`repo`** (gives full repository access)
4. Click **"Generate token"**
5. **IMPORTANT**: Copy the token immediately (you won't see it again!)
6. Use this token as your password when pushing

### Step 5: Verify

1. Go back to your GitHub repository page
2. Refresh the page
3. You should see all your files:
   - `backend/` folder
   - `frontend/` folder
   - `README.md`
   - All documentation files
   - etc.

## Quick Command Reference

```bash
# Check what will be pushed
git ls-files | head -20

# See commit history
git log --oneline -10

# Add GitHub remote (do this once)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Check remote is set
git remote -v

# Push to GitHub
git push -u origin main
```

## Troubleshooting

**"remote origin already exists"**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

**"Authentication failed"**
- Make sure you're using a Personal Access Token, not your password
- Check the token has `repo` scope
- Try generating a new token

**"Permission denied"**
- Verify repository name is correct
- Check you have write access
- Make sure you're using the correct GitHub username

## What Gets Pushed ✅

- ✅ All source code (`backend/`, `frontend/`)
- ✅ All documentation (`.md` files)
- ✅ Configuration files (`package.json`, `requirements.txt`, etc.)
- ✅ Git history (all your commits)

## What Does NOT Get Pushed 🔒

- 🔒 `backend/.env` (contains database password - good!)
- 🔒 `frontend/.env` (contains API URL - good!)
- 🔒 `node_modules/` (dependencies - will be installed on server)
- 🔒 `venv/` (Python virtual environment)

**This is correct!** Never commit `.env` files with secrets.

## Next Steps After Pushing

Once your code is on GitHub:
1. ✅ Railway can connect to GitHub for backend deployment
2. ✅ Vercel can connect to GitHub for frontend deployment
3. ✅ Your code is backed up
4. ✅ You can deploy automatically on push

---

## Need Help?

If you get stuck:
1. Check the error message
2. Verify your GitHub repository exists
3. Make sure you're using a Personal Access Token
4. Try the troubleshooting steps above
