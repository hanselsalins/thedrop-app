import { useNavigate } from 'react-router-dom';
import { Clock, ArrowUpRight, Share2 } from 'lucide-react';
import { WhyThisStory } from './WhyThisStory';
import { ReactionMini } from './ReactionMini';

const CATEGORY_COLORS = {
  world: '#3A86FF',
  science: '#39FF14',
  money: '#FFD60A',
  history: '#FF6B35',
  entertainment: '#FF006E',
  local: '#4CC9F0',
};

const CATEGORY_LABELS = {
  world: "World",
  science: "Science",
  money: "Money",
  history: "History",
  entertainment: "Entertainment",
  local: "Local",
};

export const NewsCard = ({ article, isKids }) => {
  const navigate = useNavigate();
  const rw = article.rewrite;
  const title = rw?.title || article.original_title;
  const summary = rw?.summary || '';
  const readingTime = rw?.reading_time || '2 min';
  const catColor = CATEGORY_COLORS[article.category] || '#888';

  const cardBg = isKids ? '#FFFFFF' : '#121212';
  const textColor = isKids ? '#1A1A1A' : '#EDEDED';
  const subColor = isKids ? '#666' : '#888';

  return (
    <div
      data-testid={`news-card-${article.id}`}
      onClick={() => navigate(`/article/${article.id}`)}
      role="button"
      tabIndex={0}
      className="w-full text-left overflow-hidden cursor-pointer"
      style={{
        borderRadius: isKids ? '24px' : '16px',
        background: cardBg,
        border: isKids ? 'none' : '1px solid rgba(255,255,255,0.06)',
        boxShadow: isKids ? '0 4px 24px rgba(0,0,0,0.06)' : 'none',
      }}
    >
      {/* Image */}
      <div className="relative aspect-video overflow-hidden">
        <img
          src={article.image_url}
          alt={title}
          className="w-full h-full object-cover"
          loading="lazy"
          onError={(e) => { e.target.style.background = catColor + '22'; e.target.src = ''; }}
        />
        <div
          className="absolute inset-0"
          style={{
            background: isKids
              ? 'linear-gradient(to top, rgba(255,255,255,0.9) 0%, transparent 50%)'
              : 'linear-gradient(to top, #121212 0%, transparent 50%)',
          }}
        />
        <span
          className="absolute top-3 left-3 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase"
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            background: catColor,
            color: ['#FFD60A', '#39FF14', '#CCFF00'].includes(catColor) ? '#050505' : '#fff',
          }}
        >
          {CATEGORY_LABELS[article.category] || article.category}
        </span>
      </div>

      {/* Content */}
      <div className="p-4 -mt-6 relative z-10">
        <h3
          className="font-bold leading-snug mb-1.5"
          style={{
            fontFamily: isKids ? 'Fredoka, sans-serif' : 'Syne, sans-serif',
            color: textColor,
            fontSize: isKids ? '1.15rem' : '1.05rem',
          }}
        >
          {title}
        </h3>
        {summary && (
          <p className="text-sm leading-relaxed mb-3 line-clamp-2"
            style={{ fontFamily: 'Outfit, sans-serif', color: subColor }}>
            {summary}
          </p>
        )}

        {/* Source Row with Logo */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            {article.source_logo && (
              <img
                src={article.source_logo}
                alt={article.source}
                className="w-4 h-4 rounded object-contain"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            )}
            <span className="text-xs opacity-60" style={{ fontFamily: 'Outfit, sans-serif', color: textColor }}>
              {article.source}
            </span>
            {article.source_language && article.source_language !== 'English' && (
              <span className="text-[9px] px-1.5 py-0.5 rounded-full opacity-50 font-medium"
                style={{ fontFamily: 'JetBrains Mono, monospace', background: isKids ? '#eee' : 'rgba(255,255,255,0.08)', color: textColor }}>
                {article.source_language}
              </span>
            )}
            <div className="flex items-center gap-1 text-xs opacity-50" style={{ color: textColor }}>
              <Clock size={12} />
              <span style={{ fontFamily: 'Outfit, sans-serif' }}>{readingTime}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ReactionMini counts={article.reaction_counts} isKids={isKids} />
            <WhyThisStory reason={article.why_reason} isKids={isKids} />
            <button
              data-testid={`share-btn-${article.id}`}
              onClick={(e) => {
                e.stopPropagation();
                const shareUrl = `${window.location.origin}/article/${article.id}`;
                const shareText = `${rw?.title || article.original_title}\n\nRead on The Drop — No Cap News.\n${shareUrl}`;
                if (navigator.share) {
                  navigator.share({ title: rw?.title || article.original_title, text: shareText, url: shareUrl }).catch(() => {});
                } else {
                  navigator.clipboard.writeText(shareText).catch(() => {});
                }
              }}
              className="p-1.5 rounded-full"
              style={{ background: isKids ? 'rgba(58,134,255,0.08)' : 'rgba(255,255,255,0.06)' }}>
              <Share2 size={13} style={{ color: isKids ? '#3A86FF' : '#888' }} />
            </button>
            <div className="p-1.5 rounded-full"
              style={{ background: isKids ? catColor + '15' : 'rgba(204,255,0,0.08)' }}>
              <ArrowUpRight size={14} style={{ color: isKids ? catColor : '#CCFF00' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
