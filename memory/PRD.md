# The Drop - No Cap News - PRD

## Problem Statement
Build a full-stack news aggregator app called "The Drop" with mobile-first responsive frontend for kids aged 8-20. Crawls real news daily, rewrites each article in age-appropriate language using AI (OpenAI GPT-4o), serves a mobile-first card-based feed. Tagline: "No Cap News".

## Architecture
- **Backend**: FastAPI + MongoDB + OpenAI GPT-4o (via Emergent LLM key)
- **Frontend**: React + Tailwind CSS + Framer Motion
- **Data**: RSS feeds from 200+ international sources across 20 countries
- **AI**: emergentintegrations library with GPT-4o for multi-lingual article rewriting

## User Personas
- **Group A (8-10)**: Kids - simple language, big images, emojis, short sentences
- **Group B (11-13)**: Tweens - conversational, relatable, Gen Z hints
- **Group C (14-16)**: Teens - Gen Z tone, social-media style, nuanced
- **Group D (17-20)**: Young Adults - near-adult, analytical, critical thinking

## Core Requirements
1. RSS news crawling from 200+ international sources
2. AI-powered article rewriting per age group (4 variants) using GPT-4o
3. Mobile-first card-based feed with country-based filtering
4. Dynamic theming (Playground Pop for kids, Midnight Oil for teens)
5. 6 content categories with filtering
6. Age group selector (onboarding + profile settings)
7. Country selector with flag emojis in Profile
8. Multi-lingual processing — GPT-4o handles all source languages natively
9. Low confidence flag for Urdu/Bangla articles
10. Retry logic for rewrite failures

## What's Been Implemented

### Phase 1 — MVP (March 9, 2026)
- [x] Backend: Full API with crawl, rewrite, articles, users, categories, stats endpoints
- [x] JWT Authentication: register, login, profile management
- [x] User model: full_name, email, password, DOB, gender, city, country
- [x] Auto age-group calculation from date of birth
- [x] RSS crawling from BBC and NY Times across 6 categories
- [x] GPT-5.2 rewriting with age-appropriate prompts + safety wrapper (now upgraded to GPT-4o)
- [x] System prompts stored in MongoDB (editable via API)
- [x] Splash screen, Auth page, Feed page, Article page, Profile page
- [x] Dynamic theming, Protected routes, Bottom navigation

### Phase 2 — Engagement Features (March 9, 2026)
- [x] Reading Streak with personal best tracking
- [x] "Did You Know?" Micro-Facts (GPT-4o generated)
- [x] Reaction Bar (5 emoji reactions)
- [x] Trust Badges (Source logos)
- [x] "Why This Story?" Explainer
- [x] Push Notification System (Web Notifications API)

### Phase 3 — International Expansion (March 9, 2026)
- [x] **20 Countries Database**: US, GB, IN, CA, AU, PK, BD, NG, ZA, DE, FR, JP, BR, MX, KE, EG, AE, ID, PH, KR
- [x] **200+ News Sources**: 10 sources per country with RSS feeds
- [x] **Global Source Schema**: country_code, city_tier_1[5], city_tier_2[5], sources[10], primary_language, crawl_schedule, local_priority
- [x] **Source Schema**: name, url, rss_url, feed_type, category_tags[], language, logo_url, status
- [x] **Updated Article Schema**: article_id, source_name, source_country, source_language, source_url, original_headline, original_body, image_url, published_at, category_tags, crawled_at, safety_status, rewrite_status, low_confidence_flag
- [x] **GPT-4o Multi-Lingual Rewrite**: All source languages passed directly to GPT-4o, output always in English
- [x] **Urdu/Bangla Confidence Check**: CONFIDENCE: HIGH/LOW instruction appended only for Urdu/Bangla sources
- [x] **Rewrite Retry Logic**: On failure → retry once → if fails again, flag for manual review (rewrite_status="failed")
- [x] **Country-Filtered Feed**: Articles filtered by user's selected country
- [x] **Profile Country Selector**: Dropdown with flag emojis and primary language labels
- [x] **Feed Country Display**: Header shows country flag + city, country
- [x] **NewsCard Language Badge**: Shows source language for non-English articles
- [x] **Background Crawling**: All crawl operations run in background (non-blocking)
- [x] **Async RSS Parsing**: feedparser.parse() runs in thread pool with 15s timeout
- [x] **Country-Specific Crawl**: POST /api/crawl/{country_code} endpoint

## API Endpoints
- `/api/auth/{register, login, me}` — Authentication
- `/api/articles`, `/api/articles/{id}` — Article CRUD with country filtering
- `/api/articles/{id}/react`, `/api/articles/{id}/reactions` — Reactions
- `/api/streak`, `/api/streak/read` — Reading streaks
- `/api/prompts`, `/api/prompts/{id}` — System prompts
- `/api/notifications/{settings, register-device, check-streaks}` — Notifications
- `/api/crawl`, `/api/crawl/{country_code}` — Crawl triggers
- `/api/countries`, `/api/countries/{country_code}/sources` — Country data
- `/api/categories` — Content categories
- `/api/stats` — App statistics
- `/api/micro-facts`, `/api/micro-facts/generate` — Micro-facts

### Phase 4 — User Profile & Social System (March 10, 2026)
- [x] Two signup flows: parent-led (under-14) and self-signup (14+)
- [x] Profile page with identity header, stats dashboard (Knowledge Score, streak, reactions)
- [x] Friends system: search, send/accept/decline requests, block
- [x] Invite link system: /join/@username auto-connects friends on signup
- [x] Leaderboard ranked by knowledge_score with is_self flag
- [x] Share button on NewsCard with Web Share API + clipboard fallback
- [x] Privacy rules for under-14 accounts:
  - Child accounts non-searchable in friend search
  - Direct friend requests to children blocked (403)
  - Children can only be added via invite link
  - Mock parent email notification on child friend connection
  - No photo uploads for child accounts (DiceBear avatar only)
- [x] Knowledge Score batch calculation endpoint
- [x] Mock parent email notifications (ready for Resend integration)

## Prioritized Backlog
### P1 (High)
- Weekly News Recap Email System (ON HOLD — awaiting user go-ahead)
- Scheduled daily crawl cron job

### P2 (Medium)
- Search functionality for articles
- Bookmarking/saving articles

### P3 (Low)
- Fix flaky test auth selectors (data-testid)
- Location-based local news
- Content safety classifier
