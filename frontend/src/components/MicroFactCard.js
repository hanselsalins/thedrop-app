import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

export const MicroFactCard = ({ fact, isKids }) => {
  const textColor = isKids ? '#1A1A1A' : '#EDEDED';

  return (
    <motion.div
      data-testid="micro-fact-card"
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      className="p-5 rounded-2xl"
      style={{
        background: isKids
          ? 'linear-gradient(135deg, rgba(255,214,10,0.15), rgba(255,106,0,0.08))'
          : 'linear-gradient(135deg, rgba(204,255,0,0.08), rgba(114,9,183,0.06))',
        border: isKids
          ? '1.5px solid rgba(255,214,10,0.3)'
          : '1.5px solid rgba(204,255,0,0.12)',
      }}
    >
      <div className="flex items-center gap-2 mb-2.5">
        <div
          className="p-1.5 rounded-lg"
          style={{
            background: isKids ? 'rgba(255,214,10,0.25)' : 'rgba(204,255,0,0.12)',
          }}
        >
          <Sparkles size={14} style={{ color: isKids ? '#FF6B35' : '#CCFF00' }} />
        </div>
        <span
          className="text-[10px] font-bold tracking-widest uppercase"
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            color: isKids ? '#FF6B35' : '#CCFF00',
          }}
        >
          Did You Know?
        </span>
      </div>
      <p
        className="text-sm leading-relaxed font-medium"
        style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}
      >
        {fact.fact}
      </p>
    </motion.div>
  );
};
