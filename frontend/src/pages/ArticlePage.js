import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { BottomNav } from '../components/BottomNav';
import { ReactionBar } from '../components/ReactionBar';
import { motion } from 'framer-motion';
import { ArrowLeft, ExternalLink, Share2, Clock, Tag } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CATEGORY_LABELS = {
  world: "What's Happening",
  science: "Science & Discovery",
  money: "Money & Economy",
  history: "History in the Making",
  entertainment: "Entertainment",
  local: "In Your City",
};

export default function ArticlePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { ageGroup, themeMode, token } = useTheme();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);

  const isKids = themeMode === 'kids';
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/articles/${id}`, {
          params: { age_group: ageGroup || '14-16' }, headers,
        });
        setArticle(res.data);
      } catch (e) {
        console.error('Failed to fetch article:', e);
      }
      setLoading(false);
    };
    fetchArticle();
  }, [id, ageGroup]);

  // Record read for streak
  useEffect(() => {
    if (!token || !article) return;
    axios.post(`${BACKEND_URL}/api/streak/read`, {}, { headers }).catch(() => {});
  }, [article, token]);

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: article.rewrite?.title || article.original_title,
          url: window.location.href,
        });
      } catch (e) {}
    }
  };

  const bgColor = isKids ? '#F0F4F8' : '#000000';
  const textColor = isKids ? '#1A1A1A' : '#EDEDED';
  const subColor = isKids ? '#666' : '#888';

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: bgColor }}>
        <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
          style={{ borderColor: isKids ? '#3A86FF' : '#CCFF00', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: bgColor }}>
        <p style={{ color: textColor }}>Article not found.</p>
      </div>
    );
  }

  const rw = article.rewrite;
  const title = rw?.title || article.original_title;
  const body = rw?.body || article.original_content || '';
  const summary = rw?.summary || '';
  const readingTime = rw?.reading_time || '2 min';
  const wonderQuestion = rw?.wonder_question || '';

  return (
    <div data-testid="article-page" className="min-h-screen pb-24" style={{ background: bgColor }}>
      {/* Hero Image */}
      <div className="relative">
        <div className="aspect-video w-full overflow-hidden">
          <img src={article.image_url} alt={title} className="w-full h-full object-cover"
            onError={(e) => { e.target.style.background = isKids ? '#FFD60A' : '#121212'; e.target.src = ''; }} />
        </div>
        <div className="absolute inset-0" style={{
          background: isKids
            ? 'linear-gradient(to top, rgba(240,244,248,1) 0%, transparent 60%)'
            : 'linear-gradient(to top, #000 0%, transparent 60%)',
        }} />
        <button data-testid="back-btn" onClick={() => navigate(-1)}
          className="absolute top-4 left-4 p-2 rounded-full z-10"
          style={{ background: isKids ? 'rgba(255,255,255,0.9)' : 'rgba(0,0,0,0.6)', backdropFilter: 'blur(10px)' }}>
          <ArrowLeft size={20} style={{ color: isKids ? '#1A1A1A' : '#FAFAFA' }} />
        </button>
        <button data-testid="share-btn" onClick={handleShare}
          className="absolute top-4 right-4 p-2 rounded-full z-10"
          style={{ background: isKids ? 'rgba(255,255,255,0.9)' : 'rgba(0,0,0,0.6)', backdropFilter: 'blur(10px)' }}>
          <Share2 size={20} style={{ color: isKids ? '#1A1A1A' : '#FAFAFA' }} />
        </button>
      </div>

      {/* Content */}
      <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.4 }}
        className="px-5 -mt-8 relative z-10">

        {/* Category Badge */}
        <span className="inline-block px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase mb-3"
          style={{ fontFamily: 'JetBrains Mono, monospace', background: isKids ? '#3A86FF' : '#CCFF00', color: isKids ? '#fff' : '#050505' }}>
          {CATEGORY_LABELS[article.category] || article.category}
        </span>

        {/* Title */}
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight leading-tight mb-3"
          style={{ fontFamily: isKids ? 'Fredoka, sans-serif' : 'Syne, sans-serif', color: textColor }}>
          {title}
        </h1>

        {/* Meta with Source Logo */}
        <div className="flex items-center gap-3 mb-5" style={{ color: subColor }}>
          {article.source_logo && (
            <img src={article.source_logo} alt={article.source}
              className="w-5 h-5 rounded object-contain"
              onError={(e) => { e.target.style.display = 'none'; }} />
          )}
          <div className="flex items-center gap-1.5 text-sm" style={{ fontFamily: 'Outfit, sans-serif' }}>
            <Tag size={14} />
            <span>{article.source}</span>
          </div>
          <div className="flex items-center gap-1.5 text-sm" style={{ fontFamily: 'Outfit, sans-serif' }}>
            <Clock size={14} />
            <span>{readingTime} read</span>
          </div>
        </div>

        {/* Summary */}
        {summary && (
          <div className="p-4 rounded-xl mb-6" style={{
            background: isKids ? 'rgba(58,134,255,0.08)' : 'rgba(204,255,0,0.06)',
            border: isKids ? '1px solid rgba(58,134,255,0.2)' : '1px solid rgba(204,255,0,0.15)',
          }}>
            <p className="text-base font-medium leading-relaxed"
              style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}>
              {summary}
            </p>
          </div>
        )}

        {/* Body */}
        <div className="text-base leading-relaxed space-y-4"
          style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}>
          {body.split('\n').filter(Boolean).map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>

        {/* Wonder Question */}
        {wonderQuestion && (
          <div data-testid="wonder-question" className="mt-6 p-4 rounded-xl" style={{
            background: isKids ? 'rgba(255,214,10,0.12)' : 'rgba(204,255,0,0.06)',
            border: isKids ? '1px solid rgba(255,214,10,0.3)' : '1px solid rgba(204,255,0,0.15)',
          }}>
            <p className="text-xs font-bold tracking-wider uppercase mb-2 opacity-60"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: isKids ? '#FF6B35' : '#CCFF00' }}>
              Wonder Question
            </p>
            <p className="text-base font-medium leading-relaxed italic"
              style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}>
              {wonderQuestion}
            </p>
          </div>
        )}

        {/* Reaction Bar */}
        <ReactionBar articleId={article.id} />

        {/* Source Link */}
        <a data-testid="source-link" href={article.original_url} target="_blank" rel="noopener noreferrer"
          className="inline-flex items-center gap-2 mt-6 mb-4 px-4 py-2.5 rounded-xl text-sm font-medium"
          style={{
            fontFamily: 'Outfit, sans-serif',
            background: isKids ? '#fff' : 'rgba(255,255,255,0.06)',
            border: isKids ? '2px solid #1A1A1A' : '1px solid rgba(255,255,255,0.15)',
            color: textColor,
          }}>
          <ExternalLink size={16} />
          Read the original article at {article.source} &rarr;
        </a>
      </motion.div>

      <BottomNav isKids={isKids} active="home" />
    </div>
  );
}
