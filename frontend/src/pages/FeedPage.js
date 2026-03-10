import { useState, useEffect, useCallback } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useNotifications } from '../hooks/useNotifications';
import { NewsCard } from '../components/NewsCard';
import { CategoryTabs } from '../components/CategoryTabs';
import { BottomNav } from '../components/BottomNav';
import { StreakBadge } from '../components/StreakBadge';
import { MicroFactCard } from '../components/MicroFactCard';
import { MilestoneBanner } from '../components/MilestoneBanner';
import { motion } from 'framer-motion';
import { Loader2, RefreshCw, Globe } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function FeedPage() {
  const { ageGroup, themeMode, user, token } = useTheme();
  const [articles, setArticles] = useState([]);
  const [categories, setCategories] = useState([]);
  const [microFacts, setMicroFacts] = useState([]);
  const [streak, setStreak] = useState({ current_streak: 0, longest_streak: 0, read_today: false });
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [countries, setCountries] = useState([]);

  const isKids = themeMode === 'kids';
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const { milestone, checkMilestone, acknowledgeMilestone, requestPermission, permission } = useNotifications();

  // Get the user's current country flag
  const userCountryObj = countries.find(c => c.country_name === user?.country);

  // Request notification permission on first load
  useEffect(() => {
    if (permission === 'default') {
      const t = setTimeout(() => requestPermission(), 3000);
      return () => clearTimeout(t);
    }
  }, [permission, requestPermission]);

  const fetchArticles = useCallback(async () => {
    try {
      const params = { age_group: ageGroup || '14-16', limit: 20 };
      if (activeCategory !== 'all') params.category = activeCategory;
      const res = await axios.get(`${BACKEND_URL}/api/articles`, { params, headers });
      setArticles(res.data);
    } catch (e) {
      console.error('Failed to fetch articles:', e);
    } finally {
      setLoading(false);
    }
  }, [ageGroup, activeCategory, token]);

  const fetchCategories = useCallback(async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/categories`);
      setCategories(res.data);
    } catch (e) {}
  }, []);

  const fetchMicroFacts = useCallback(async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/micro-facts`, { params: { age_group: ageGroup || '14-16' } });
      setMicroFacts(res.data);
    } catch (e) {}
  }, [ageGroup]);

  const fetchStreak = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${BACKEND_URL}/api/streak`, { headers });
      setStreak(res.data);
    } catch (e) {}
  }, [token]);

  const fetchCountries = useCallback(async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/countries`);
      setCountries(res.data);
    } catch (e) {}
  }, []);

  useEffect(() => { fetchCategories(); fetchCountries(); }, [fetchCategories, fetchCountries]);
  useEffect(() => { fetchStreak(); }, [fetchStreak]);
  useEffect(() => { fetchMicroFacts(); }, [fetchMicroFacts]);
  useEffect(() => { setLoading(true); fetchArticles(); }, [fetchArticles]);
  useEffect(() => { checkMilestone(); }, [checkMilestone]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await axios.post(`${BACKEND_URL}/api/crawl?age_group=${ageGroup || '14-16'}`);
      await new Promise(r => setTimeout(r, 3000));
      await fetchArticles();
      await fetchMicroFacts();
    } catch (e) {}
    setRefreshing(false);
  };

  // Interleave micro-facts every 3-4 articles
  const buildFeedItems = () => {
    const items = [];
    let factIdx = 0;
    articles.forEach((article, i) => {
      items.push({ type: 'article', data: article });
      if ((i + 1) % 3 === 0 && factIdx < microFacts.length) {
        items.push({ type: 'fact', data: microFacts[factIdx] });
        factIdx++;
      }
    });
    return items;
  };

  const feedItems = buildFeedItems();
  const bgColor = isKids ? '#F0F4F8' : '#000000';
  const textColor = isKids ? '#1A1A1A' : '#EDEDED';

  return (
    <div data-testid="feed-page" className="min-h-screen pb-24" style={{ background: bgColor }}>
      {/* Milestone Banner */}
      <MilestoneBanner
        milestone={milestone}
        onDismiss={() => acknowledgeMilestone(milestone?.notification_id)}
        isKids={isKids}
      />
      {/* Header */}
      <div
        className="sticky top-0 z-30 px-5 pt-6 pb-3"
        style={{
          background: isKids ? 'rgba(240,244,248,0.95)' : 'rgba(0,0,0,0.95)',
          backdropFilter: 'blur(20px)',
        }}
      >
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="flex items-center gap-3">
              <h1
                className="text-2xl font-bold tracking-tight"
                style={{ fontFamily: isKids ? 'Fredoka, sans-serif' : 'Syne, sans-serif', color: textColor }}
              >
                The Drop
              </h1>
              <StreakBadge
                currentStreak={streak.current_streak}
                longestStreak={streak.longest_streak}
                readToday={streak.read_today}
                isKids={isKids}
                variant="compact"
              />
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span
                className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold tracking-widest uppercase"
                style={{ fontFamily: 'JetBrains Mono, monospace', background: isKids ? '#FFD60A' : '#CCFF00', color: '#050505' }}
              >
                No Cap News
              </span>
              {user?.city && (
                <span className="text-xs opacity-40" style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}>
                  {userCountryObj?.flag_emoji && `${userCountryObj.flag_emoji} `}{user.city}, {user.country}
                </span>
              )}
            </div>
          </div>
          <button
            data-testid="refresh-btn"
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2.5 rounded-xl"
            style={{
              background: isKids ? '#fff' : 'rgba(255,255,255,0.08)',
              border: isKids ? '2px solid #1A1A1A' : '1px solid rgba(255,255,255,0.15)',
            }}
          >
            <RefreshCw size={18} className={refreshing ? 'animate-spin' : ''}
              style={{ color: isKids ? '#1A1A1A' : '#CCFF00' }} />
          </button>
        </div>

        <CategoryTabs categories={categories} activeCategory={activeCategory}
          setActiveCategory={setActiveCategory} isKids={isKids} />
      </div>

      {/* Feed */}
      <div className="px-4 pt-4 space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin" size={32} style={{ color: isKids ? '#3A86FF' : '#CCFF00' }} />
          </div>
        ) : feedItems.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20">
            <p className="text-lg opacity-60" style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}>
              No articles yet. Hit refresh to load fresh news!
            </p>
          </motion.div>
        ) : (
          feedItems.map((item, index) => (
            <motion.div
              key={item.type === 'article' ? item.data.id : `fact-${index}`}
              initial={{ y: 30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: Math.min(index * 0.04, 0.5), duration: 0.35 }}
            >
              {item.type === 'article' ? (
                <NewsCard article={item.data} isKids={isKids} ageGroup={ageGroup} />
              ) : (
                <MicroFactCard fact={item.data} isKids={isKids} />
              )}
            </motion.div>
          ))
        )}
      </div>

      <BottomNav isKids={isKids} active="home" />
    </div>
  );
}
