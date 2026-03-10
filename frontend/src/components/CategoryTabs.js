export const CategoryTabs = ({ categories, activeCategory, setActiveCategory, isKids }) => {
  const allCategories = [{ id: 'all', name: 'For You', color: isKids ? '#FF006E' : '#CCFF00' }, ...categories];

  return (
    <div className="w-full overflow-x-auto scrollbar-hide" style={{ WebkitOverflowScrolling: 'touch' }}>
      <div className="flex gap-2 pb-1 min-w-max pr-4">
        {allCategories.map((cat) => {
          const isActive = activeCategory === cat.id;
          return (
            <button
              key={cat.id}
              data-testid={`category-tab-${cat.id}`}
              onClick={() => setActiveCategory(cat.id)}
              className="shrink-0 px-4 py-2 text-xs font-bold tracking-wider uppercase whitespace-nowrap"
              style={{
                fontFamily: 'JetBrains Mono, monospace',
                borderRadius: isKids ? '999px' : '10px',
                background: isActive
                  ? (cat.color || (isKids ? '#3A86FF' : '#CCFF00'))
                  : (isKids ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.06)'),
                color: isActive
                  ? (['#FFD60A', '#39FF14', '#CCFF00'].includes(cat.color) ? '#050505' : '#fff')
                  : (isKids ? '#666' : '#888'),
                border: isActive ? 'none' : (isKids ? '1px solid #ddd' : '1px solid rgba(255,255,255,0.1)'),
              }}
            >
              {cat.name}
            </button>
          );
        })}
      </div>
    </div>
  );
};
