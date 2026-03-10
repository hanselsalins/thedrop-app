import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { motion } from 'framer-motion';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const groupStyles = {
  '8-10': {
    bg: 'linear-gradient(135deg, #FFD60A 0%, #FF006E 100%)',
    label: 'Kid Mode',
    sub: 'Ages 8-10',
    desc: 'Big pictures, simple words, lots of fun!',
    icon: '🎮',
  },
  '11-13': {
    bg: 'linear-gradient(135deg, #3A86FF 0%, #8338EC 100%)',
    label: 'Tween Mode',
    sub: 'Ages 11-13',
    desc: 'Real talk, cool comparisons, easy to get.',
    icon: '🎯',
  },
  '14-16': {
    bg: 'linear-gradient(135deg, #7209B7 0%, #CCFF00 100%)',
    label: 'Teen Mode',
    sub: 'Ages 14-16',
    desc: 'No cap, just facts with the right vibe.',
    icon: '🔥',
  },
  '17-20': {
    bg: 'linear-gradient(135deg, #050505 0%, #333 100%)',
    label: 'Young Adult',
    sub: 'Ages 17-20',
    desc: 'Deep dives, real context, think critically.',
    icon: '💫',
    border: '1px solid rgba(204, 255, 0, 0.3)',
  },
};

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { setAgeGroup, setUserId, setHasOnboarded } = useTheme();
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSelect = async (groupId) => {
    setSelected(groupId);
    setLoading(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/users`, { age_group: groupId });
      setUserId(res.data.id);
      setAgeGroup(groupId);
      setHasOnboarded(true);
      setTimeout(() => navigate('/feed'), 600);
    } catch (e) {
      console.error('Failed to create user:', e);
      setAgeGroup(groupId);
      setHasOnboarded(true);
      setTimeout(() => navigate('/feed'), 600);
    }
    setLoading(false);
  };

  return (
    <div
      data-testid="onboarding-page"
      className="min-h-screen flex flex-col px-5 py-8"
      style={{ background: '#050505' }}
    >
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <h1
          className="text-4xl md:text-5xl font-bold tracking-tight"
          style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}
        >
          Pick your vibe
        </h1>
        <p
          className="mt-2 text-base opacity-60"
          style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}
        >
          We'll serve your news the way you like it.
        </p>
      </motion.div>

      <div className="flex flex-col gap-4 flex-1">
        {Object.entries(groupStyles).map(([id, style], index) => (
          <motion.button
            key={id}
            data-testid={`age-group-${id}`}
            initial={{ x: -40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: index * 0.1, duration: 0.4 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => handleSelect(id)}
            disabled={loading}
            className="relative rounded-2xl p-5 text-left overflow-hidden"
            style={{
              background: style.bg,
              border: style.border || 'none',
              opacity: loading && selected !== id ? 0.4 : 1,
            }}
          >
            {selected === id && (
              <motion.div
                layoutId="selector"
                className="absolute inset-0 rounded-2xl"
                style={{ border: '3px solid #CCFF00' }}
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
            <div className="flex items-center justify-between relative z-10">
              <div>
                <span
                  className="text-xs font-bold tracking-widest uppercase opacity-80"
                  style={{ fontFamily: 'JetBrains Mono, monospace', color: id === '17-20' ? '#CCFF00' : '#fff' }}
                >
                  {style.sub}
                </span>
                <h3
                  className="text-2xl font-bold mt-1"
                  style={{ fontFamily: 'Syne, sans-serif', color: id === '17-20' ? '#FAFAFA' : '#fff' }}
                >
                  {style.label}
                </h3>
                <p
                  className="text-sm mt-1 opacity-80"
                  style={{ fontFamily: 'Outfit, sans-serif', color: id === '17-20' ? '#ccc' : '#fff' }}
                >
                  {style.desc}
                </p>
              </div>
              <span className="text-4xl">{style.icon}</span>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
