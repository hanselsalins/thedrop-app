from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from openai import OpenAI
import os
import logging
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, date, timedelta
import feedparser
import asyncio
import bcrypt
import jwt
import json as json_module
import re
import string
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from global_sources import GLOBAL_SOURCES, get_country_by_code, get_active_sources, get_countries_list

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

JWT_SECRET = os.environ.get('JWT_SECRET', 'thedrop-nocap-secret-2026')
JWT_ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Helpers ---
def calculate_age_group(dob_str: str) -> str:
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age <= 10:
            return "8-10"
        elif age <= 13:
            return "11-13"
        elif age <= 16:
            return "14-16"
        else:
            return "17-20"
    except Exception:
        return "14-16"


def create_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc).timestamp() + 86400 * 30}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def age_group_from_age(age: int) -> str:
    if age <= 10:
        return "8-10"
    elif age <= 13:
        return "11-13"
    elif age <= 16:
        return "14-16"
    else:
        return "17-20"


def generate_invite_code() -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


async def ensure_unique_username(base: str) -> str:
    clean = re.sub(r'[^a-z0-9_]', '', base.lower())
    if len(clean) < 3:
        clean = clean + ''.join(random.choices(string.ascii_lowercase, k=3 - len(clean)))
    username = clean[:20]
    exists = await db.users.find_one({"username": username})
    if not exists:
        return username
    for _ in range(10):
        candidate = f"{clean[:16]}{random.randint(100, 9999)}"
        exists = await db.users.find_one({"username": candidate})
        if not exists:
            return candidate
    return f"{clean[:14]}{uuid.uuid4().hex[:6]}"


def mock_send_parent_email(parent_email: str, child_name: str):
    """Mock email send — ready to connect to Resend later."""
    logger.info(f"[MOCK EMAIL] To: {parent_email}")
    logger.info(f"[MOCK EMAIL] Subject: You just set up {child_name} on The Drop")
    logger.info(f"[MOCK EMAIL] Body: Hi! You've created a safe news account for {child_name} on The Drop. "
                f"All content is age-appropriate and AI-curated. Visit your profile to manage settings.")


def mock_send_parent_email_friend_request(parent_email: str, child_name: str, friend_name: str):
    """Mock parent notification for friend request involving a child account."""
    logger.info(f"[MOCK PARENT NOTIFICATION] To: {parent_email}")
    logger.info(f"[MOCK PARENT NOTIFICATION] Subject: {child_name} has a new friend on The Drop")
    logger.info(f"[MOCK PARENT NOTIFICATION] Body: Hi! {friend_name} just connected with {child_name} on The Drop via invite link. "
                f"All interactions are safe — no direct messaging is allowed.")


def today_str():
    return date.today().isoformat()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    except Exception:
        pass
    return None


# --- Models ---
class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    dob: str
    gender: str
    city: str
    country: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class RegisterChildRequest(BaseModel):
    parent_name: str
    parent_email: str
    parent_password: str
    child_name: str
    child_age: int
    child_country: str
    child_city: str = ""
    avatar_url: str = ""


class RegisterSelfRequest(BaseModel):
    full_name: str
    email: str
    password: str
    age: int
    country: str
    city: str = ""
    username: str
    avatar_url: str = ""

class ReactionRequest(BaseModel):
    reaction: str  # "mind_blown", "surprising", "angry", "sad", "inspiring"

class PromptUpdate(BaseModel):
    prompt: str

class NotificationSettingsUpdate(BaseModel):
    streak_reminders: Optional[bool] = None
    milestone_alerts: Optional[bool] = None
    daily_news_alerts: Optional[bool] = None

class DeviceTokenRequest(BaseModel):
    token: str
    platform: str = "web"  # "web", "ios", "android"


VALID_REACTIONS = ["mind_blown", "surprising", "angry", "sad", "inspiring"]
REACTION_EMOJIS = {
    "mind_blown": "🤯",
    "surprising": "😮",
    "angry": "😡",
    "sad": "😢",
    "inspiring": "💪",
}

CATEGORIES = [
    {"id": "world", "name": "What's Happening", "icon": "globe", "color": "#3A86FF"},
    {"id": "science", "name": "Science & Discovery", "icon": "flask", "color": "#39FF14"},
    {"id": "money", "name": "Money & Economy", "icon": "coins", "color": "#FFD60A"},
    {"id": "history", "name": "History in the Making", "icon": "hourglass", "color": "#FF6B35"},
    {"id": "entertainment", "name": "Entertainment", "icon": "music", "color": "#FF006E"},
    {"id": "local", "name": "In Your City", "icon": "map-pin", "color": "#4CC9F0"},
]

# --- Source Logos ---
SOURCE_LOGOS = {
    "BBC News": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/BBC_News_2019.svg/200px-BBC_News_2019.svg.png",
    "BBC Science": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/BBC_News_2019.svg/200px-BBC_News_2019.svg.png",
    "BBC Business": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/BBC_News_2019.svg/200px-BBC_News_2019.svg.png",
    "BBC Entertainment": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/BBC_News_2019.svg/200px-BBC_News_2019.svg.png",
    "NY Times": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Nytimes_hq.jpg/200px-Nytimes_hq.jpg",
    "Reuters": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Reuters_Logo.svg/200px-Reuters_Logo.svg.png",
    "AP News": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Associated_Press_logo_2012.svg/200px-Associated_Press_logo_2012.svg.png",
}

# ===== PROMPTS =====
DEFAULT_AGE_GROUP_PROMPTS = {
    "8-10": {
        "label": "Kid Mode",
        "prompt": """You are a friendly news helper for young kids aged 8-10. Your job is to take a real news story and explain it in a way that a curious 9-year-old would understand and enjoy.

RULES:
- Use very simple words. If a word is hard, explain it immediately in brackets. Example: 'The government (the people who run the country) made a new rule.'
- Write in short sentences. Maximum 15 words per sentence.
- Maximum 150 words for the full article.
- Start with one sentence that tells the child WHY this matters to them or their world.
- Use at least one fun comparison or analogy to something kids know (school, food, games, animals, family).
- Use 2-3 relevant emojis naturally within the text, where they add meaning - not just as decoration at the end.
- End with one simple 'wonder question' - a curious question that makes the child think.
- Never use scary language. If the topic involves conflict or danger, describe it calmly and focus on what people are doing to help.
- Tone: warm, excited, like a favourite teacher explaining something.

OUTPUT FORMAT:
Headline: [Simple, fun headline - max 8 words]
Summary: [1 sentence - what happened, in the simplest terms]
Story: [Full rewritten article - max 150 words]
Wonder Question: [1 curious question for the child]"""
    },
    "11-13": {
        "label": "Tween Mode",
        "prompt": """You are a news writer for middle schoolers aged 11-13. Your job is to take a real news story and make it genuinely interesting and easy to understand for a 12-year-old who doesn't usually read the news.

RULES:
- Use simple, clear language. Avoid jargon or overly academic words.
- Sentences should be mostly short, but you can vary them slightly for rhythm. Maximum 20 words per sentence.
- Maximum 200 words for the full article.
- Start by explaining why this news is relevant to the audience's lives.
- Use at least one clear analogy or comparison to something relatable to their world.
- Use 1-2 relevant emojis naturally within the text.
- End with a 'wonder question' that encourages critical thinking or reflection.
- Avoid overly sensational or alarmist language. Focus on clear, factual reporting.
- Tone: Engaging, informative, slightly informal, relatable.

OUTPUT FORMAT:
Headline: [Catchy and informative headline - max 10 words]
Summary: [1-2 sentences summarizing the main point]
Story: [Rewritten article - max 200 words]
Wonder Question: [A thought-provoking question for the reader]"""
    },
    "14-16": {
        "label": "Teen Mode",
        "prompt": """You are a news writer for teenagers aged 14-16. Your job is to take a real news story and make it compelling, informative, and relevant to their interests and understanding of the world.

RULES:
- Use clear and contemporary language, appropriate for the age group.
- Sentence length can be more varied, but aim for clarity and flow. Maximum 25 words per sentence.
- Maximum 300 words for the full article.
- Begin by highlighting the hook or main point and why it matters to their generation.
- Use analogies or comparisons that resonate with their experiences.
- You can use emojis sparingly (0-1) if they genuinely enhance understanding.
- End with a 'wonder question' that prompts deeper thought.
- Maintain a balanced and objective tone, while still being engaging.
- Tone: Knowledgeable, engaging, relevant, slightly more mature.

OUTPUT FORMAT:
Headline: [Intriguing headline that captures attention - max 12 words]
Summary: [2-3 sentences providing context and key information]
Story: [Rewritten article - max 300 words]
Wonder Question: [A question that encourages critical thinking or speculation]"""
    },
    "17-20": {
        "label": "Young Adult",
        "prompt": """You are a news writer for young adults aged 17-20. Your job is to take a real news story and present it in a way that is insightful, comprehensive, and encourages critical engagement with current events.

RULES:
- Use sophisticated and precise language, suitable for an educated young adult audience.
- Sentence structure can be complex and varied to convey nuanced ideas.
- Maximum 400 words for the full article.
- Start with a strong introduction that establishes the significance and complexity of the news.
- Where appropriate, draw parallels to historical events, theoretical concepts, or wider societal trends.
- Emojis are generally not appropriate for this audience.
- End with a 'wonder question' that challenges assumptions or explores implications.
- Maintain an objective and analytical tone.
- Tone: Insightful, analytical, sophisticated, authoritative.

OUTPUT FORMAT:
Headline: [Sophisticated and informative headline - max 15 words]
Summary: [2-3 sentences providing essential context and analysis]
Story: [Rewritten article - max 400 words]
Wonder Question: [A question that provokes deep thought, debate, or analysis]"""
    }
}

