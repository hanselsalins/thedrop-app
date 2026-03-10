import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Flame, ArrowRight, Zap } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const RANK_COLORS = {
  'Curious': '#888', 'Informed': '#3A86FF', 'Switched On': '#CCFF00',
  'Sharp': '#FF006E', 'No Cap Legend': '#FFD60A',
};

export default function InvitePage() {
  const { username } = useParams();
  const navigate = useNavigate();
  const [inviter, setInviter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const clean = (username || '').replace('@', '');
    if (!clean) { setError('Invalid invite link'); setLoading(false); return; }
    axios.get(`${BACKEND_URL}/api/invite/lookup/${clean}`)
      .then(r => setInviter(r.data))
      .catch(() => setError('User not found'))
      .finally(() => setLoading(false));
  }, [username]);

  const handleSignup = () => {
    // Pass inviter username via state so AuthPage can auto-connect after signup
    const clean = (username || '').replace('@', '');
    navigate('/auth', { state: { invitedBy: clean } });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#050505' }}>
        <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: '#CCFF00', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  if (error || !inviter) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6" style={{ background: '#050505' }}>
        <p className="text-lg mb-4" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>{error || 'Something went wrong'}</p>
        <button onClick={() => navigate('/auth')} className="px-6 py-3 rounded-2xl font-bold"
          style={{ fontFamily: 'Syne, sans-serif', background: '#CCFF00', color: '#050505' }}>
          Go to Sign Up
        </button>
      </div>
    );
  }

  return (
    <div data-testid="invite-page" className="min-h-screen flex flex-col relative overflow-hidden" style={{ background: '#050505' }}>
      {/* Background accents */}
      <div className="absolute top-20 right-0 w-72 h-72 rounded-full opacity-8 blur-3xl" style={{ background: '#CCFF00' }} />
      <div className="absolute bottom-20 left-0 w-60 h-60 rounded-full opacity-6 blur-3xl" style={{ background: '#7209B7' }} />

      <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 text-center">
        {/* Logo */}
        <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}>
          <span className="text-xs font-bold tracking-[0.3em] uppercase" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#CCFF00' }}>
            THE DROP
          </span>
          <p className="text-[10px] opacity-30 mt-0.5" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>
            No Cap News
          </p>
        </motion.div>

        {/* Inviter avatar + info */}
        <motion.div initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.2, type: 'spring' }}
          className="mt-10 mb-6">
          <div className="w-28 h-28 rounded-full overflow-hidden mx-auto border-4" style={{ borderColor: '#CCFF00' }}>
            <img src={inviter.avatar_url} alt={inviter.full_name} className="w-full h-full object-cover" data-testid="inviter-avatar" />
          </div>
        </motion.div>

        <motion.h1 initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}
          className="text-2xl sm:text-3xl font-bold mb-2" style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}>
          {inviter.full_name} reads the news on The Drop.
        </motion.h1>
        <motion.p initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.35 }}
          className="text-lg mb-6 opacity-60" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>
          Join them.
        </motion.p>

        {/* Stats chips */}
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4 }}
          className="flex items-center gap-3 mb-10">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
            style={{ background: 'rgba(255,107,53,0.1)', border: '1px solid rgba(255,107,53,0.2)' }}>
            <Flame size={14} color="#FF6B35" fill="#FF6B35" />
            <span className="text-xs font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FF6B35' }}>
              {inviter.current_streak} day streak
            </span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
            style={{ background: `${RANK_COLORS[inviter.rank_label] || '#CCFF00'}15`, border: `1px solid ${RANK_COLORS[inviter.rank_label] || '#CCFF00'}30` }}>
            <Zap size={14} color={RANK_COLORS[inviter.rank_label] || '#CCFF00'} />
            <span className="text-xs font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: RANK_COLORS[inviter.rank_label] || '#CCFF00' }}>
              {inviter.knowledge_score} pts · {inviter.rank_label}
            </span>
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.5 }}
          className="w-full max-w-sm">
          <button data-testid="invite-signup-btn" onClick={handleSignup}
            className="w-full py-4 rounded-2xl text-base font-bold flex items-center justify-center gap-2 transition-all hover:scale-[1.02]"
            style={{ fontFamily: 'Syne, sans-serif', background: '#CCFF00', color: '#050505' }}>
            Sign up free <ArrowRight size={18} />
          </button>
        </motion.div>
      </div>
    </div>
  );
}
