# Production Cost Breakdown

This document outlines the estimated monthly costs for running the Eldorado Masters Pool application in production, **excluding the Slash Golf API subscription**.

## Current Infrastructure

Based on your deployment setup:
- **Database**: Supabase (PostgreSQL)
- **Backend**: Railway
- **Frontend**: Vercel

---

## Monthly Cost Estimate

### **Total: $0 - $5/month** (Free tier for most usage)

---

## Detailed Breakdown

### 1. Supabase (Database) - **FREE**

**Free Tier Includes:**
- ✅ 500 MB database storage
- ✅ 2 GB bandwidth
- ✅ Unlimited API requests
- ✅ Up to 2 projects

**Your Usage:**
- Database size: ~50-100 MB (tournaments, entries, scores, snapshots)
- Bandwidth: Minimal (mostly internal API calls)
- **Cost: $0/month**

**If You Exceed Free Tier:**
- Pro Plan: $25/month (includes 8 GB storage, 50 GB bandwidth)
- **Unlikely needed** unless you store years of historical data

---

### 2. Railway (Backend Hosting) - **FREE to $5/month**

**Free Tier (Hobby Plan):**
- ✅ $5 credit/month (free)
- ✅ 512 MB RAM
- ✅ 1 GB storage
- ✅ 100 GB bandwidth
- ✅ Unlimited deployments

**Your Usage:**
- RAM: ~200-300 MB (FastAPI app)
- Storage: < 100 MB (code + dependencies)
- Bandwidth: ~10-20 GB/month (API calls from frontend)
- **Cost: $0/month** (within free tier)

**If You Exceed Free Tier:**
- Usage-based pricing:
  - Compute: ~$0.000463/GB-hour
  - Bandwidth: $0.10/GB over 100 GB
- **Estimated**: $2-5/month if you exceed free credits

**Note**: Railway charges for:
- Active compute time (when your app is running)
- Bandwidth over 100 GB
- Storage over 1 GB

**Your App Runs 24/7**: 
- ~730 hours/month
- At 512 MB RAM: ~0.5 GB
- Compute cost: 730 × 0.5 × $0.000463 = **~$0.17/month**
- Well within the $5 free credit!

---

### 3. Vercel (Frontend Hosting) - **FREE**

**Free Tier (Hobby Plan):**
- ✅ Unlimited deployments
- ✅ 100 GB bandwidth/month
- ✅ Automatic SSL
- ✅ Global CDN

**Your Usage:**
- Bandwidth: ~5-10 GB/month (static assets + API calls)
- Builds: Unlimited (free tier)
- **Cost: $0/month**

**If You Exceed Free Tier:**
- Pro Plan: $20/month (includes 1 TB bandwidth)
- **Unlikely needed** unless you have massive traffic

---

## Cost Scenarios

### Scenario 1: Light Usage (Current Setup)
- **Supabase**: $0 (free tier)
- **Railway**: $0 (within $5 credit)
- **Vercel**: $0 (free tier)
- **Total: $0/month** ✅

### Scenario 2: Moderate Usage (Growing)
- **Supabase**: $0 (still free tier)
- **Railway**: $2-3/month (slightly over free credit)
- **Vercel**: $0 (still free tier)
- **Total: $2-3/month**

### Scenario 3: Heavy Usage (Many Users)
- **Supabase**: $25/month (Pro plan)
- **Railway**: $5-10/month (more compute)
- **Vercel**: $20/month (Pro plan)
- **Total: $50-55/month**

---

## What Could Increase Costs?

### Database (Supabase)
- **Storage**: If you store 5+ years of tournament data → Need Pro plan ($25/month)
- **Bandwidth**: If you have 1000+ concurrent users → May need Pro plan

### Backend (Railway)
- **Compute**: If you upgrade to 1 GB RAM → ~$0.34/month
- **Bandwidth**: If you exceed 100 GB/month → $0.10/GB
- **Multiple Services**: If you add Redis, workers, etc. → Additional costs

### Frontend (Vercel)
- **Bandwidth**: If you exceed 100 GB/month → Need Pro plan ($20/month)
- **Team Features**: If you need team collaboration → Pro plan

---

## Cost Optimization Tips

### 1. Stay on Free Tiers
- ✅ Current setup is optimized for free tiers
- ✅ Database size is minimal
- ✅ Bandwidth usage is low

### 2. Monitor Usage
- Set up alerts in Railway for usage approaching limits
- Monitor Supabase storage growth
- Track Vercel bandwidth usage

### 3. Optimize if Needed
- **Database**: Archive old tournament data (move to cold storage)
- **Backend**: Use active hours feature (already implemented) to reduce compute
- **Frontend**: Enable caching to reduce bandwidth

---

## Real-World Estimate

Based on your current setup and typical usage patterns:

### **Most Likely Cost: $0/month** 🎉

Your application is well within free tier limits:
- Database: Small (tournament data is minimal)
- Backend: Low compute (FastAPI is lightweight)
- Frontend: Static site (very low bandwidth)

### **Conservative Estimate: $2-5/month**

If you slightly exceed free tiers:
- Railway might charge $2-3/month
- Everything else stays free

### **Worst Case: $50-55/month**

Only if you have:
- 1000+ concurrent users
- Years of historical data
- High bandwidth usage

---

## Summary

**Current Production Cost: $0/month** (excluding Slash Golf API)

Your infrastructure is optimized for free tiers, and your usage patterns suggest you'll stay within free limits for the foreseeable future. The only potential cost is Railway if you exceed the $5/month credit, which is unlikely with your current setup.

**Recommendation**: Start with free tiers and monitor usage. Upgrade only if you hit limits or need additional features.

---

## Additional Notes

- **Slash Golf API**: Not included in this breakdown (separate subscription)
- **Domain Name**: Optional (~$10-15/year if you want a custom domain)
- **Email Service**: If you add email notifications later (SendGrid free tier: 100 emails/day)
- **Monitoring**: Consider free services like Sentry (error tracking) or UptimeRobot (uptime monitoring)

---

*Last Updated: January 2026*
*Based on current pricing as of January 2026*
