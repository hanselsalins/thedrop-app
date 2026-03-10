import { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { motion } from 'framer-motion';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const REACTIONS = [
  { id: 'mind_blown', emoji: '🤯', label: 'Mind blown' },
  { id: 'surprising', emoji: '😮', label: 'Surprising' },
  { id: 'angry', emoji: '😡', label: 'Angry' },
  { id: 'sad', emoji: '😢', label: 'Sad' },
  { id: 'inspiring', emoji: '💪', label: 'Inspiring' },
];

export const ReactionBar = ({ articleId }) => {
  const { token, themeMode } = useTheme();
  const isKids = themeMode === 'kids';
  const [counts, setCounts] = useState({});
  const [userReaction, setUserReaction] = useState(null);
  const [animating, setAnimating] = useState(null);

  useEffect(() => {
    const fetchReactions = async () => {
      try {
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const res = await axios.get(`${BACKEND_URL}/api/articles/${articleId}/reactions`, { headers });
        setCounts(res.data.counts || {});
        setUserReaction(res.data.user_reaction);
      } catch (e) {
        console.error('Failed to fetch reactions:', e);
      }
    };
    fetchReactions();
  }, [articleId, token]);

  const handleReact = async (reactionId) => {
    if (!token) return;
    setAnimating(reactionId);

    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/react`,
        { reaction: reactionId },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (res.data.action === 'removed') {
        setCounts(prev => ({ ...prev, [reactionId]: Math.max(0, (prev[reactionId] || 0) - 1) }));
        setUserReaction(null);
      } else {
        // If switching from another reaction
        if (userReaction && userReaction !== reactionId) {
          setCounts(prev => ({
            ...prev,
            [userReaction]: Math.max(0, (prev[userReaction] || 0) - 1),
            [reactionId]: (prev[reactionId] || 0) + 1,
          }));
        } else {
          setCounts(prev => ({ ...prev, [reactionId]: (prev[reactionId] || 0) + 1 }));
        }
        setUserReaction(reactionId);
      }
    } catch (e) {
      console.error('React failed:', e);
    }
    setTimeout(() => setAnimating(null), 300);
  };

  const textColor = isKids ? '#1A1A1A' : '#EDEDED';

  return (
    <div
      data-testid="reaction-bar"
      className="mt-6 p-4 rounded-xl"
      style={{
        background: isKids ? '#fff' : '#121212',
        border: isKids ? '1px solid #eee' : '1px solid rgba(255,255,255,0.08)',
      }}
    >
      <p className="text-[10px] font-bold tracking-wider uppercase mb-3 opacity-50"
        style={{ fontFamily: 'JetBrains Mono, monospace', color: textColor }}>
        HOW DID THIS MAKE YOU FEEL?
      </p>
      <div className="flex items-center justify-between">
        {REACTIONS.map((r) => {
          const isActive = userReaction === r.id;
          const count = counts[r.id] || 0;
          return (
            <button
              key={r.id}
              data-testid={`reaction-${r.id}`}
              onClick={() => handleReact(r.id)}
              className="flex flex-col items-center gap-1 px-1"
            >
              <motion.span
                className="text-2xl"
                animate={animating === r.id ? { scale: [1, 1.4, 1] } : {}}
                transition={{ duration: 0.3 }}
                style={{
                  filter: isActive ? 'none' : 'grayscale(0.5)',
                  opacity: isActive ? 1 : 0.6,
                }}
              >
                {r.emoji}
              </motion.span>
              <span
                className="text-[10px] font-bold"
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  color: isActive ? (isKids ? '#FF006E' : '#CCFF00') : (isKids ? '#999' : '#555'),
                }}
              >
                {count > 0 ? count : ''}
              </span>
              <span
                className="text-[8px] opacity-50"
                style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}
              >
                {r.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
