import { Flame, Trophy } from 'lucide-react';

export const StreakBadge = ({ currentStreak, longestStreak, readToday, isKids, variant = 'compact' }) => {
  if (variant === 'compact') {
    return (
      <div
        data-testid="streak-badge"
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
        style={{
          background: isKids ? 'rgba(255,107,53,0.1)' : 'rgba(255,107,53,0.08)',
          border: readToday
            ? (isKids ? '1.5px solid rgba(255,107,53,0.3)' : '1.5px solid rgba(255,107,53,0.2)')
            : '1px dashed rgba(255,107,53,0.2)',
        }}
      >
        <Flame size={14} style={{ color: '#FF6B35' }} />
        <span
          className="text-xs font-bold"
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            color: '#FF6B35',
          }}
        >
          {currentStreak > 0 ? `${currentStreak} day${currentStreak > 1 ? 's' : ''}` : 'Start!'}
        </span>
      </div>
    );
  }

  // Full variant for profile page
  return (
    <div
      data-testid="streak-badge-full"
      className="p-4 rounded-xl"
      style={{
        background: isKids ? '#fff' : '#121212',
        border: isKids ? 'none' : '1px solid rgba(255,255,255,0.06)',
        boxShadow: isKids ? '0 2px 12px rgba(0,0,0,0.05)' : 'none',
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(255,107,53,0.12)' }}
          >
            <Flame size={22} style={{ color: '#FF6B35' }} />
          </div>
          <div>
            <p className="text-[10px] font-bold tracking-wider uppercase opacity-50"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: isKids ? '#1A1A1A' : '#EDEDED' }}>
              READING STREAK
            </p>
            <p className="text-2xl font-bold" style={{ fontFamily: 'Syne, sans-serif', color: '#FF6B35' }}>
              {currentStreak} day{currentStreak !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg"
          style={{ background: 'rgba(255,214,10,0.1)' }}>
          <Trophy size={12} style={{ color: '#FFD60A' }} />
          <span className="text-[10px] font-bold"
            style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FFD60A' }}>
            Best: {longestStreak}
          </span>
        </div>
      </div>
      {!readToday && currentStreak > 0 && (
        <p className="text-xs mt-2 opacity-60"
          style={{ fontFamily: 'Outfit, sans-serif', color: isKids ? '#1A1A1A' : '#EDEDED' }}>
          Read a story today to keep your streak going!
        </p>
      )}
    </div>
  );
};
