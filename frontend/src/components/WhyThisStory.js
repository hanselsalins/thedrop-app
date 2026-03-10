import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, X } from 'lucide-react';

export const WhyThisStory = ({ reason, isKids }) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        data-testid="why-this-story-btn"
        onClick={(e) => { e.stopPropagation(); setOpen(!open); }}
        className="p-1 rounded-full"
        style={{
          background: isKids ? 'rgba(58,134,255,0.1)' : 'rgba(255,255,255,0.06)',
        }}
      >
        <Info size={13} style={{ color: isKids ? '#3A86FF' : '#888' }} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 5 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 5 }}
            transition={{ duration: 0.15 }}
            onClick={(e) => e.stopPropagation()}
            className="absolute bottom-full left-0 mb-2 p-3 rounded-xl z-50 w-60"
            style={{
              background: isKids ? '#fff' : '#1a1a1a',
              border: isKids ? '1px solid #eee' : '1px solid rgba(255,255,255,0.12)',
              boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
            }}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-[10px] font-bold tracking-wider uppercase mb-1 opacity-50"
                  style={{ fontFamily: 'JetBrains Mono, monospace', color: isKids ? '#1A1A1A' : '#EDEDED' }}>
                  WHY THIS STORY?
                </p>
                <p className="text-xs leading-relaxed"
                  style={{ fontFamily: 'Outfit, sans-serif', color: isKids ? '#444' : '#bbb' }}>
                  {reason}
                </p>
              </div>
              <button onClick={(e) => { e.stopPropagation(); setOpen(false); }} className="shrink-0 mt-0.5">
                <X size={12} style={{ color: isKids ? '#999' : '#666' }} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
