import { useNavigate } from 'react-router-dom';
import { Home, Search, User } from 'lucide-react';

export const BottomNav = ({ isKids, active = 'home' }) => {
  const navigate = useNavigate();

  const items = [
    { id: 'home', icon: Home, label: 'Home', path: '/feed' },
    { id: 'search', icon: Search, label: 'Search', path: '/feed' },
    { id: 'profile', icon: User, label: 'Profile', path: '/profile' },
  ];

  const bgColor = isKids ? 'rgba(255,255,255,0.95)' : 'rgba(18,18,18,0.95)';
  const activeColor = isKids ? '#FF006E' : '#CCFF00';
  const inactiveColor = isKids ? '#aaa' : '#555';

  return (
    <nav
      data-testid="bottom-nav"
      className="fixed bottom-0 left-0 right-0 z-50 px-6 pb-6 pt-2"
      style={{
        background: bgColor,
        backdropFilter: 'blur(20px)',
        borderTop: isKids ? '1px solid #eee' : '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div className="max-w-md mx-auto flex items-center justify-around">
        {items.map(({ id, icon: Icon, label, path }) => (
          <button
            key={id}
            data-testid={`nav-${id}`}
            onClick={() => navigate(path)}
            className="flex flex-col items-center gap-1 py-1 px-4"
          >
            <Icon
              size={22}
              strokeWidth={active === id ? 2.5 : 1.5}
              style={{ color: active === id ? activeColor : inactiveColor }}
            />
            <span
              className="text-[10px] font-bold tracking-wide"
              style={{
                fontFamily: 'JetBrains Mono, monospace',
                color: active === id ? activeColor : inactiveColor,
              }}
            >
              {label}
            </span>
          </button>
        ))}
      </div>
    </nav>
  );
};
