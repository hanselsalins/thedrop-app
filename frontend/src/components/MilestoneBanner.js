import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, X } from 'lucide-react';

export const MilestoneBanner = ({ milestone, onDismiss, isKids }) => {
  if (!milestone) return null;

  return (
    <AnimatePresence>
      <motion.div
        data-testid="milestone-banner"
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -100, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        className="fixed top-0 left-0 right-0 z-[100] px-4 pt-4"
        style={{ maxWidth: '430px', margin: '0 auto' }}
      >
        <div
          className="p-4 rounded-2xl flex items-start gap-3"
          style={{
            background: isKids
              ? 'linear-gradient(135deg, #FFD60A, #FF6B35)'
              : 'linear-gradient(135deg, #CCFF00, #7209B7)',
            boxShadow: '0 8px 40px rgba(0,0,0,0.3)',
          }}
        >
          <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: 'rgba(255,255,255,0.2)' }}>
            <Trophy size={24} color="#fff" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold tracking-wider uppercase opacity-80"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#fff' }}>
              MILESTONE REACHED
            </p>
            <p className="text-base font-bold mt-0.5 leading-snug"
              style={{ fontFamily: 'Syne, sans-serif', color: '#fff' }}>
              {milestone.emoji} {milestone.message}
            </p>
          </div>
          <button
            data-testid="milestone-dismiss"
            onClick={onDismiss}
            className="p-1 rounded-full shrink-0"
            style={{ background: 'rgba(255,255,255,0.2)' }}
          >
            <X size={16} color="#fff" />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
