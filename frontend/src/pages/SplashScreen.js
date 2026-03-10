import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';

export default function SplashScreen() {
  const navigate = useNavigate();
  const { isAuthenticated } = useTheme();
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 400);
    const t2 = setTimeout(() => setPhase(2), 1200);
    const t3 = setTimeout(() => {
      if (isAuthenticated) {
        navigate('/feed');
      } else {
        navigate('/auth');
      }
    }, 2800);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [navigate, isAuthenticated]);

  return (
    <div
      data-testid="splash-screen"
      className="fixed inset-0 flex flex-col items-center justify-center overflow-hidden"
      style={{ background: '#050505' }}
    >
      <div className="absolute inset-0 opacity-10" style={{
        backgroundImage: `radial-gradient(circle at 30% 50%, #CCFF00 0%, transparent 50%), radial-gradient(circle at 70% 30%, #7000FF 0%, transparent 50%)`
      }} />

      <AnimatePresence>
        {phase >= 0 && (
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="relative z-10 text-center"
          >
            <h1
              className="font-bold tracking-tight"
              style={{
                fontFamily: 'Syne, sans-serif',
                fontSize: 'clamp(3rem, 12vw, 5rem)',
                color: '#FAFAFA',
                lineHeight: 0.95,
              }}
            >
              The Drop
            </h1>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {phase >= 1 && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="relative z-10 mt-4"
          >
            <span
              className="inline-block px-4 py-1.5 rounded-full text-sm font-bold tracking-widest uppercase"
              style={{
                fontFamily: 'JetBrains Mono, monospace',
                background: '#CCFF00',
                color: '#050505',
              }}
            >
              No Cap News
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {phase >= 2 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            transition={{ duration: 0.5 }}
            className="relative z-10 mt-6 text-sm"
            style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}
          >
            Real news. No filter. No fluff.
          </motion.p>
        )}
      </AnimatePresence>

      <motion.div
        className="absolute bottom-12 left-1/2 -translate-x-1/2"
        animate={{ opacity: [0.3, 1, 0.3] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        <div className="w-6 h-6 rounded-full" style={{ background: '#CCFF00' }} />
      </motion.div>
    </div>
  );
}
