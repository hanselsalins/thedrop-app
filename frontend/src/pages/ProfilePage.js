import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useNotifications } from '../hooks/useNotifications';
import { BottomNav } from '../components/BottomNav';
import { NotificationSettings } from '../components/NotificationSettings';
import { motion, AnimatePresence } from 'framer-motion';
import { LogOut, MapPin, Calendar, Globe, Flame, BookOpen, Trophy, Zap, Heart, Users, ChevronDown, Edit3, Check, Search, UserPlus, Crown, Link, Copy, X } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const RANK_COLORS = {
  'Curious': '#888',
  'Informed': '#3A86FF',
  'Switched On': '#CCFF00',
  'Sharp': '#FF006E',
  'No Cap Legend': '#FFD60A',
};

const AGE_BADGES = {
  '8-10': { label: 'Junior Reader', emoji: '', color: '#FFD60A' },
  '11-13': { label: 'News Scout', emoji: '', color: '#3A86FF' },
  '14-16': { label: 'Drop Regular', emoji: '', color: '#CCFF00' },
  '17-20': { label: 'Sharp Mind', emoji: '', color: '#FF006E' },
};

const CATEGORY_ICONS = {
  world: Globe, science: Zap, money: Trophy, entertainment: Heart,
  history: BookOpen, local: MapPin,
};

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, setUserData, token, ageGroup, themeMode, logout } = useTheme();
  const [stats, setStats] = useState(null);
  const [countries, setCountries] = useState([]);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [editingCity, setEditingCity] = useState(false);
  const [editCity, setEditCity] = useState(user?.city || '');
  const [saving, setSaving] = useState(false);
  const [friends, setFriends] = useState([]);
  const [friendRequests, setFriendRequests] = useState([]);
  const [leaderboard, setLeaderboard] = useState(null);
  const [prevWinner, setPrevWinner] = useState(null);
  const [socialTab, setSocialTab] = useState('friends'); // 'friends', 'leaderboard', 'requests'
  const [showAddFriend, setShowAddFriend] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [inviteLink, setInviteLink] = useState('');
  const [copiedLink, setCopiedLink] = useState(false);
  const { permission, requestPermission } = useNotifications();

  const isKids = themeMode === 'kids';
  const bg = isKids ? '#F0F4F8' : '#050505';
  const text = isKids ? '#1A1A1A' : '#FAFAFA';
  const card = isKids ? '#FFFFFF' : '#0d0d0d';
  const sub = isKids ? '#666' : '#666';
  const border = isKids ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)';
  const accent = isKids ? '#3A86FF' : '#CCFF00';
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    if (!token) return;
    axios.get(`${BACKEND_URL}/api/profile/stats`, { headers }).then(r => setStats(r.data)).catch(() => {});
    axios.get(`${BACKEND_URL}/api/countries`).then(r => setCountries(r.data)).catch(() => {});
    axios.get(`${BACKEND_URL}/api/friends`, { headers }).then(r => setFriends(r.data)).catch(() => {});
    axios.get(`${BACKEND_URL}/api/friends/requests`, { headers }).then(r => setFriendRequests(r.data)).catch(() => {});
    axios.get(`${BACKEND_URL}/api/friends/leaderboard`, { headers }).then(r => {
      setLeaderboard(r.data.leaderboard);
      setPrevWinner(r.data.previous_month_winner);
    }).catch(() => {});
    axios.get(`${BACKEND_URL}/api/invite/my-link`, { headers }).then(r => {
      setInviteLink(`${window.location.origin}${r.data.invite_url}`);
    }).catch(() => {});
  }, [token]);

  const badge = AGE_BADGES[ageGroup] || AGE_BADGES['14-16'];
  const userCountry = countries.find(c => c.country_name === user?.country);

  const handleCountrySelect = async (c) => {
    setShowCountryPicker(false);
    setSaving(true);
    try {
      const res = await axios.put(`${BACKEND_URL}/api/auth/me`, { country: c.country_name }, { headers });
      setUserData(res.data);
    } catch {}
    setSaving(false);
  };

  const handleSaveCity = async () => {
    setSaving(true);
    try {
      const res = await axios.put(`${BACKEND_URL}/api/auth/me`, { city: editCity }, { headers });
      setUserData(res.data);
      setEditingCity(false);
    } catch {}
    setSaving(false);
  };

  const handleLogout = () => { logout(); navigate('/auth'); };

  const handleSearchFriends = async (q) => {
    setSearchQuery(q);
    if (q.length < 2) { setSearchResults([]); return; }
    setSearching(true);
    try {
      const r = await axios.get(`${BACKEND_URL}/api/friends/search?q=${q}`, { headers });
      setSearchResults(r.data);
    } catch { setSearchResults([]); }
    setSearching(false);
  };

  const handleSendRequest = async (username) => {
    try {
      await axios.post(`${BACKEND_URL}/api/friends/request`, { target_username: username }, { headers });
      setSearchResults(prev => prev.filter(r => r.username !== username));
    } catch {}
  };

  const handleAcceptRequest = async (friendshipId) => {
    try {
      await axios.post(`${BACKEND_URL}/api/friends/accept/${friendshipId}`, {}, { headers });
      setFriendRequests(prev => prev.filter(r => r.friendship_id !== friendshipId));
      // Refresh friends
      const r = await axios.get(`${BACKEND_URL}/api/friends`, { headers });
      setFriends(r.data);
    } catch {}
  };

  const handleDeclineRequest = async (friendshipId) => {
    try {
      await axios.post(`${BACKEND_URL}/api/friends/decline/${friendshipId}`, {}, { headers });
      setFriendRequests(prev => prev.filter(r => r.friendship_id !== friendshipId));
    } catch {}
  };

  const handleCopyInvite = () => {
    navigator.clipboard.writeText(inviteLink).then(() => {
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    });
  };

  const getRankLabel = (score) => {
    if (score >= 501) return 'No Cap Legend';
    if (score >= 301) return 'Sharp';
    if (score >= 151) return 'Switched On';
    if (score >= 51) return 'Informed';
    return 'Curious';
  };

  const formatMemberSince = (d) => {
    if (!d) return '';
    try {
      const dt = new Date(d);
      return dt.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    } catch { return ''; }
  };

  // Flame size based on streak milestones
  const getFlameSize = (streak) => {
    if (streak >= 100) return 48;
    if (streak >= 50) return 40;
    if (streak >= 30) return 36;
    if (streak >= 7) return 32;
    return 24;
  };

  return (
    <div data-testid="profile-page" className="min-h-screen pb-24" style={{ background: bg }}>
      <div className="px-5 pt-6 max-w-lg mx-auto">

        {/* ━━━━━ SECTION 1: IDENTITY HEADER ━━━━━ */}
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
          className="relative p-5 rounded-2xl mb-4"
          style={{ background: card, border: `1px solid ${border}` }}>

          {/* Logout */}
          <button data-testid="logout-btn" onClick={handleLogout}
            className="absolute top-4 right-4 p-2 rounded-xl transition-colors"
            style={{ background: 'rgba(255,42,109,0.08)' }}>
            <LogOut size={16} color="#FF2A6D" />
          </button>

          <div className="flex items-start gap-4">
            {/* Avatar */}
            <div className="w-20 h-20 rounded-full overflow-hidden flex-shrink-0 border-3"
              style={{ borderColor: accent, borderWidth: '3px' }}>
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" data-testid="profile-avatar" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-2xl font-bold"
                  style={{ background: `linear-gradient(135deg, ${accent}, #7209B7)`, color: '#fff', fontFamily: 'Syne, sans-serif' }}>
                  {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
              )}
            </div>

            <div className="flex-1 min-w-0 pt-1">
              {/* Name + username */}
              <h1 className="text-xl font-bold truncate" style={{ fontFamily: isKids ? 'Fredoka, sans-serif' : 'Syne, sans-serif', color: text }}>
                {user?.full_name}
                {user?.username && (
                  <span className="text-sm font-normal opacity-40 ml-2" style={{ fontFamily: 'JetBrains Mono, monospace' }}>
                    @{user.username}
                  </span>
                )}
              </h1>

              {/* Country + City */}
              <div className="flex items-center gap-1.5 mt-1">
                {userCountry && <span className="text-sm">{userCountry.flag_emoji}</span>}
                <span className="text-xs" style={{ fontFamily: 'Outfit, sans-serif', color: sub }}>
                  {user?.city ? `${user.city}, ` : ''}{user?.country || ''}
                </span>
              </div>

              {/* Member since + Age badge */}
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                {stats?.member_since && (
                  <span className="text-[10px] opacity-40" style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                    <Calendar size={10} className="inline mr-1" />
                    Member since {formatMemberSince(stats.member_since)}
                  </span>
                )}
                <span data-testid="age-badge" className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full"
                  style={{ fontFamily: 'JetBrains Mono, monospace', background: badge.color, color: '#050505' }}>
                  {badge.label}
                </span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* ━━━━━ SECTION 2: STATS DASHBOARD ━━━━━ */}
        {stats && (
          <div className="space-y-3 mb-4">

            {/* Knowledge Score — hero card */}
            <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.05 }}
              data-testid="knowledge-score-card"
              className="p-5 rounded-2xl text-center relative overflow-hidden"
              style={{
                background: isKids
                  ? 'linear-gradient(135deg, #3A86FF, #8338EC)'
                  : 'linear-gradient(135deg, #0d0d0d 0%, #1a1a1a 100%)',
                border: `1px solid ${border}`,
              }}>
              <div className="absolute top-0 right-0 w-32 h-32 rounded-full opacity-10 blur-2xl"
                style={{ background: RANK_COLORS[stats.knowledge_score.rank_label] || '#CCFF00' }} />

              <p className="text-xs font-bold tracking-[0.2em] uppercase mb-2 opacity-50"
                style={{ fontFamily: 'JetBrains Mono, monospace', color: isKids ? '#fff' : text }}>
                KNOWLEDGE SCORE
              </p>
              <p data-testid="knowledge-score-value" className="text-5xl font-bold mb-1"
                style={{ fontFamily: 'Syne, sans-serif', color: RANK_COLORS[stats.knowledge_score.rank_label] || accent }}>
                {stats.knowledge_score.score}
              </p>
              <span data-testid="knowledge-rank-label" className="inline-block px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase"
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  background: `${RANK_COLORS[stats.knowledge_score.rank_label] || accent}20`,
                  color: RANK_COLORS[stats.knowledge_score.rank_label] || accent,
                  border: `1px solid ${RANK_COLORS[stats.knowledge_score.rank_label] || accent}30`,
                }}>
                {stats.knowledge_score.rank_label}
              </span>
            </motion.div>

            {/* Streak + Stories Read — 2-col grid */}
            <div className="grid grid-cols-2 gap-3">
              {/* Streak */}
              <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}
                data-testid="streak-card"
                className="p-4 rounded-xl" style={{ background: card, border: `1px solid ${border}` }}>
                <div className="flex items-center justify-center mb-2">
                  <Flame size={getFlameSize(stats.streak.current)} color="#FF6B35"
                    fill={stats.streak.current > 0 ? '#FF6B35' : 'none'} />
                </div>
                <p data-testid="streak-current" className="text-2xl font-bold text-center"
                  style={{ fontFamily: 'Syne, sans-serif', color: text }}>
                  {stats.streak.current}
                </p>
                <p className="text-[10px] text-center uppercase tracking-wider opacity-40"
                  style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                  day streak
                </p>
                <p className="text-[10px] text-center mt-1.5 opacity-30"
                  style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                  Best: {stats.streak.longest}
                </p>
              </motion.div>

              {/* Stories Read */}
              <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.12 }}
                data-testid="stories-read-card"
                className="p-4 rounded-xl" style={{ background: card, border: `1px solid ${border}` }}>
                <div className="flex items-center justify-center mb-2">
                  <BookOpen size={24} color={accent} />
                </div>
                <p data-testid="stories-read-total" className="text-2xl font-bold text-center"
                  style={{ fontFamily: 'Syne, sans-serif', color: text }}>
                  {stats.stories_read.total}
                </p>
                <p className="text-[10px] text-center uppercase tracking-wider opacity-40"
                  style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                  stories read
                </p>
                <p className="text-[10px] text-center mt-1.5 opacity-30"
                  style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                  This week: {stats.stories_read.this_week} / Month: {stats.stories_read.this_month}
                </p>
              </motion.div>
            </div>

            {/* Favourite Topic + Reactions — 2-col grid */}
            <div className="grid grid-cols-2 gap-3">
              {/* Favourite Topic */}
              <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.15 }}
                data-testid="favourite-topic-card"
                className="p-4 rounded-xl" style={{ background: card, border: `1px solid ${border}` }}>
                {(() => {
                  const CatIcon = CATEGORY_ICONS[stats.favourite_category] || Globe;
                  return (
                    <>
                      <div className="flex items-center justify-center mb-2">
                        <Trophy size={24} color="#FFD60A" />
                      </div>
                      <p className="text-sm font-bold text-center capitalize"
                        style={{ fontFamily: 'Syne, sans-serif', color: text }}>
                        {stats.favourite_category}
                      </p>
                      <p className="text-[10px] text-center uppercase tracking-wider opacity-40"
                        style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                        top topic
                      </p>
                    </>
                  );
                })()}
              </motion.div>

              {/* Reactions */}
              <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.17 }}
                data-testid="reactions-card"
                className="p-4 rounded-xl" style={{ background: card, border: `1px solid ${border}` }}>
                <div className="flex items-center justify-center mb-2">
                  <span className="text-2xl">{stats.reactions.most_used || '---'}</span>
                </div>
                <p data-testid="reactions-total" className="text-2xl font-bold text-center"
                  style={{ fontFamily: 'Syne, sans-serif', color: text }}>
                  {stats.reactions.total}
                </p>
                <p className="text-[10px] text-center uppercase tracking-wider opacity-40"
                  style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                  reactions
                </p>
                <p className="text-[10px] text-center mt-1.5 opacity-30"
                  style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                  This month: {stats.reactions.this_month}
                </p>
              </motion.div>
            </div>

            {/* Countries Covered */}
            <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}
              data-testid="countries-card"
              className="p-4 rounded-xl flex items-center gap-4" style={{ background: card, border: `1px solid ${border}` }}>
              <Globe size={28} color={accent} />
              <div>
                <p className="text-lg font-bold" style={{ fontFamily: 'Syne, sans-serif', color: text }}>
                  {stats.countries_covered} <span className="text-sm font-normal opacity-40">countries</span>
                </p>
                <p className="text-[10px] uppercase tracking-wider opacity-40"
                  style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                  in your feed this week
                </p>
              </div>
            </motion.div>
          </div>
        )}

        {/* ━━━━━ SECTION 3: SETTINGS ━━━━━ */}
        <div className="space-y-3 mb-4">
          {/* Country Selector */}
          <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.25 }}
            className="p-4 rounded-xl relative" style={{ background: card, border: `1px solid ${border}` }}>
            <p className="text-[10px] font-bold tracking-wider uppercase mb-2 opacity-40"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>NEWS COUNTRY</p>
            <button data-testid="country-selector-btn" onClick={() => setShowCountryPicker(!showCountryPicker)}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg"
              style={{ background: isKids ? '#f5f5f5' : 'rgba(255,255,255,0.04)', border: `1px solid ${border}` }}>
              <span className="text-sm font-medium" style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                {userCountry ? `${userCountry.flag_emoji} ${userCountry.country_name}` : (user?.country || 'Select')}
              </span>
              <ChevronDown size={14} style={{ color: sub }} />
            </button>
            {showCountryPicker && (
              <div className="absolute left-0 right-0 mt-1 mx-4 rounded-xl overflow-hidden z-20 max-h-52 overflow-y-auto"
                style={{ background: isKids ? '#fff' : '#1a1a1a', border: `1px solid ${border}`, boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
                {countries.map(c => (
                  <button key={c.country_code} data-testid={`country-option-${c.country_code}`}
                    onClick={() => handleCountrySelect(c)}
                    className="w-full text-left px-4 py-2.5 text-sm flex items-center gap-2 transition-colors"
                    style={{ fontFamily: 'Outfit, sans-serif', color: c.country_name === user?.country ? accent : text }}
                    onMouseEnter={e => e.target.style.background = isKids ? 'rgba(0,0,0,0.03)' : 'rgba(255,255,255,0.04)'}
                    onMouseLeave={e => e.target.style.background = 'transparent'}>
                    <span>{c.flag_emoji}</span><span>{c.country_name}</span>
                  </button>
                ))}
              </div>
            )}
          </motion.div>

          {/* City */}
          <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.27 }}
            className="p-4 rounded-xl" style={{ background: card, border: `1px solid ${border}` }}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-[10px] font-bold tracking-wider uppercase opacity-40"
                style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>CITY</p>
              {!editingCity ? (
                <button data-testid="edit-city-btn" onClick={() => { setEditingCity(true); setEditCity(user?.city || ''); }}
                  className="p-1.5 rounded-lg" style={{ background: `${accent}15` }}>
                  <Edit3 size={12} color={accent} />
                </button>
              ) : (
                <button data-testid="save-city-btn" onClick={handleSaveCity} disabled={saving}
                  className="p-1.5 rounded-lg" style={{ background: `${accent}15` }}>
                  <Check size={12} color={accent} />
                </button>
              )}
            </div>
            {editingCity ? (
              <input data-testid="edit-city-input" value={editCity} onChange={e => setEditCity(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-sm outline-none"
                style={{ fontFamily: 'Outfit, sans-serif', background: isKids ? '#f5f5f5' : 'rgba(255,255,255,0.04)', border: `1px solid ${border}`, color: text }} />
            ) : (
              <p className="text-sm font-medium" style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                {user?.city || 'Not set'}
              </p>
            )}
          </motion.div>

          {/* Notification Settings */}
          <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
            <NotificationSettings isKids={isKids} permission={permission} onRequestPermission={requestPermission} />
          </motion.div>
        </div>

        {/* ━━━━━ SECTION 3: SOCIAL / FRIENDS ━━━━━ */}
        <motion.div initial={{ y: 15, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.35 }}
          className="mb-4">

          {/* Section header + Add Friend */}
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold" style={{ fontFamily: isKids ? 'Fredoka, sans-serif' : 'Syne, sans-serif', color: text }}>
              Friends
            </h2>
            <div className="flex gap-2">
              <button data-testid="invite-link-btn" onClick={handleCopyInvite}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] font-bold uppercase tracking-wider"
                style={{ fontFamily: 'JetBrains Mono, monospace', background: `${accent}15`, color: accent }}>
                {copiedLink ? <Check size={12} /> : <Link size={12} />}
                {copiedLink ? 'Copied!' : 'Invite'}
              </button>
              <button data-testid="add-friend-btn" onClick={() => setShowAddFriend(!showAddFriend)}
                className="p-2 rounded-xl" style={{ background: `${accent}15` }}>
                {showAddFriend ? <X size={14} color={accent} /> : <UserPlus size={14} color={accent} />}
              </button>
            </div>
          </div>

          {/* Add Friend Search Modal */}
          <AnimatePresence>
            {showAddFriend && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                className="mb-3 overflow-hidden">
                <div className="p-4 rounded-xl" style={{ background: card, border: `1px solid ${border}` }}>
                  <div className="relative mb-3">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 opacity-30" style={{ color: text }} />
                    <input data-testid="friend-search-input" placeholder="Find @username" value={searchQuery}
                      onChange={e => handleSearchFriends(e.target.value)}
                      className="w-full pl-9 pr-4 py-2.5 rounded-lg text-sm outline-none"
                      style={{ fontFamily: 'JetBrains Mono, monospace', background: isKids ? '#f5f5f5' : 'rgba(255,255,255,0.04)', border: `1px solid ${border}`, color: text }} />
                  </div>
                  {searching && <p className="text-xs opacity-30 text-center py-2" style={{ color: text }}>Searching...</p>}
                  {searchResults.map(r => (
                    <div key={r.id} className="flex items-center gap-3 py-2.5 border-t" style={{ borderColor: border }}>
                      <img src={r.avatar_url} alt="" className="w-9 h-9 rounded-full" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate" style={{ fontFamily: 'Outfit, sans-serif', color: text }}>{r.full_name}</p>
                        <p className="text-[10px] opacity-40" style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>@{r.username} · {r.knowledge_score} pts</p>
                      </div>
                      <button data-testid={`add-friend-${r.username}`} onClick={() => handleSendRequest(r.username)}
                        className="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase"
                        style={{ fontFamily: 'JetBrains Mono, monospace', background: accent, color: '#050505' }}>
                        Add
                      </button>
                    </div>
                  ))}
                  {searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
                    <p className="text-xs opacity-30 text-center py-2" style={{ color: text }}>No users found</p>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Tabs: Friends / Leaderboard / Requests */}
          <div className="flex gap-1 p-1 rounded-xl mb-3" style={{ background: isKids ? '#e8e8e8' : 'rgba(255,255,255,0.04)' }}>
            {[
              { id: 'friends', label: 'Friends', count: friends.length },
              { id: 'leaderboard', label: 'Board' },
              { id: 'requests', label: 'Requests', count: friendRequests.length },
            ].map(tab => (
              <button key={tab.id} data-testid={`social-tab-${tab.id}`}
                onClick={() => setSocialTab(tab.id)}
                className="flex-1 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-1"
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  background: socialTab === tab.id ? (isKids ? '#fff' : 'rgba(255,255,255,0.08)') : 'transparent',
                  color: socialTab === tab.id ? accent : sub,
                }}>
                {tab.label}
                {tab.count > 0 && (
                  <span className="w-4 h-4 rounded-full text-[8px] flex items-center justify-center"
                    style={{ background: tab.id === 'requests' ? '#FF2A6D' : accent, color: '#050505' }}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Friends List */}
          {socialTab === 'friends' && (
            <div className="space-y-1" style={{ background: card, borderRadius: '12px', border: `1px solid ${border}` }}>
              {friends.length === 0 ? (
                <p className="text-xs opacity-30 text-center py-6" style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                  No friends yet. Search or share your invite link!
                </p>
              ) : (
                friends.slice(0, 20).map((f, i) => (
                  <div key={f.id} data-testid={`friend-${f.username}`}
                    className="flex items-center gap-3 px-4 py-3"
                    style={{ borderTop: i > 0 ? `1px solid ${border}` : 'none' }}>
                    <img src={f.avatar_url} alt="" className="w-9 h-9 rounded-full" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate" style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                        {f.full_name} <span className="text-[10px] opacity-40" style={{ fontFamily: 'JetBrains Mono, monospace' }}>@{f.username}</span>
                      </p>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] flex items-center gap-0.5" style={{ color: '#FF6B35' }}>
                          <Flame size={10} /> {f.current_streak}
                        </span>
                        <span className="text-[10px] opacity-40" style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                          {f.knowledge_score} pts · {getRankLabel(f.knowledge_score)}
                        </span>
                      </div>
                    </div>
                    {f.last_read_date !== new Date().toISOString().split('T')[0] && f.current_streak > 0 && (
                      <span className="text-[8px] px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(255,107,53,0.1)', color: '#FF6B35', fontFamily: 'JetBrains Mono, monospace' }}>
                        at risk
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Leaderboard */}
          {socialTab === 'leaderboard' && leaderboard && (
            <div style={{ background: card, borderRadius: '12px', border: `1px solid ${border}` }}>
              {prevWinner && (
                <div className="px-4 py-3 text-center" style={{ borderBottom: `1px solid ${border}` }}>
                  <span className="text-[10px] opacity-40" style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                    Last month's No Cap Legend: <Crown size={10} className="inline" style={{ color: '#FFD60A' }} /> @{prevWinner.username}
                  </span>
                </div>
              )}
              {leaderboard.map((e, i) => (
                <div key={e.id} data-testid={`leaderboard-${e.rank}`}
                  className="flex items-center gap-3 px-4 py-3"
                  style={{
                    borderTop: i > 0 ? `1px solid ${border}` : 'none',
                    background: e.is_self ? `${accent}08` : 'transparent',
                  }}>
                  <span className="w-6 text-center text-sm font-bold"
                    style={{ fontFamily: 'Syne, sans-serif', color: e.rank <= 3 ? '#FFD60A' : sub }}>
                    {e.rank}
                  </span>
                  <img src={e.avatar_url} alt="" className="w-8 h-8 rounded-full" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                      {e.full_name} {e.is_self && <span className="text-[9px] opacity-40">(you)</span>}
                    </p>
                    <span className="text-[10px] opacity-40" style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                      {e.rank_label}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold" style={{ fontFamily: 'Syne, sans-serif', color: RANK_COLORS[e.rank_label] || accent }}>
                      {e.knowledge_score}
                    </p>
                    <span className="text-[9px] flex items-center gap-0.5 justify-end" style={{ color: '#FF6B35' }}>
                      <Flame size={9} /> {e.current_streak}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Friend Requests */}
          {socialTab === 'requests' && (
            <div style={{ background: card, borderRadius: '12px', border: `1px solid ${border}` }}>
              {friendRequests.length === 0 ? (
                <p className="text-xs opacity-30 text-center py-6" style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                  No pending requests
                </p>
              ) : (
                friendRequests.map((r, i) => (
                  <div key={r.friendship_id} data-testid={`request-${r.sender.username}`}
                    className="flex items-center gap-3 px-4 py-3"
                    style={{ borderTop: i > 0 ? `1px solid ${border}` : 'none' }}>
                    <img src={r.sender.avatar_url} alt="" className="w-9 h-9 rounded-full" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate" style={{ fontFamily: 'Outfit, sans-serif', color: text }}>
                        {r.sender.full_name}
                      </p>
                      <p className="text-[10px] opacity-40" style={{ fontFamily: 'JetBrains Mono, monospace', color: text }}>
                        @{r.sender.username}
                      </p>
                    </div>
                    <div className="flex gap-1.5">
                      <button data-testid={`accept-${r.sender.username}`} onClick={() => handleAcceptRequest(r.friendship_id)}
                        className="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase"
                        style={{ fontFamily: 'JetBrains Mono, monospace', background: accent, color: '#050505' }}>
                        Accept
                      </button>
                      <button data-testid={`decline-${r.sender.username}`} onClick={() => handleDeclineRequest(r.friendship_id)}
                        className="px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase"
                        style={{ fontFamily: 'JetBrains Mono, monospace', background: 'rgba(255,42,109,0.1)', color: '#FF2A6D' }}>
                        Decline
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </motion.div>
      </div>

      <BottomNav isKids={isKids} active="profile" />
    </div>
  );
}