DEFAULT_SAFETY_WRAPPER = """SAFETY RULES (non-negotiable):
- Never include graphic violence descriptions
- No political bias - present facts neutrally
- No inappropriate content for the target age group
- If the article is about sensitive topics, handle with age-appropriate care
- Do not sensationalize or create fear
- Focus on facts and understanding, not shock value"""


async def seed_system_prompts():
    for age_group, data in DEFAULT_AGE_GROUP_PROMPTS.items():
        await db.system_prompts.update_one(
            {"age_range": age_group, "type": "rewrite"},
            {"$set": {"id": f"rewrite_{age_group}", "type": "rewrite", "age_range": age_group,
                       "label": data["label"], "prompt": data["prompt"],
                       "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True)
    await db.system_prompts.update_one(
        {"type": "safety"},
        {"$set": {"id": "safety_wrapper", "type": "safety", "label": "Content Safety Wrapper",
                   "prompt": DEFAULT_SAFETY_WRAPPER, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True)


async def seed_source_logos():
    for name, url in SOURCE_LOGOS.items():
        await db.source_logos.update_one(
            {"source": name},
            {"$set": {"source": name, "logo_url": url, "visible": True}},
            upsert=True)
    logger.info(f"Seeded {len(SOURCE_LOGOS)} source logos")


async def seed_global_sources():
    """Seed the global_sources collection with 20 countries and their news sources."""
    count = 0
    for country in GLOBAL_SOURCES:
        await db.global_sources.update_one(
            {"country_code": country["country_code"]},
            {"$set": {
                "country_code": country["country_code"],
                "country_name": country["country_name"],
                "flag_emoji": country["flag_emoji"],
                "primary_language": country["primary_language"],
                "crawl_schedule": country["crawl_schedule"],
                "local_priority": country["local_priority"],
                "city_tier_1": country["city_tier_1"],
                "city_tier_2": country["city_tier_2"],
                "sources": country["sources"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )
        count += 1
        # Also seed each source into source_logos for quick lookup
        for src in country["sources"]:
            if src.get("logo_url"):
                await db.source_logos.update_one(
                    {"source": src["name"]},
                    {"$set": {"source": src["name"], "logo_url": src["logo_url"], "visible": True}},
                    upsert=True,
                )
    logger.info(f"Seeded {count} countries with global news sources.")


async def get_prompt_for_age_group(age_group: str) -> str:
    doc = await db.system_prompts.find_one({"age_range": age_group, "type": "rewrite"}, {"_id": 0})
    return doc["prompt"] if doc else DEFAULT_AGE_GROUP_PROMPTS.get(age_group, {}).get("prompt", "")

async def get_safety_wrapper() -> str:
    doc = await db.system_prompts.find_one({"type": "safety"}, {"_id": 0})
    return doc["prompt"] if doc else DEFAULT_SAFETY_WRAPPER

async def get_source_logo(source_name: str) -> str:
    doc = await db.source_logos.find_one({"source": source_name}, {"_id": 0})
    return doc.get("logo_url", "") if doc else SOURCE_LOGOS.get(source_name, "")


RSS_FEEDS = {
    "world": [
        {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC News"},
        {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "source": "NY Times"},
    ],
    "science": [
        {"url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "source": "BBC Science"},
        {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml", "source": "NY Times"},
    ],
    "money": [
        {"url": "https://feeds.bbci.co.uk/news/business/rss.xml", "source": "BBC Business"},
        {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "source": "NY Times"},
    ],
    "history": [
        {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC News"},
    ],
    "entertainment": [
        {"url": "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "source": "BBC Entertainment"},
        {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml", "source": "NY Times"},
    ],
    "local": [
        {"url": "https://feeds.bbci.co.uk/news/rss.xml", "source": "BBC News"},
        {"url": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml", "source": "NY Times"},
    ],
}

CATEGORY_IMAGES = {
    "world": "https://images.unsplash.com/photo-1633421878925-ac220d8f6e4f?w=800&q=80",
    "science": "https://images.unsplash.com/photo-1730266718522-ff6d21f3a91f?w=800&q=80",
    "money": "https://images.unsplash.com/photo-1726825779715-b47ced2411a7?w=800&q=80",
    "history": "https://images.unsplash.com/photo-1619525673991-abb47426c650?w=800&q=80",
    "entertainment": "https://images.unsplash.com/photo-1620245446020-879dc5cf2414?w=800&q=80",
    "local": "https://images.unsplash.com/photo-1559038452-c182e478b3e4?w=800&q=80",
}


# ===== NOTIFICATION SYSTEM =====

STREAK_REMINDER_MESSAGES = [
    {"emoji": "🔥", "text": "Don't lose your streak! Today's Drop is waiting."},
    {"emoji": "⚡", "text": "Your streak is on the line. Catch today's Drop."},
    {"emoji": "📰", "text": "One story. That's all it takes. Keep your streak alive."},
    {"emoji": "🔥", "text": "{streak}-day streak at risk. Open The Drop before midnight."},
]

MILESTONE_MESSAGES = {
    7: {"emoji": "🏆", "text": "7-day streak! You're on fire. Keep The Drop going."},
    30: {"emoji": "🔥", "text": "30 days straight. You actually know what's happening in the world. No cap."},
    50: {"emoji": "💎", "text": "50-day streak. You're a news legend in the making."},
    100: {"emoji": "💎", "text": "100-day streak. You are The Drop. Legendary."},
}

MILESTONES = [7, 30, 50, 100]

DEFAULT_NOTIFICATION_PREFS = {
    "streak_reminders": True,
    "milestone_alerts": True,
    "daily_news_alerts": True,
}


async def log_notification(user_id: str, notif_type: str, message: str, delivered: bool = True):
    await db.notification_log.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": notif_type,
        "message": message,
        "delivered": delivered,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def get_notifications_sent_today(user_id: str) -> int:
    today = today_str()
    count = await db.notification_log.count_documents({
        "user_id": user_id,
        "timestamp": {"$regex": f"^{today}"},
    })
    return count


async def check_milestone(user_id: str, streak_count: int) -> dict:
    """Check if the user just hit a milestone. Returns milestone info or None."""
    if streak_count not in MILESTONES:
        return None

    # Check if we already notified this milestone
    existing = await db.notification_log.find_one({
        "user_id": user_id,
        "type": "milestone",
        "message": {"$regex": f"^{streak_count}-day"},
    })
    if existing:
        return None

    msg_data = MILESTONE_MESSAGES.get(streak_count)
    if not msg_data:
        return None

    return {
        "milestone": streak_count,
        "emoji": msg_data["emoji"],
        "message": f"{streak_count}-day streak! {msg_data['text']}",
    }


async def get_streak_reminder_message(user: dict) -> str:
    """Get a random streak reminder message, personalized with streak count."""
    streak = user.get("current_streak", 0)
    msg = random.choice(STREAK_REMINDER_MESSAGES)
    text = msg["text"].replace("{streak}", str(streak))
    return f"{msg['emoji']} {text}"


# ===== AI REWRITING =====
async def rewrite_article_for_age_group(title: str, content: str, age_group: str, category: str,
                                         source_language: str = "English",
                                         source_country: str = "US") -> dict:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        return {"title": title, "summary": content[:150], "body": content, "reading_time": "2 min",
                "low_confidence_flag": False, "rewrite_status": "failed"}

    system_prompt = await get_prompt_for_age_group(age_group)
    safety = await get_safety_wrapper()
    chat = LlmChat(api_key=api_key, session_id=f"rewrite-{uuid.uuid4()}",
                    system_message=system_prompt + "\n" + safety).with_model("openai", "gpt-4o")

    # Build the rewrite prompt — pass source_language directly to GPT-4o
    confidence_instruction = ""
    if source_language in ("Urdu", "Bangla"):
        confidence_instruction = """

IMPORTANT: This article is in {lang}. After rewriting, assess your confidence in the accuracy of the translation/rewrite.
Add a "confidence" key to your JSON response with value "HIGH" or "LOW".
Rate "LOW" if: the source text was ambiguous, contained idioms you're unsure about, or if the meaning might be lost in translation.
Rate "HIGH" if you are confident the rewrite accurately captures the original meaning.""".format(lang=source_language)

    prompt = f"""Rewrite this news article. The source language is {source_language}. Rewrite the output entirely in English regardless of the source language.
Respond in valid JSON only with keys: title, summary, body, wonder_question, reading_time{', confidence' if source_language in ('Urdu', 'Bangla') else ''}.

Source Language: {source_language}
Source Country: {source_country}
Original Title: {title}
Original Content: {content[:2000]}
Category: {category}
Target Age Group: {age_group}

Map: "title"=Headline, "summary"=Summary, "body"=Story, "wonder_question"=Wonder Question, "reading_time"=estimated reading time.
Return ONLY valid JSON, no markdown, no code blocks.{confidence_instruction}"""

    # Retry logic: attempt once, if fails retry, then mark for manual review
    for attempt in range(2):
        try:
            response = await chat.send_message(UserMessage(text=prompt))
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()
            result = json_module.loads(clean)

            # Handle low_confidence_flag for Urdu/Bangla
            if source_language in ("Urdu", "Bangla"):
                confidence = result.pop("confidence", "HIGH").upper()
                result["low_confidence_flag"] = confidence == "LOW"
            else:
                result["low_confidence_flag"] = False

            result["rewrite_status"] = "complete"
            return result
        except Exception as e:
            logger.error(f"AI rewrite attempt {attempt + 1} failed for age_group={age_group}, lang={source_language}: {e}")
            if attempt == 0:
                # Create fresh chat for retry
                chat = LlmChat(api_key=api_key, session_id=f"rewrite-retry-{uuid.uuid4()}",
                                system_message=system_prompt + "\n" + safety).with_model("openai", "gpt-4o")
                continue

    # Both attempts failed — flag for manual review
    logger.error(f"Rewrite failed after 2 attempts: title='{title[:50]}', lang={source_language}")
    return {"title": title, "summary": content[:150], "body": content[:500],
            "reading_time": "2 min", "rewrite_status": "failed",
            "low_confidence_flag": source_language in ("Urdu", "Bangla")}


# ===== MICRO-FACTS GENERATION =====
async def generate_micro_facts(age_group: str):
    # Get today's top article titles for context
    articles = await db.articles.find({}, {"_id": 0, "original_title": 1, "category": 1}).sort("crawled_at", -1).to_list(10)
    titles_context = "\n".join([f"- [{a.get('category','general')}] {a['original_title']}" for a in articles[:8]])

    prompt_intro = {
        "8-10": "You write fun facts for kids aged 8-10. Use very simple words, max 20 words per fact. Make it exciting!",
        "11-13": "You write interesting facts for tweens aged 11-13. Keep it cool and relatable, max 25 words per fact.",
        "14-16": "You write engaging facts for teens aged 14-16. Be informative and slightly edgy, max 30 words per fact.",
        "17-20": "You write insightful facts for young adults aged 17-20. Be sophisticated, max 35 words per fact.",
    }

    msg = f"""Generate 6 surprising "Did You Know?" micro-facts loosely related to today's news topics.

Today's news topics:
{titles_context}

Return ONLY a valid JSON array of objects with keys: "fact" (the micro-fact text), "category" (which news category it relates to: world/science/money/history/entertainment/local).
No markdown, no code blocks. Just the JSON array."""

    try:
        if openai_client is None:
            logger.error("OpenAI client is not configured; skipping micro-fact generation.")
            return

        model = os.environ.get("OPENAI_MODEL_DEFAULT", "gpt-4o-mini")

        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": prompt_intro.get(age_group, prompt_intro["14-16"]),
                },
                {
                    "role": "user",
                    "content": msg,
                },
            ],
        )

        clean = response.choices[0].message.content.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
        facts = json_module.loads(clean)

        today = today_str()
        for f in facts:
            await db.micro_facts.update_one(
                {"fact": f["fact"], "date": today, "age_group": age_group},
                {"$set": {"fact": f["fact"], "category": f.get("category", "general"),
                           "date": today, "age_group": age_group, "id": str(uuid.uuid4())}},
                upsert=True)
        logger.info(f"Generated {len(facts)} micro-facts for age_group={age_group}")
    except Exception as e:
        logger.error(f"Micro-fact generation failed: {e}")


# ===== WHY THIS STORY =====
def generate_why_reason(article: dict, user: dict = None) -> str:
    category = article.get("category", "")
    user_country = user.get("country", "") if user else ""
    user_city = user.get("city", "") if user else ""

    reasons = {
        "local": f"This is a top story from {user_city or user_country or 'your region'} today." if user_country else "This is a local news story relevant to your area.",
        "world": "This story is a major global event everyone's talking about.",
        "science": "This story is trending in Science globally.",
        "money": "This is a key story about the economy that affects everyday life.",
        "history": "This story connects today's events to important historical context.",
        "entertainment": "This story is trending in Entertainment and Culture.",
    }

    return reasons.get(category, "This is part of today's balanced mix across all topics.")


# ===== RSS CRAWLING =====
async def crawl_rss_feeds(country_code: str = None):
    """Crawl RSS feeds. If country_code is provided, crawl only that country.
    Otherwise, crawl all countries from global_sources."""
    logger.info(f"Starting RSS crawl... (country={country_code or 'ALL'})")
    articles_added = 0

    if country_code:
        countries = await db.global_sources.find(
            {"country_code": country_code.upper()}, {"_id": 0}
        ).to_list(1)
    else:
        countries = await db.global_sources.find({}, {"_id": 0}).to_list(50)

    # If no global_sources seeded yet, fall back to legacy feeds
    if not countries:
        return await _crawl_legacy_feeds()

    for country in countries:
        for src in country.get("sources", []):
            if src.get("status") != "active" or src.get("feed_type") != "rss":
                continue
            rss_url = src.get("rss_url", "")
            if not rss_url:
                continue
            try:
                feed = await asyncio.wait_for(
                    asyncio.to_thread(feedparser.parse, rss_url), timeout=15
                )
                if not feed.entries:
                    continue
                for entry in feed.entries[:5]:
                    link = entry.get("link", "")
                    if not link:
                        continue
                    existing = await db.articles.find_one({"original_url": link})
                    if existing:
                        continue

                    image_url = ""
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0].get('url', '')
                    elif hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url', '')
                    if not image_url:
                        image_url = CATEGORY_IMAGES.get(
                            src.get("category_tags", ["world"])[0], CATEGORY_IMAGES.get("world", ""))

                    content = entry.get('summary', entry.get('description', entry.get('title', '')))
                    published = entry.get('published', '') or datetime.now(timezone.utc).isoformat()
                    article_id = str(uuid.uuid4())
                    logo_url = src.get("logo_url", "") or await get_source_logo(src["name"])

                    # Determine category from source's category_tags
                    category = src.get("category_tags", ["world"])[0]

                    await db.articles.insert_one({
                        "id": article_id,
                        "article_id": article_id,
                        "source_name": src["name"],
                        "source": src["name"],
                        "source_country": country["country_code"],
                        "source_language": src.get("language", country.get("primary_language", "English")),
                        "source_url": link,
                        "original_headline": entry.get('title', 'Untitled'),
                        "original_title": entry.get('title', 'Untitled'),
                        "original_body": content,
                        "original_content": content,
                        "original_url": link,
                        "source_logo": logo_url,
                        "category": category,
                        "category_tags": src.get("category_tags", ["world"]),
                        "image_url": image_url,
                        "published_at": published,
                        "crawled_at": datetime.now(timezone.utc).isoformat(),
                        "safety_status": "safe",
                        "rewrite_status": "pending",
                        "low_confidence_flag": False,
                        "rewrites": {},
                        "reaction_counts": {},
                    })
                    articles_added += 1
            except Exception as e:
                logger.error(f"Error crawling {src['name']} ({rss_url}): {e}")
                # Mark as pending_review if first-time failure
                if src.get("status") == "active":
                    await db.global_sources.update_one(
                        {"country_code": country["country_code"], "sources.name": src["name"]},
                        {"$set": {"sources.$.last_error": str(e),
                                  "sources.$.last_error_at": datetime.now(timezone.utc).isoformat()}}
                    )

    logger.info(f"Crawl complete. Added {articles_added} new articles.")
    return articles_added


async def _crawl_legacy_feeds():
    """Fallback: crawl from hardcoded RSS_FEEDS if global_sources not yet seeded."""
    articles_added = 0
    for category, feeds in RSS_FEEDS.items():
        for feed_info in feeds:
            try:
                feed = await asyncio.wait_for(
                    asyncio.to_thread(feedparser.parse, feed_info["url"]), timeout=15
                )
                for entry in feed.entries[:3]:
                    existing = await db.articles.find_one({"original_url": entry.get("link", "")})
                    if existing:
                        continue
                    image_url = ""
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0].get('url', '')
                    elif hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url', '')
                    if not image_url:
                        image_url = CATEGORY_IMAGES.get(category, "")

                    content = entry.get('summary', entry.get('description', entry.get('title', '')))
                    published = entry.get('published', '') or datetime.now(timezone.utc).isoformat()
                    article_id = str(uuid.uuid4())
                    logo_url = await get_source_logo(feed_info["source"])

                    await db.articles.insert_one({
                        "id": article_id, "article_id": article_id,
                        "source_name": feed_info["source"], "source": feed_info["source"],
                        "source_country": "US", "source_language": "English",
                        "source_url": entry.get('link', ''),
                        "original_headline": entry.get('title', 'Untitled'),
                        "original_title": entry.get('title', 'Untitled'),
                        "original_body": content, "original_content": content,
                        "original_url": entry.get('link', ''),
                        "source_logo": logo_url, "category": category,
                        "category_tags": [category],
                        "image_url": image_url, "published_at": published,
                        "crawled_at": datetime.now(timezone.utc).isoformat(),
                        "safety_status": "safe", "rewrite_status": "pending",
                        "low_confidence_flag": False,
                        "rewrites": {}, "reaction_counts": {}
                    })
                    articles_added += 1
            except Exception as e:
                logger.error(f"Error crawling {feed_info['url']}: {e}")
    return articles_added


async def rewrite_pending_articles(age_group: str):
    logger.info(f"Starting rewrites for age_group={age_group}...")
    cursor = db.articles.find(
        {f"rewrites.{age_group}": {"$exists": False}},
        {"_id": 0, "id": 1, "original_title": 1, "original_headline": 1,
         "original_content": 1, "original_body": 1, "category": 1,
         "source_language": 1, "source_country": 1}
    )
    articles = await cursor.to_list(50)
    for article in articles:
        title = article.get("original_headline") or article.get("original_title", "")
        content = article.get("original_body") or article.get("original_content", "")
        source_lang = article.get("source_language", "English")
        source_country = article.get("source_country", "US")

        rewrite = await rewrite_article_for_age_group(
            title, content, age_group, article["category"],
            source_language=source_lang, source_country=source_country)

        update_fields = {f"rewrites.{age_group}": rewrite}
        # Update article-level fields from rewrite result
        if rewrite.get("rewrite_status"):
            update_fields["rewrite_status"] = rewrite["rewrite_status"]
        if rewrite.get("low_confidence_flag") is not None:
            update_fields["low_confidence_flag"] = rewrite["low_confidence_flag"]

        await db.articles.update_one({"id": article["id"]}, {"$set": update_fields})
    logger.info(f"Rewrites complete for {len(articles)} articles, age_group={age_group}")


# ========== AUTH ROUTES ==========
@api_router.post("/auth/register")
async def register(req: RegisterRequest):
    existing = await db.users.find_one({"email": req.email.lower().strip()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    age_group = calculate_age_group(req.dob)
    password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())
    invite_code = generate_invite_code()
    now = datetime.now(timezone.utc).isoformat()
    base_username = re.sub(r'[^a-z0-9_]', '', req.full_name.lower().replace(" ", ""))
    username = await ensure_unique_username(base_username)
    doc = {
        "id": user_id, "full_name": req.full_name.strip(), "email": req.email.lower().strip(),
        "password_hash": password_hash, "dob": req.dob, "gender": req.gender,
        "city": req.city.strip(), "country": req.country.strip(), "age_group": age_group,
        "account_type": "self", "username": username,
        "avatar_url": f"https://api.dicebear.com/9.x/adventurer/svg?seed={username}",
        "invite_code": invite_code, "knowledge_score": 0,
        "member_since": now, "created_at": now,
        "current_streak": 0, "longest_streak": 0, "last_read_date": "",
        "notification_prefs": DEFAULT_NOTIFICATION_PREFS.copy(),
        "device_tokens": [], "timezone": "UTC",
        "stories_read_count": 0, "reactions_given_count": 0, "days_active": [],
    }
    await db.users.insert_one(doc)
    token = create_token(user_id)
    user_resp = {k: v for k, v in doc.items() if k not in ("password_hash", "_id")}
    return {"token": token, "user": user_resp}


@api_router.post("/auth/register-child")
async def register_child(req: RegisterChildRequest):
    """Parent-led signup for under-14 users."""
    existing = await db.users.find_one({"email": req.parent_email.lower().strip()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if req.child_age >= 14:
        raise HTTPException(status_code=400, detail="Use self-signup for age 14+")
    if len(req.parent_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    age_group = age_group_from_age(req.child_age)
    password_hash = bcrypt.hashpw(req.parent_password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())
    invite_code = generate_invite_code()
    now = datetime.now(timezone.utc).isoformat()
    base_username = re.sub(r'[^a-z0-9_]', '', req.child_name.lower().replace(" ", ""))
    username = await ensure_unique_username(base_username)
    approx_dob = f"{date.today().year - req.child_age}-06-15"

    doc = {
        "id": user_id, "full_name": req.child_name.strip(),
        "email": req.parent_email.lower().strip(),
        "password_hash": password_hash,
        "dob": approx_dob, "age": req.child_age, "gender": "",
        "city": req.child_city.strip(), "country": req.child_country.strip(),
        "age_group": age_group, "account_type": "child",
        "parent_name": req.parent_name.strip(),
        "parent_email": req.parent_email.lower().strip(),
        "username": username,
        "avatar_url": req.avatar_url or f"https://api.dicebear.com/9.x/adventurer/svg?seed={username}",
        "invite_code": invite_code, "knowledge_score": 0,
        "member_since": now, "created_at": now,
        "current_streak": 0, "longest_streak": 0, "last_read_date": "",
        "notification_prefs": DEFAULT_NOTIFICATION_PREFS.copy(),
        "device_tokens": [], "timezone": "UTC",
        "stories_read_count": 0, "reactions_given_count": 0, "days_active": [],
    }
    await db.users.insert_one(doc)
    mock_send_parent_email(req.parent_email, req.child_name)
    token = create_token(user_id)
    user_resp = {k: v for k, v in doc.items() if k not in ("password_hash", "_id")}
    return {"token": token, "user": user_resp}


@api_router.post("/auth/register-self")
async def register_self(req: RegisterSelfRequest):
    """Self signup for age 14+."""
    existing = await db.users.find_one({"email": req.email.lower().strip()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if req.age < 14:
        raise HTTPException(status_code=400, detail="Under-14 users must use parent signup")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    username_clean = req.username.lower().strip().lstrip("@")
    if not re.match(r'^[a-z0-9_]{3,20}$', username_clean):
        raise HTTPException(status_code=400, detail="Username must be 3-20 characters, letters, numbers, underscores only")
    existing_username = await db.users.find_one({"username": username_clean})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    age_group = age_group_from_age(req.age)
    password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())
    invite_code = generate_invite_code()
    now = datetime.now(timezone.utc).isoformat()
    approx_dob = f"{date.today().year - req.age}-06-15"

    doc = {
        "id": user_id, "full_name": req.full_name.strip(),
        "email": req.email.lower().strip(),
        "password_hash": password_hash,
        "dob": approx_dob, "age": req.age, "gender": "",
        "city": req.city.strip(), "country": req.country.strip(),
        "age_group": age_group, "account_type": "self",
        "username": username_clean,
        "avatar_url": req.avatar_url or f"https://api.dicebear.com/9.x/adventurer/svg?seed={username_clean}",
        "invite_code": invite_code, "knowledge_score": 0,
        "member_since": now, "created_at": now,
        "current_streak": 0, "longest_streak": 0, "last_read_date": "",
        "notification_prefs": DEFAULT_NOTIFICATION_PREFS.copy(),
        "device_tokens": [], "timezone": "UTC",
        "stories_read_count": 0, "reactions_given_count": 0, "days_active": [],
    }
    await db.users.insert_one(doc)
    token = create_token(user_id)
    user_resp = {k: v for k, v in doc.items() if k not in ("password_hash", "_id")}
    return {"token": token, "user": user_resp}


@api_router.get("/auth/check-username/{username}")
async def check_username(username: str):
    """Check if a username is available."""
    clean = username.lower().strip().lstrip("@")
    if not re.match(r'^[a-z0-9_]{3,20}$', clean):
        return {"available": False, "username": clean, "reason": "Must be 3-20 chars, letters/numbers/underscores only"}
    existing = await db.users.find_one({"username": clean})
    return {"available": existing is None, "username": clean}


@api_router.get("/auth/user-by-invite/{invite_code}")
async def get_user_by_invite(invite_code: str):
    """Look up a user by invite code for the invite landing page."""
    user = await db.users.find_one({"invite_code": invite_code}, {"_id": 0, "password_hash": 0})
    if not user:
        # Also try username lookup
        user = await db.users.find_one({"username": invite_code.lower().strip()}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "full_name": user.get("full_name", ""),
        "username": user.get("username", ""),
        "avatar_url": user.get("avatar_url", ""),
        "knowledge_score": user.get("knowledge_score", 0),
        "current_streak": user.get("current_streak", 0),
        "invite_code": user.get("invite_code", ""),
    }

@api_router.post("/auth/login")
async def login(req: LoginRequest):
    user = await db.users.find_one({"email": req.email.lower().strip()})
    if not user or not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["id"])
    user_resp = {k: v for k, v in user.items() if k != "password_hash" and k != "_id"}
    return {"token": token, "user": user_resp}

@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return user

@api_router.put("/auth/me")
async def update_me(req: UserUpdate, user=Depends(get_current_user)):
    updates = {}
    if req.full_name is not None: updates["full_name"] = req.full_name.strip()
    if req.gender is not None: updates["gender"] = req.gender
    if req.city is not None: updates["city"] = req.city.strip()
    if req.country is not None: updates["country"] = req.country.strip()
    if req.avatar_url is not None: updates["avatar_url"] = req.avatar_url
    if req.username is not None:
        username_clean = req.username.lower().strip().lstrip("@")
        if not re.match(r'^[a-z0-9_]{3,20}$', username_clean):
            raise HTTPException(status_code=400, detail="Invalid username format")
        existing = await db.users.find_one({"username": username_clean, "id": {"$ne": user["id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        updates["username"] = username_clean
    if updates:
        await db.users.update_one({"id": user["id"]}, {"$set": updates})
    return await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})


# ========== STREAK ROUTES ==========
@api_router.post("/streak/read")
async def record_read(user=Depends(get_current_user)):
    today = today_str()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    last_read = user.get("last_read_date", "")
    current = user.get("current_streak", 0)
    longest = user.get("longest_streak", 0)

    if last_read == today:
        return {"current_streak": current, "longest_streak": longest, "last_read_date": today}

    if last_read == yesterday:
        current += 1
    else:
        current = 1

    longest = max(longest, current)
    # Track stories read count and days active
    updates = {
        "current_streak": current, "longest_streak": longest, "last_read_date": today
    }
    await db.users.update_one({"id": user["id"]}, {
        "$set": updates,
        "$inc": {"stories_read_count": 1},
        "$addToSet": {"days_active": today},
    })

    # Check for milestone
    milestone = await check_milestone(user["id"], current)
    if milestone and user.get("notification_prefs", {}).get("milestone_alerts", True):
        await log_notification(user["id"], "milestone", milestone["message"])

    return {"current_streak": current, "longest_streak": longest, "last_read_date": today,
            "milestone": milestone}

@api_router.get("/streak")
async def get_streak(user=Depends(get_current_user)):
    today = today_str()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    last_read = user.get("last_read_date", "")
    current = user.get("current_streak", 0)
    longest = user.get("longest_streak", 0)

    # If missed today AND yesterday, streak is broken
    if last_read and last_read != today and last_read != yesterday:
        current = 0
        await db.users.update_one({"id": user["id"]}, {"$set": {"current_streak": 0}})

    return {"current_streak": current, "longest_streak": longest, "last_read_date": last_read,
            "read_today": last_read == today}


# ========== PROFILE STATS ==========
@api_router.get("/profile/stats")
async def get_profile_stats(user=Depends(get_current_user)):
    """Get comprehensive profile stats for the current user."""
    user_id = user["id"]
    today = today_str()
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1).isoformat()[:10]
    week_start = (now - timedelta(days=now.weekday())).isoformat()[:10]

    # Stories read
    stories_read_total = user.get("stories_read_count", 0)
    days_active = user.get("days_active", [])
    days_active_this_month = [d for d in days_active if d >= month_start]
    days_active_this_week = [d for d in days_active if d >= week_start]

    # Reaction stats
    total_reactions = await db.reactions.count_documents({"user_id": user_id})
    reactions_this_month = await db.reactions.count_documents({
        "user_id": user_id, "created_at": {"$gte": month_start}
    })

    # Most used reaction
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$reaction", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1},
    ]
    most_used = await db.reactions.aggregate(pipeline).to_list(1)
    most_used_reaction = most_used[0]["_id"] if most_used else None

    # Favourite category this month
    cat_pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": month_start}}},
        {"$lookup": {"from": "articles", "localField": "article_id", "foreignField": "id", "as": "article"}},
        {"$unwind": {"path": "$article", "preserveNullAndEmptyArrays": True}},
        {"$group": {"_id": "$article.category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1},
    ]
    fav_cat = await db.reactions.aggregate(cat_pipeline).to_list(1)
    favourite_category = fav_cat[0]["_id"] if fav_cat and fav_cat[0]["_id"] else "world"

    # Streak data
    current_streak = user.get("current_streak", 0)
    longest_streak = user.get("longest_streak", 0)

    # Knowledge Score calculation
    knowledge_score = int(
        (stories_read_total * 1)
        + (current_streak * 2)
        + (total_reactions * 0.5)
        + (len(days_active_this_month) * 3)
    )

    # Rank label
    if knowledge_score >= 501:
        rank_label = "No Cap Legend"
    elif knowledge_score >= 301:
        rank_label = "Sharp"
    elif knowledge_score >= 151:
        rank_label = "Switched On"
    elif knowledge_score >= 51:
        rank_label = "Informed"
    else:
        rank_label = "Curious"

    # Update knowledge score in user doc
    await db.users.update_one({"id": user_id}, {"$set": {"knowledge_score": knowledge_score}})

    # Log knowledge score
    await db.knowledge_score_log.update_one(
        {"user_id": user_id, "calculated_at": today},
        {"$set": {
            "user_id": user_id, "score": knowledge_score, "calculated_at": today,
            "stories_read": stories_read_total, "streak_days": current_streak,
            "reactions_given": total_reactions, "days_active": len(days_active_this_month),
        }},
        upsert=True,
    )

    # Countries covered this week
    countries_pipeline = [
        {"$match": {"source_country": {"$exists": True}, "crawled_at": {"$gte": week_start}}},
        {"$group": {"_id": "$source_country"}},
    ]
    countries_covered = len(await db.articles.aggregate(countries_pipeline).to_list(30))

    return {
        "streak": {
            "current": current_streak,
            "longest": longest_streak,
            "read_today": user.get("last_read_date", "") == today,
        },
        "stories_read": {
            "total": stories_read_total,
            "this_week": len(days_active_this_week),
            "this_month": len(days_active_this_month),
        },
        "reactions": {
            "total": total_reactions,
            "this_month": reactions_this_month,
            "most_used": most_used_reaction,
        },
        "favourite_category": favourite_category,
        "knowledge_score": {
            "score": knowledge_score,
            "rank_label": rank_label,
        },
        "countries_covered": countries_covered,
        "member_since": user.get("member_since", user.get("created_at", "")),
    }


@api_router.post("/knowledge-score/calculate-all")
async def calculate_all_knowledge_scores():
    """Batch calculate knowledge scores for all users. Designed for daily cron job."""
    today = today_str()
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1).isoformat()[:10]
    users = await db.users.find({}, {"_id": 0, "id": 1, "current_streak": 1,
                                      "stories_read_count": 1, "days_active": 1}).to_list(10000)
    updated = 0
    for u in users:
        user_id = u["id"]
        stories_read = u.get("stories_read_count", 0)
        streak = u.get("current_streak", 0)
        days_active = u.get("days_active", [])
        days_active_month = len([d for d in days_active if d >= month_start])
        total_reactions = await db.reactions.count_documents({"user_id": user_id})

        score = int((stories_read * 1) + (streak * 2) + (total_reactions * 0.5) + (days_active_month * 3))
        await db.users.update_one({"id": user_id}, {"$set": {"knowledge_score": score}})
        await db.knowledge_score_log.update_one(
            {"user_id": user_id, "calculated_at": today},
            {"$set": {"user_id": user_id, "score": score, "calculated_at": today,
                       "stories_read": stories_read, "streak_days": streak,
                       "reactions_given": total_reactions, "days_active": days_active_month}},
            upsert=True)
        updated += 1
    return {"updated": updated, "date": today}


@api_router.post("/articles/{article_id}/react")
async def toggle_reaction(article_id: str, body: ReactionRequest, user=Depends(get_current_user)):
    if body.reaction not in VALID_REACTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid reaction. Must be one of {VALID_REACTIONS}")

    existing = await db.reactions.find_one({"article_id": article_id, "user_id": user["id"]}, {"_id": 0})

    if existing and existing.get("reaction") == body.reaction:
        # Remove reaction (toggle off)
        await db.reactions.delete_one({"article_id": article_id, "user_id": user["id"]})
        await db.articles.update_one({"id": article_id},
            {"$inc": {f"reaction_counts.{body.reaction}": -1}})
        await db.users.update_one({"id": user["id"]}, {"$inc": {"reactions_given_count": -1}})
        return {"action": "removed", "reaction": body.reaction}
    else:
        # If had different reaction, decrement old
        if existing:
            old_reaction = existing["reaction"]
            await db.articles.update_one({"id": article_id},
                {"$inc": {f"reaction_counts.{old_reaction}": -1}})
        else:
            # Only increment if it's a new reaction (not changing)
            await db.users.update_one({"id": user["id"]}, {"$inc": {"reactions_given_count": 1}})

        # Set new reaction
        await db.reactions.update_one(
            {"article_id": article_id, "user_id": user["id"]},
            {"$set": {"article_id": article_id, "user_id": user["id"],
                       "reaction": body.reaction, "created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True)
        await db.articles.update_one({"id": article_id},
            {"$inc": {f"reaction_counts.{body.reaction}": 1}})
        return {"action": "added", "reaction": body.reaction}

@api_router.get("/articles/{article_id}/reactions")
async def get_article_reactions(article_id: str, user=Depends(get_optional_user)):
    article = await db.articles.find_one({"id": article_id}, {"_id": 0, "reaction_counts": 1})
    counts = article.get("reaction_counts", {}) if article else {}
    # Clean up negative counts
    counts = {k: max(0, v) for k, v in counts.items()}
    user_reaction = None
    if user:
        doc = await db.reactions.find_one({"article_id": article_id, "user_id": user["id"]}, {"_id": 0})
        user_reaction = doc.get("reaction") if doc else None
    return {"counts": counts, "user_reaction": user_reaction}


# ========== FRIENDS SYSTEM ==========
class FriendRequest(BaseModel):
    target_username: str


@api_router.post("/friends/request")
async def send_friend_request(body: FriendRequest, user=Depends(get_current_user)):
    """Send a friend request to another user by username."""
    target = await db.users.find_one({"username": body.target_username.lower().strip()}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself")

    # Check if under-14 target (can't be found via search, only invite link)
    if target.get("account_type") == "child":
        raise HTTPException(status_code=403, detail="This user can only be added via invite link")

    # Check existing friendship
    existing = await db.friendships.find_one({
        "$or": [
            {"user_id_1": user["id"], "user_id_2": target["id"]},
            {"user_id_1": target["id"], "user_id_2": user["id"]},
        ]
    }, {"_id": 0})

    if existing:
        if existing["status"] == "accepted":
            raise HTTPException(status_code=400, detail="Already friends")
        if existing["status"] == "pending":
            raise HTTPException(status_code=400, detail="Friend request already pending")
        if existing["status"] == "blocked":
            raise HTTPException(status_code=400, detail="Unable to send request")

    friendship_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.friendships.insert_one({
        "id": friendship_id,
        "user_id_1": user["id"],
        "user_id_2": target["id"],
        "status": "pending",
        "initiated_by": user["id"],
        "created_at": now,
        "accepted_at": None,
    })

    # Log notification for target
    await log_notification(target["id"], "friend_request",
                           f"{user.get('full_name', 'Someone')} wants to read The Drop with you.")

    return {"message": "Friend request sent", "friendship_id": friendship_id}


@api_router.post("/friends/accept/{friendship_id}")
async def accept_friend_request(friendship_id: str, user=Depends(get_current_user)):
    friendship = await db.friendships.find_one({"id": friendship_id}, {"_id": 0})
    if not friendship:
        raise HTTPException(status_code=404, detail="Request not found")
    if friendship["user_id_2"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your request to accept")
    if friendship["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already {friendship['status']}")

    now = datetime.now(timezone.utc).isoformat()
    await db.friendships.update_one({"id": friendship_id}, {"$set": {"status": "accepted", "accepted_at": now}})
    return {"message": "Friend request accepted"}


@api_router.post("/friends/decline/{friendship_id}")
async def decline_friend_request(friendship_id: str, user=Depends(get_current_user)):
    friendship = await db.friendships.find_one({"id": friendship_id}, {"_id": 0})
    if not friendship:
        raise HTTPException(status_code=404, detail="Request not found")
    if friendship["user_id_2"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your request to decline")
    await db.friendships.delete_one({"id": friendship_id})
    return {"message": "Friend request declined"}


@api_router.get("/friends")
async def get_friends(user=Depends(get_current_user)):
    """Get all accepted friends with their stats."""
    friendships = await db.friendships.find({
        "$or": [{"user_id_1": user["id"]}, {"user_id_2": user["id"]}],
        "status": "accepted",
    }, {"_id": 0}).to_list(100)

    friend_ids = []
    for f in friendships:
        friend_id = f["user_id_2"] if f["user_id_1"] == user["id"] else f["user_id_1"]
        friend_ids.append(friend_id)

    friends = []
    for fid in friend_ids:
        friend = await db.users.find_one({"id": fid}, {"_id": 0, "password_hash": 0})
        if friend:
            friends.append({
                "id": friend["id"],
                "full_name": friend.get("full_name", ""),
                "username": friend.get("username", ""),
                "avatar_url": friend.get("avatar_url", ""),
                "current_streak": friend.get("current_streak", 0),
                "knowledge_score": friend.get("knowledge_score", 0),
                "last_read_date": friend.get("last_read_date", ""),
            })

    # Sort by streak descending
    friends.sort(key=lambda x: x["current_streak"], reverse=True)
    return friends


@api_router.get("/friends/requests")
async def get_friend_requests(user=Depends(get_current_user)):
    """Get pending friend requests received by the current user."""
    requests = await db.friendships.find({
        "user_id_2": user["id"], "status": "pending"
    }, {"_id": 0}).to_list(50)

    result = []
    for r in requests:
        sender = await db.users.find_one({"id": r["user_id_1"]}, {"_id": 0, "password_hash": 0})
        if sender:
            result.append({
                "friendship_id": r["id"],
                "sender": {
                    "id": sender["id"],
                    "full_name": sender.get("full_name", ""),
                    "username": sender.get("username", ""),
                    "avatar_url": sender.get("avatar_url", ""),
                    "knowledge_score": sender.get("knowledge_score", 0),
                },
                "created_at": r["created_at"],
            })
    return result


@api_router.get("/friends/leaderboard")
async def get_friends_leaderboard(user=Depends(get_current_user)):
    """Get friends-only leaderboard ranked by knowledge score. Resets monthly."""
    friendships = await db.friendships.find({
        "$or": [{"user_id_1": user["id"]}, {"user_id_2": user["id"]}],
        "status": "accepted",
    }, {"_id": 0}).to_list(100)

    friend_ids = [user["id"]]  # Include self
    for f in friendships:
        friend_id = f["user_id_2"] if f["user_id_1"] == user["id"] else f["user_id_1"]
        friend_ids.append(friend_id)

    leaderboard = []
    for fid in friend_ids:
        u = await db.users.find_one({"id": fid}, {"_id": 0, "password_hash": 0})
        if u:
            score = u.get("knowledge_score", 0)
            if score >= 501: rank_label = "No Cap Legend"
            elif score >= 301: rank_label = "Sharp"
            elif score >= 151: rank_label = "Switched On"
            elif score >= 51: rank_label = "Informed"
            else: rank_label = "Curious"

            leaderboard.append({
                "id": u["id"],
                "full_name": u.get("full_name", ""),
                "username": u.get("username", ""),
                "avatar_url": u.get("avatar_url", ""),
                "knowledge_score": score,
                "current_streak": u.get("current_streak", 0),
                "rank_label": rank_label,
                "is_self": u["id"] == user["id"],
            })

    leaderboard.sort(key=lambda x: x["knowledge_score"], reverse=True)

    # Add rank numbers
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1

    # Get previous month's winner
    now = datetime.now(timezone.utc)
    prev_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1).isoformat()[:10]
    prev_month_end = now.replace(day=1).isoformat()[:10]
    prev_winner = None
    for fid in friend_ids:
        log = await db.knowledge_score_log.find_one(
            {"user_id": fid, "calculated_at": {"$gte": prev_month_start, "$lt": prev_month_end}},
            {"_id": 0},
            sort=[("score", -1)]
        )
        if log and (not prev_winner or log["score"] > prev_winner["score"]):
            winner_user = await db.users.find_one({"id": fid}, {"_id": 0, "password_hash": 0})
            if winner_user:
                prev_winner = {
                    "username": winner_user.get("username", ""),
                    "full_name": winner_user.get("full_name", ""),
                    "score": log["score"],
                }

    return {"leaderboard": leaderboard, "previous_month_winner": prev_winner}


@api_router.get("/friends/search")
async def search_friends(q: str, user=Depends(get_current_user)):
    """Search users by username. Under-14 accounts are not searchable."""
    clean = q.lower().strip().lstrip("@")
    if len(clean) < 2:
        return []
    results = await db.users.find({
        "username": {"$regex": f"^{re.escape(clean)}", "$options": "i"},
        "account_type": {"$ne": "child"},  # Under-14 not searchable
        "id": {"$ne": user["id"]},
    }, {"_id": 0, "password_hash": 0}).limit(10).to_list(10)

    return [{
        "id": r["id"],
        "full_name": r.get("full_name", ""),
        "username": r.get("username", ""),
        "avatar_url": r.get("avatar_url", ""),
        "knowledge_score": r.get("knowledge_score", 0),
    } for r in results]


@api_router.post("/friends/block/{target_user_id}")
async def block_user(target_user_id: str, user=Depends(get_current_user)):
    """Block a user. Removes friendship silently."""
    # Remove any existing friendship
    await db.friendships.delete_many({
        "$or": [
            {"user_id_1": user["id"], "user_id_2": target_user_id},
            {"user_id_1": target_user_id, "user_id_2": user["id"]},
        ]
    })
    # Create block record
    await db.friendships.insert_one({
        "id": str(uuid.uuid4()),
        "user_id_1": user["id"],
        "user_id_2": target_user_id,
        "status": "blocked",
        "initiated_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "accepted_at": None,
    })
    return {"message": "User blocked"}


# ========== INVITE LINKS ==========
@api_router.get("/invite/my-link")
async def get_my_invite_link(user=Depends(get_current_user)):
    """Get the current user's invite link."""
    username = user.get("username", "")
    invite_code = user.get("invite_code", "")
    return {
        "invite_url": f"/join/@{username}",
        "username": username,
        "invite_code": invite_code,
    }


@api_router.get("/invite/lookup/{username}")
async def lookup_invite(username: str):
    """Look up an inviting user's public profile for the invite landing page."""
    clean = username.lower().strip().lstrip("@")
    target = await db.users.find_one({"username": clean}, {"_id": 0, "password_hash": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    score = target.get("knowledge_score", 0)
    if score >= 501: rank = "No Cap Legend"
    elif score >= 301: rank = "Sharp"
    elif score >= 151: rank = "Switched On"
    elif score >= 51: rank = "Informed"
    else: rank = "Curious"

    # Track click
    await db.invite_links.update_one(
        {"owner_user_id": target["id"]},
        {"$inc": {"clicks": 1}, "$setOnInsert": {
            "id": str(uuid.uuid4()), "owner_user_id": target["id"],
            "invite_code": target.get("invite_code", ""), "signups": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    return {
        "id": target["id"],
        "full_name": target.get("full_name", ""),
        "username": target.get("username", ""),
        "avatar_url": target.get("avatar_url", ""),
        "knowledge_score": score,
        "rank_label": rank,
        "current_streak": target.get("current_streak", 0),
    }


@api_router.post("/invite/connect/{inviter_username}")
async def connect_via_invite(inviter_username: str, user=Depends(get_current_user)):
    """Auto-connect the current user with the inviter after signup via invite link."""
    clean = inviter_username.lower().strip().lstrip("@")
    inviter = await db.users.find_one({"username": clean}, {"_id": 0})
    if not inviter or inviter["id"] == user["id"]:
        return {"message": "Skipped"}

    # Check if already connected
    existing = await db.friendships.find_one({
        "$or": [
            {"user_id_1": user["id"], "user_id_2": inviter["id"]},
            {"user_id_1": inviter["id"], "user_id_2": user["id"]},
        ]
    })
    if existing:
        return {"message": "Already connected"}

    now = datetime.now(timezone.utc).isoformat()

    # If either user is a child account, need parent approval (mock notification)
    if user.get("account_type") == "child":
        parent_email = user.get("parent_email", "")
        mock_send_parent_email_friend_request(parent_email, user.get("full_name", ""), inviter.get("full_name", ""))
        # Still auto-connect for invite links (per spec: no friend request needed for invite-link signups)

    if inviter.get("account_type") == "child":
        parent_email = inviter.get("parent_email", "")
        mock_send_parent_email_friend_request(parent_email, inviter.get("full_name", ""), user.get("full_name", ""))

    await db.friendships.insert_one({
        "id": str(uuid.uuid4()),
        "user_id_1": inviter["id"],
        "user_id_2": user["id"],
        "status": "accepted",
        "initiated_by": inviter["id"],
        "created_at": now,
        "accepted_at": now,
    })

    # Track signup conversion
    await db.invite_links.update_one(
        {"owner_user_id": inviter["id"]},
        {"$inc": {"signups": 1}},
    )

    return {"message": "Connected as friends"}


# ========== NOTIFICATION ROUTES ==========
@api_router.get("/notifications/settings")
async def get_notification_settings(user=Depends(get_current_user)):
    prefs = user.get("notification_prefs", DEFAULT_NOTIFICATION_PREFS)
    return {
        "streak_reminders": prefs.get("streak_reminders", True),
        "milestone_alerts": prefs.get("milestone_alerts", True),
        "daily_news_alerts": prefs.get("daily_news_alerts", True),
        "has_device_token": bool(user.get("device_tokens")),
        "timezone": user.get("timezone", "UTC"),
    }

@api_router.put("/notifications/settings")
async def update_notification_settings(body: NotificationSettingsUpdate, user=Depends(get_current_user)):
    prefs = user.get("notification_prefs", DEFAULT_NOTIFICATION_PREFS.copy())
    if body.streak_reminders is not None:
        prefs["streak_reminders"] = body.streak_reminders
    if body.milestone_alerts is not None:
        prefs["milestone_alerts"] = body.milestone_alerts
    if body.daily_news_alerts is not None:
        prefs["daily_news_alerts"] = body.daily_news_alerts

    await db.users.update_one({"id": user["id"]}, {"$set": {"notification_prefs": prefs}})
    return prefs

@api_router.post("/notifications/register-device")
async def register_device(body: DeviceTokenRequest, user=Depends(get_current_user)):
    """Register a push notification token for the user's device."""
    tokens = user.get("device_tokens", [])
    # Remove duplicate, add new
    tokens = [t for t in tokens if t.get("token") != body.token]
    tokens.append({"token": body.token, "platform": body.platform, "registered_at": datetime.now(timezone.utc).isoformat()})
    await db.users.update_one({"id": user["id"]}, {"$set": {"device_tokens": tokens}})
    return {"message": "Device registered", "token_count": len(tokens)}

@api_router.post("/notifications/update-timezone")
async def update_timezone(tz: str, user=Depends(get_current_user)):
    await db.users.update_one({"id": user["id"]}, {"$set": {"timezone": tz}})
    return {"timezone": tz}

@api_router.get("/notifications/log")
async def get_notification_log(user=Depends(get_current_user), limit: int = 20):
    """Get recent notifications for the user."""
    logs = await db.notification_log.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    return logs

@api_router.get("/notifications/pending-milestone")
async def get_pending_milestone(user=Depends(get_current_user)):
    """Check if user has an unacknowledged milestone notification."""
    streak = user.get("current_streak", 0)
    for m in MILESTONES:
        if streak >= m:
            existing = await db.notification_log.find_one({
                "user_id": user["id"], "type": "milestone",
                "message": {"$regex": f"^{m}-day"},
            })
            if existing and not existing.get("acknowledged"):
                return {"milestone": m, "message": MILESTONE_MESSAGES[m]["text"],
                        "emoji": MILESTONE_MESSAGES[m]["emoji"], "notification_id": existing.get("id")}
    return None

@api_router.post("/notifications/acknowledge/{notification_id}")
async def acknowledge_notification(notification_id: str, user=Depends(get_current_user)):
    await db.notification_log.update_one(
        {"id": notification_id, "user_id": user["id"]},
        {"$set": {"acknowledged": True}})
    return {"acknowledged": True}

@api_router.post("/notifications/check-streaks")
async def check_streak_reminders():
    """Cron-callable endpoint: Check all users who haven't read today and queue reminders.
    Should be called around 6 PM. Rate limited to 2 notifications per user per day."""
    today = today_str()
    users_cursor = db.users.find(
        {"last_read_date": {"$ne": today},
         "notification_prefs.streak_reminders": True,
         "current_streak": {"$gt": 0}},
        {"_id": 0, "password_hash": 0}
    )
    users = await users_cursor.to_list(1000)

    sent = 0
    for u in users:
        # Rate limit: max 2 per day
        sent_today = await get_notifications_sent_today(u["id"])
        if sent_today >= 2:
            continue

        msg = await get_streak_reminder_message(u)
        await log_notification(u["id"], "streak_reminder", msg)
        sent += 1

    return {"checked": len(users), "reminders_queued": sent}


# ========== CORE ROUTES ==========
@api_router.get("/")
async def root():
    return {"message": "The Drop API - No Cap News"}

@api_router.get("/categories")
async def get_categories():
    return CATEGORIES

@api_router.get("/articles")
async def get_articles(category: Optional[str] = None, age_group: str = "14-16", limit: int = 20,
                       country_code: Optional[str] = None,
                       user=Depends(get_optional_user)):
    query = {}
    if category and category != "all":
        query["category"] = category
    # Filter by country if provided, otherwise use user's country
    effective_country = country_code
    if not effective_country and user:
        # Map user's country name to country_code
        user_country = user.get("country", "")
        if user_country:
            country_doc = await db.global_sources.find_one(
                {"country_name": {"$regex": f"^{user_country}$", "$options": "i"}},
                {"_id": 0, "country_code": 1}
            )
            if country_doc:
                effective_country = country_doc["country_code"]
    if effective_country:
        query["source_country"] = effective_country.upper()

    # Sort by engagement (reaction total) + recency
    cursor = db.articles.find(query, {"_id": 0, "original_content": 0}).sort("crawled_at", -1).limit(limit)
    articles = await cursor.to_list(limit)

    result = []
    for a in articles:
        rewrite = a.get("rewrites", {}).get(age_group)
        counts = a.get("reaction_counts", {})
        counts = {k: max(0, v) for k, v in counts.items()}
        why = generate_why_reason(a, user)
        logo = a.get("source_logo", "") or await get_source_logo(a.get("source", ""))
        result.append({
            "id": a["id"], "original_title": a["original_title"],
            "original_url": a.get("original_url", ""), "source": a.get("source", ""),
            "source_logo": logo,
            "source_country": a.get("source_country", ""),
            "source_language": a.get("source_language", "English"),
            "category": a.get("category", ""), "image_url": a.get("image_url", ""),
            "published_at": a.get("published_at", ""), "rewrite": rewrite,
            "reaction_counts": counts, "why_reason": why,
            "low_confidence_flag": a.get("low_confidence_flag", False),
        })

    # Sort by total reactions (engagement signal) then recency
    result.sort(key=lambda x: sum(x.get("reaction_counts", {}).values()), reverse=True)
    return result

@api_router.get("/articles/{article_id}")
async def get_article(article_id: str, age_group: str = "14-16", user=Depends(get_optional_user)):
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    rewrite = article.get("rewrites", {}).get(age_group)
    counts = article.get("reaction_counts", {})
    counts = {k: max(0, v) for k, v in counts.items()}
    why = generate_why_reason(article, user)
    logo = article.get("source_logo", "") or await get_source_logo(article.get("source", ""))
    return {
        "id": article["id"], "original_title": article["original_title"],
        "original_url": article.get("original_url", ""),
        "original_content": article.get("original_content", ""),
        "source": article.get("source", ""), "source_logo": logo,
        "source_country": article.get("source_country", ""),
        "source_language": article.get("source_language", "English"),
        "category": article.get("category", ""), "image_url": article.get("image_url", ""),
        "published_at": article.get("published_at", ""), "rewrite": rewrite,
        "reaction_counts": counts, "why_reason": why,
        "rewrite_status": article.get("rewrite_status", "pending"),
        "low_confidence_flag": article.get("low_confidence_flag", False),
        "safety_status": article.get("safety_status", "safe"),
    }


# ========== MICRO-FACTS ROUTES ==========
@api_router.get("/micro-facts")
async def get_micro_facts(age_group: str = "14-16"):
    today = today_str()
    facts = await db.micro_facts.find({"date": today, "age_group": age_group}, {"_id": 0}).to_list(10)
    if not facts:
        # Fallback: try any date
        facts = await db.micro_facts.find({"age_group": age_group}, {"_id": 0}).sort("date", -1).to_list(6)
    return facts

@api_router.post("/micro-facts/generate")
async def trigger_micro_facts(background_tasks: BackgroundTasks, age_group: str = "14-16"):
    background_tasks.add_task(generate_micro_facts, age_group)
    return {"message": f"Generating micro-facts for {age_group} in background"}


# ========== OTHER ROUTES ==========
@api_router.post("/crawl")
async def trigger_crawl(background_tasks: BackgroundTasks, age_group: str = "14-16",
                        country_code: str = None):
    async def crawl_and_rewrite():
        count = await crawl_rss_feeds(country_code=country_code)
        logger.info(f"Background crawl done: {count} articles for country={country_code or 'ALL'}")
        await rewrite_pending_articles(age_group)
        await generate_micro_facts(age_group)
    background_tasks.add_task(crawl_and_rewrite)
    return {"message": f"Crawl started for country={country_code or 'ALL'}. Processing in background."}

@api_router.post("/crawl/{country_code}")
async def trigger_country_crawl(country_code: str, background_tasks: BackgroundTasks,
                                 age_group: str = "14-16"):
    async def crawl_and_rewrite():
        count = await crawl_rss_feeds(country_code=country_code)
        logger.info(f"Background crawl done: {count} articles for {country_code}")
        await rewrite_pending_articles(age_group)
    background_tasks.add_task(crawl_and_rewrite)
    return {"message": f"Crawl started for {country_code}. Processing in background."}

@api_router.post("/rewrite")
async def trigger_rewrite(age_group: str = "14-16"):
    await rewrite_pending_articles(age_group)
    return {"message": f"Rewrites complete for age_group={age_group}"}

@api_router.get("/stats")
async def get_stats():
    total_articles = await db.articles.count_documents({})
    total_users = await db.users.count_documents({})
    categories_count = {}
    for cat in CATEGORIES:
        categories_count[cat["id"]] = await db.articles.count_documents({"category": cat["id"]})
    countries_count = await db.global_sources.count_documents({})
    return {"total_articles": total_articles, "total_users": total_users,
            "by_category": categories_count, "countries_configured": countries_count}


@api_router.get("/countries")
async def list_countries():
    """List all configured countries with their info for frontend selectors."""
    countries = await db.global_sources.find(
        {}, {"_id": 0, "country_code": 1, "country_name": 1, "flag_emoji": 1,
             "primary_language": 1, "city_tier_1": 1, "city_tier_2": 1}
    ).sort("country_name", 1).to_list(50)
    return countries


@api_router.get("/countries/{country_code}/sources")
async def get_country_sources(country_code: str):
    """Get all configured news sources for a specific country."""
    country = await db.global_sources.find_one(
        {"country_code": country_code.upper()}, {"_id": 0}
    )
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


# ========== SOURCE LOGOS ==========
@api_router.get("/source-logos")
async def get_source_logos():
    logos = await db.source_logos.find({}, {"_id": 0}).to_list(50)
    return logos

@api_router.put("/source-logos/{source_name}")
async def update_source_logo(source_name: str, logo_url: str = "", visible: bool = True):
    await db.source_logos.update_one(
        {"source": source_name},
        {"$set": {"logo_url": logo_url, "visible": visible}},
        upsert=True)
    return await db.source_logos.find_one({"source": source_name}, {"_id": 0})


# ========== SYSTEM PROMPTS ==========
@api_router.get("/system-prompts")
async def get_system_prompts():
    return await db.system_prompts.find({}, {"_id": 0}).to_list(20)

@api_router.get("/system-prompts/{prompt_id}")
async def get_system_prompt(prompt_id: str):
    doc = await db.system_prompts.find_one({"id": prompt_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return doc

@api_router.put("/system-prompts/{prompt_id}")
async def update_system_prompt(prompt_id: str, body: PromptUpdate):
    result = await db.system_prompts.update_one(
        {"id": prompt_id}, {"$set": {"prompt": body.prompt, "updated_at": datetime.now(timezone.utc).isoformat()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return await db.system_prompts.find_one({"id": prompt_id}, {"_id": 0})


# ========== STARTUP ==========
@app.on_event("startup")
async def startup_event():
    await seed_system_prompts()
    await seed_source_logos()
    await seed_global_sources()
    logger.info("System prompts, source logos & global sources seeded.")

    count = await db.articles.count_documents({})
    if count == 0:
        logger.info("No articles. Triggering initial crawl in background...")
        asyncio.create_task(_initial_crawl())
    else:
        # Generate micro-facts if none exist today
        today = today_str()
        facts_count = await db.micro_facts.count_documents({"date": today})
        if facts_count == 0:
            asyncio.create_task(generate_micro_facts("14-16"))


async def _initial_crawl():
    """Initial crawl on startup — runs in background to not block startup."""
    try:
        await crawl_rss_feeds(country_code="US")
        await crawl_rss_feeds(country_code="GB")
        await rewrite_pending_articles("14-16")
        await rewrite_pending_articles("8-10")
        await generate_micro_facts("8-10")
        await generate_micro_facts("14-16")
    except Exception as e:
        logger.error(f"Initial crawl failed: {e}")

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware, allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
