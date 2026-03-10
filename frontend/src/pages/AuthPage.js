import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, ArrowLeft, Eye, EyeOff, Mail, Lock, User, MapPin, ChevronDown, Check, Shield, Sparkles } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AVATAR_SEEDS = ['', '-star', '-moon', '-sun', '-fire', '-wave', '-leaf', '-gem'];
const getAvatarUrl = (seed) => `https://api.dicebear.com/9.x/adventurer/svg?seed=${seed}`;
const generateAvatarOptions = (baseSeed) =>
  AVATAR_SEEDS.map(s => ({ seed: `${baseSeed}${s}`, url: getAvatarUrl(`${baseSeed}${s}`) }));

const AGE_BADGES = {
  '8-10': { label: 'Junior Reader', color: '#FFD60A' },
  '11-13': { label: 'News Scout', color: '#3A86FF' },
  '14-16': { label: 'Drop Regular', color: '#CCFF00' },
  '17-20': { label: 'Sharp Mind', color: '#FF006E' },
};

// Shared styles
const inputStyle = {
  background: 'rgba(255,255,255,0.06)',
  border: '1px solid rgba(255,255,255,0.12)',
  borderRadius: '14px',
  color: '#FAFAFA',
  fontFamily: 'Outfit, sans-serif',
};
const inputClass = "w-full px-4 py-3.5 text-base outline-none placeholder:text-white/30 focus:border-[#CCFF00]/50";
const btnPrimary = "w-full py-4 rounded-2xl text-base font-bold tracking-wide flex items-center justify-center gap-2 transition-all";

const slideIn = { initial: { x: 60, opacity: 0 }, animate: { x: 0, opacity: 1 }, exit: { x: -60, opacity: 0 }, transition: { duration: 0.3 } };

export default function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const invitedBy = location.state?.invitedBy || '';
  const { setToken, setUserData } = useTheme();
  const [phase, setPhase] = useState('gate'); // 'gate', 'flow-a', 'flow-b', 'login'
  const [error, setError] = useState('');

  const connectWithInviter = async (tkn) => {
    if (!invitedBy) return;
    try { await axios.post(`${BACKEND_URL}/api/invite/connect/${invitedBy}`, {}, { headers: { Authorization: `Bearer ${tkn}` } }); } catch {}
  };

  return (
    <div data-testid="auth-page" className="min-h-screen flex flex-col relative overflow-hidden" style={{ background: '#050505' }}>
      {/* Background accent */}
      <div className="absolute top-0 right-0 w-72 h-72 rounded-full opacity-10 blur-3xl" style={{ background: '#CCFF00' }} />
      <div className="absolute bottom-0 left-0 w-60 h-60 rounded-full opacity-8 blur-3xl" style={{ background: '#7209B7' }} />

      <div className="relative z-10 flex-1 flex flex-col px-5 py-8">
        <AnimatePresence mode="wait">
          {phase === 'gate' && <AgeGate key="gate" setPhase={setPhase} />}
          {phase === 'flow-a' && <FlowA key="flow-a" setPhase={setPhase} setToken={setToken} setUserData={setUserData} navigate={navigate} error={error} setError={setError} connectWithInviter={connectWithInviter} />}
          {phase === 'flow-b' && <FlowB key="flow-b" setPhase={setPhase} setToken={setToken} setUserData={setUserData} navigate={navigate} error={error} setError={setError} connectWithInviter={connectWithInviter} />}
          {phase === 'login' && <LoginForm key="login" setPhase={setPhase} setToken={setToken} setUserData={setUserData} navigate={navigate} error={error} setError={setError} />}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━ AGE GATE ━━━━━━━━━━━━━━━━━━━
function AgeGate({ setPhase }) {
  const [age, setAge] = useState('');

  const handleContinue = () => {
    const a = parseInt(age);
    if (!a || a < 5 || a > 99) return;
    setPhase(a < 14 ? 'flow-a' : 'flow-b');
  };

  return (
    <motion.div {...slideIn} className="flex-1 flex flex-col justify-center">
      <div className="mb-2">
        <span className="text-xs font-bold tracking-[0.3em] uppercase" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#CCFF00' }}>THE DROP</span>
      </div>
      <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-3" style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}>
        How old are you?
      </h1>
      <p className="text-base opacity-50 mb-10" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>
        We'll set up the right experience for your age.
      </p>

      <div className="mb-8">
        <input
          data-testid="age-gate-input"
          type="number"
          min="5" max="99"
          value={age}
          onChange={e => setAge(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleContinue()}
          placeholder="Enter your age"
          className={inputClass}
          style={{ ...inputStyle, fontSize: '1.5rem', textAlign: 'center', padding: '1.2rem' }}
        />
      </div>

      <button
        data-testid="age-gate-continue"
        onClick={handleContinue}
        disabled={!age || parseInt(age) < 5}
        className={btnPrimary}
        style={{
          background: age && parseInt(age) >= 5 ? '#CCFF00' : 'rgba(204,255,0,0.15)',
          color: '#050505',
          fontFamily: 'Syne, sans-serif',
          opacity: age && parseInt(age) >= 5 ? 1 : 0.4,
        }}
      >
        Continue <ArrowRight size={18} />
      </button>

      <button
        data-testid="age-gate-login-link"
        onClick={() => setPhase('login')}
        className="mt-6 text-sm opacity-50 hover:opacity-80 transition-opacity"
        style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}
      >
        Already have an account? <span style={{ color: '#CCFF00' }}>Log in</span>
      </button>
    </motion.div>
  );
}

// ━━━━━━━━━━━━━━━━━━━ FLOW A — PARENT-LED (UNDER 14) ━━━━━━━━━━━━━━━━━━━
function FlowA({ setPhase, setToken, setUserData, navigate, error, setError, connectWithInviter }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [countries, setCountries] = useState([]);
  const [showCountryDrop, setShowCountryDrop] = useState(false);
  const [cities, setCities] = useState([]);
  const [showPass, setShowPass] = useState(false);

  const [form, setForm] = useState({
    parent_name: '', parent_email: '', parent_password: '',
    consent_guardian: false, consent_terms: false,
    child_name: '', child_age: '', child_country: '', child_city: '',
    avatar_url: '',
  });
  const u = (k, v) => { setForm(p => ({ ...p, [k]: v })); setError(''); };

  useEffect(() => {
    axios.get(`${BACKEND_URL}/api/countries`).then(r => setCountries(r.data)).catch(() => {});
  }, []);

  const selectCountry = (c) => {
    u('child_country', c.country_name);
    setShowCountryDrop(false);
    setCities([...(c.city_tier_1 || []), ...(c.city_tier_2 || [])]);
  };

  const avatarOptions = generateAvatarOptions(form.child_name.toLowerCase().replace(/\s/g, '') || 'kid');

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${BACKEND_URL}/api/auth/register-child`, {
        parent_name: form.parent_name,
        parent_email: form.parent_email,
        parent_password: form.parent_password,
        child_name: form.child_name,
        child_age: parseInt(form.child_age),
        child_country: form.child_country,
        child_city: form.child_city,
        avatar_url: form.avatar_url,
      });
      setToken(res.data.token);
      setUserData(res.data.user);
      await connectWithInviter(res.data.token);
      navigate('/feed');
    } catch (e) {
      setError(e.response?.data?.detail || 'Registration failed');
    }
    setLoading(false);
  };

  const canStep1 = form.parent_name && form.parent_email && form.parent_password.length >= 8 && form.consent_guardian && form.consent_terms;
  const canStep2 = form.child_name && form.child_age && form.child_country;
  const canStep3 = !!form.avatar_url;

  const ageGroup = form.child_age ? (parseInt(form.child_age) <= 10 ? '8-10' : '11-13') : '';
  const badge = ageGroup ? AGE_BADGES[ageGroup] : null;
  const selectedCountry = countries.find(c => c.country_name === form.child_country);

  return (
    <motion.div {...slideIn} className="flex-1 flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button data-testid="flow-a-back" onClick={() => step > 1 ? setStep(step - 1) : setPhase('gate')}
          className="p-2 rounded-xl" style={{ background: 'rgba(255,255,255,0.06)' }}>
          <ArrowLeft size={18} color="#FAFAFA" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-1.5">
            <Shield size={14} style={{ color: '#CCFF00' }} />
            <span className="text-xs font-bold tracking-[0.2em] uppercase" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#CCFF00' }}>
              PARENT SETUP
            </span>
          </div>
          <p className="text-xs opacity-40 mt-0.5" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>
            Step {step} of 3
          </p>
        </div>
        {/* Progress dots */}
        <div className="flex gap-1.5">
          {[1, 2, 3].map(i => (
            <div key={i} className="w-2 h-2 rounded-full transition-all" style={{ background: i <= step ? '#CCFF00' : 'rgba(255,255,255,0.15)' }} />
          ))}
        </div>
      </div>

      {error && <div data-testid="auth-error" className="mb-4 px-4 py-3 rounded-xl text-sm" style={{ background: 'rgba(255,42,109,0.1)', border: '1px solid rgba(255,42,109,0.2)', color: '#FF2A6D', fontFamily: 'Outfit, sans-serif' }}>{error}</div>}

      <AnimatePresence mode="wait">
        {/* Step 1: Parent Details */}
        {step === 1 && (
          <motion.div key="a1" {...slideIn} className="flex-1 flex flex-col">
            <h2 className="text-2xl font-bold mb-1" style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}>Parent details</h2>
            <p className="text-sm opacity-40 mb-6" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>We need your info to set up a safe account.</p>

            <div className="space-y-3 mb-6">
              <input data-testid="parent-name-input" placeholder="Your first name" value={form.parent_name} onChange={e => u('parent_name', e.target.value)} className={inputClass} style={inputStyle} />
              <div className="relative">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 opacity-30" color="#FAFAFA" />
                <input data-testid="parent-email-input" type="email" placeholder="Your email address" value={form.parent_email} onChange={e => u('parent_email', e.target.value)} className={inputClass} style={{ ...inputStyle, paddingLeft: '2.8rem' }} />
              </div>
              <div className="relative">
                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 opacity-30" color="#FAFAFA" />
                <input data-testid="parent-password-input" type={showPass ? 'text' : 'password'} placeholder="Create a password (min 8 chars)" value={form.parent_password} onChange={e => u('parent_password', e.target.value)} className={inputClass} style={{ ...inputStyle, paddingLeft: '2.8rem', paddingRight: '3rem' }} />
                <button onClick={() => setShowPass(!showPass)} className="absolute right-4 top-1/2 -translate-y-1/2 opacity-40">
                  {showPass ? <EyeOff size={16} color="#FAFAFA" /> : <Eye size={16} color="#FAFAFA" />}
                </button>
              </div>
            </div>

            <div className="space-y-3 mb-8">
              <label className="flex items-start gap-3 cursor-pointer" onClick={() => u('consent_guardian', !form.consent_guardian)}>
                <div data-testid="consent-guardian-checkbox" className="w-5 h-5 rounded-md flex-shrink-0 flex items-center justify-center mt-0.5"
                  style={{ background: form.consent_guardian ? '#CCFF00' : 'transparent', border: form.consent_guardian ? 'none' : '1px solid rgba(255,255,255,0.2)' }}>
                  {form.consent_guardian && <Check size={13} color="#050505" strokeWidth={3} />}
                </div>
                <span className="text-xs" style={{ fontFamily: 'Outfit, sans-serif', color: 'rgba(250,250,250,0.6)' }}>I am the parent or guardian of the child who will use this account.</span>
              </label>
              <label className="flex items-start gap-3 cursor-pointer" onClick={() => u('consent_terms', !form.consent_terms)}>
                <div data-testid="consent-terms-checkbox" className="w-5 h-5 rounded-md flex-shrink-0 flex items-center justify-center mt-0.5"
                  style={{ background: form.consent_terms ? '#CCFF00' : 'transparent', border: form.consent_terms ? 'none' : '1px solid rgba(255,255,255,0.2)' }}>
                  {form.consent_terms && <Check size={13} color="#050505" strokeWidth={3} />}
                </div>
                <span className="text-xs" style={{ fontFamily: 'Outfit, sans-serif', color: 'rgba(250,250,250,0.6)' }}>I agree to The Drop's Terms of Service and Privacy Policy.</span>
              </label>
            </div>

            <div className="mt-auto">
              <button data-testid="flow-a-step1-next" onClick={() => setStep(2)} disabled={!canStep1}
                className={btnPrimary} style={{ background: canStep1 ? '#CCFF00' : 'rgba(204,255,0,0.15)', color: '#050505', fontFamily: 'Syne, sans-serif', opacity: canStep1 ? 1 : 0.4 }}>
                Next: Child's Profile <ArrowRight size={18} />
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 2: Child Profile */}
        {step === 2 && (
          <motion.div key="a2" {...slideIn} className="flex-1 flex flex-col">
            <h2 className="text-2xl font-bold mb-1" style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}>Child's profile</h2>
            <p className="text-sm opacity-40 mb-6" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>This is what they'll see in the app.</p>

            <div className="space-y-3 mb-6">
              <input data-testid="child-name-input" placeholder="Child's first name" value={form.child_name} onChange={e => u('child_name', e.target.value)} className={inputClass} style={inputStyle} />
              <input data-testid="child-age-input" type="number" min="5" max="13" placeholder="Child's age" value={form.child_age} onChange={e => u('child_age', e.target.value)} className={inputClass} style={inputStyle} />

              {badge && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <span className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full" style={{ fontFamily: 'JetBrains Mono, monospace', background: badge.color, color: '#050505' }}>{badge.label}</span>
                  <span className="text-xs opacity-40" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>Auto-assigned from age</span>
                </div>
              )}

              {/* Country selector */}
              <div className="relative">
                <button data-testid="child-country-selector" onClick={() => setShowCountryDrop(!showCountryDrop)}
                  className={`${inputClass} text-left flex items-center justify-between`} style={inputStyle}>
                  <span style={{ opacity: form.child_country ? 1 : 0.3 }}>
                    {selectedCountry ? `${selectedCountry.flag_emoji} ${selectedCountry.country_name}` : 'Select country'}
                  </span>
                  <ChevronDown size={16} style={{ color: 'rgba(250,250,250,0.3)', transform: showCountryDrop ? 'rotate(180deg)' : 'none', transition: '0.2s' }} />
                </button>
                {showCountryDrop && (
                  <div className="absolute left-0 right-0 mt-1 rounded-xl overflow-hidden z-20 max-h-48 overflow-y-auto"
                    style={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.12)', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
                    {countries.map(c => (
                      <button key={c.country_code} data-testid={`child-country-${c.country_code}`} onClick={() => selectCountry(c)}
                        className="w-full text-left px-4 py-2.5 text-sm flex items-center gap-2 hover:bg-white/5"
                        style={{ fontFamily: 'Outfit, sans-serif', color: c.country_name === form.child_country ? '#CCFF00' : '#FAFAFA' }}>
                        <span>{c.flag_emoji}</span><span>{c.country_name}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* City selector */}
              {cities.length > 0 && (
                <select data-testid="child-city-select" value={form.child_city} onChange={e => u('child_city', e.target.value)}
                  className={inputClass} style={{ ...inputStyle, appearance: 'none' }}>
                  <option value="">Select city (optional)</option>
                  {cities.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              )}
            </div>

            <div className="mt-auto">
              <button data-testid="flow-a-step2-next" onClick={() => setStep(3)} disabled={!canStep2}
                className={btnPrimary} style={{ background: canStep2 ? '#CCFF00' : 'rgba(204,255,0,0.15)', color: '#050505', fontFamily: 'Syne, sans-serif', opacity: canStep2 ? 1 : 0.4 }}>
                Next: Pick an Avatar <ArrowRight size={18} />
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Avatar Selection */}
        {step === 3 && (
          <motion.div key="a3" {...slideIn} className="flex-1 flex flex-col">
            <h2 className="text-2xl font-bold mb-1" style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}>Pick an avatar</h2>
            <p className="text-sm opacity-40 mb-6" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>Choose a look for {form.child_name || 'your child'}.</p>

            <div className="grid grid-cols-4 gap-3 mb-8">
              {avatarOptions.map((av, i) => (
                <button key={av.seed} data-testid={`avatar-option-${i}`}
                  onClick={() => u('avatar_url', av.url)}
                  className="aspect-square rounded-2xl overflow-hidden transition-all"
                  style={{
                    border: form.avatar_url === av.url ? '3px solid #CCFF00' : '2px solid rgba(255,255,255,0.08)',
                    background: 'rgba(255,255,255,0.04)',
                    transform: form.avatar_url === av.url ? 'scale(1.05)' : 'scale(1)',
                  }}>
                  <img src={av.url} alt={`Avatar ${i + 1}`} className="w-full h-full" />
                </button>
              ))}
            </div>

            <div className="mt-auto">
              <button data-testid="flow-a-submit" onClick={handleSubmit} disabled={!canStep3 || loading}
                className={btnPrimary} style={{ background: canStep3 ? '#CCFF00' : 'rgba(204,255,0,0.15)', color: '#050505', fontFamily: 'Syne, sans-serif', opacity: canStep3 ? 1 : 0.4 }}>
                {loading ? 'Creating account...' : 'Create Account'} {!loading && <Sparkles size={18} />}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ━━━━━━━━━━━━━━━━━━━ FLOW B — SELF SIGNUP (14+) ━━━━━━━━━━━━━━━━━━━
function FlowB({ setPhase, setToken, setUserData, navigate, error, setError, connectWithInviter }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [countries, setCountries] = useState([]);
  const [showCountryDrop, setShowCountryDrop] = useState(false);
  const [cities, setCities] = useState([]);
  const [showPass, setShowPass] = useState(false);
  const [usernameStatus, setUsernameStatus] = useState(null); // null, 'checking', 'available', 'taken'
  const [topArticles, setTopArticles] = useState([]);

  const [form, setForm] = useState({
    full_name: '', email: '', password: '',
    age: '', country: '', city: '',
    username: '', avatar_url: '', consent_terms: false,
  });
  const u = (k, v) => { setForm(p => ({ ...p, [k]: v })); setError(''); };

  useEffect(() => {
    axios.get(`${BACKEND_URL}/api/countries`).then(r => setCountries(r.data)).catch(() => {});
  }, []);

  const selectCountry = (c) => {
    u('country', c.country_name);
    setShowCountryDrop(false);
    setCities([...(c.city_tier_1 || []), ...(c.city_tier_2 || [])]);
  };

  // Username check with debounce
  const checkUsername = useCallback(async (val) => {
    const clean = val.toLowerCase().replace(/[^a-z0-9_]/g, '');
    if (clean.length < 3) { setUsernameStatus(null); return; }
    setUsernameStatus('checking');
    try {
      const r = await axios.get(`${BACKEND_URL}/api/auth/check-username/${clean}`);
      setUsernameStatus(r.data.available ? 'available' : 'taken');
    } catch { setUsernameStatus(null); }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => { if (form.username) checkUsername(form.username); }, 500);
    return () => clearTimeout(t);
  }, [form.username, checkUsername]);

  const avatarOptions = generateAvatarOptions(form.username || form.full_name.toLowerCase().replace(/\s/g, '') || 'user');

  const ageGroup = form.age ? (parseInt(form.age) <= 16 ? '14-16' : '17-20') : '';
  const badge = ageGroup ? AGE_BADGES[ageGroup] : null;
  const selectedCountry = countries.find(c => c.country_name === form.country);

  const canStep1 = form.full_name && form.email && form.password.length >= 8 && form.age && parseInt(form.age) >= 14 && form.country;
  const canStep2 = form.username && usernameStatus === 'available' && form.avatar_url && form.consent_terms;

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${BACKEND_URL}/api/auth/register-self`, {
        full_name: form.full_name, email: form.email, password: form.password,
        age: parseInt(form.age), country: form.country, city: form.city,
        username: form.username, avatar_url: form.avatar_url,
      });
      setToken(res.data.token);
      setUserData(res.data.user);
      await connectWithInviter(res.data.token);
      // Fetch top articles for welcome screen
      try {
        const articlesRes = await axios.get(`${BACKEND_URL}/api/articles`, {
          params: { limit: 3, age_group: res.data.user.age_group },
          headers: { Authorization: `Bearer ${res.data.token}` },
        });
        setTopArticles(articlesRes.data);
      } catch {}
      setStep(3); // Welcome screen
    } catch (e) {
      setError(e.response?.data?.detail || 'Registration failed');
    }
    setLoading(false);
  };

  return (
    <motion.div {...slideIn} className="flex-1 flex flex-col">
      {/* Header */}
      {step < 3 && (
        <div className="flex items-center gap-3 mb-6">
          <button data-testid="flow-b-back" onClick={() => step > 1 ? setStep(step - 1) : setPhase('gate')}
            className="p-2 rounded-xl" style={{ background: 'rgba(255,255,255,0.06)' }}>
            <ArrowLeft size={18} color="#FAFAFA" />
          </button>
          <div className="flex-1">
            <span className="text-xs font-bold tracking-[0.2em] uppercase" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#CCFF00' }}>
              SIGN UP
            </span>
            <p className="text-xs opacity-40 mt-0.5" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>Step {step} of 2</p>
          </div>
          <div className="flex gap-1.5">
            {[1, 2].map(i => (
              <div key={i} className="w-2 h-2 rounded-full" style={{ background: i <= step ? '#CCFF00' : 'rgba(255,255,255,0.15)' }} />
            ))}
          </div>
        </div>
      )}

      {error && <div data-testid="auth-error" className="mb-4 px-4 py-3 rounded-xl text-sm" style={{ background: 'rgba(255,42,109,0.1)', border: '1px solid rgba(255,42,109,0.2)', color: '#FF2A6D', fontFamily: 'Outfit, sans-serif' }}>{error}</div>}

      <AnimatePresence mode="wait">
        {/* Step 1: Basic Details */}
        {step === 1 && (
          <motion.div key="b1" {...slideIn} className="flex-1 flex flex-col">
            <h2 className="text-2xl font-bold mb-1" style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}>Join The Drop</h2>
            <p className="text-sm opacity-40 mb-6" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>No cap news, your way.</p>

            <div className="space-y-3 mb-6">
              <input data-testid="self-name-input" placeholder="First name" value={form.full_name} onChange={e => u('full_name', e.target.value)} className={inputClass} style={inputStyle} />
              <div className="relative">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 opacity-30" color="#FAFAFA" />
                <input data-testid="self-email-input" type="email" placeholder="Email address" value={form.email} onChange={e => u('email', e.target.value)} className={inputClass} style={{ ...inputStyle, paddingLeft: '2.8rem' }} />
              </div>
              <div className="relative">
                <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 opacity-30" color="#FAFAFA" />
                <input data-testid="self-password-input" type={showPass ? 'text' : 'password'} placeholder="Password (min 8 chars)" value={form.password} onChange={e => u('password', e.target.value)} className={inputClass} style={{ ...inputStyle, paddingLeft: '2.8rem', paddingRight: '3rem' }} />
                <button onClick={() => setShowPass(!showPass)} className="absolute right-4 top-1/2 -translate-y-1/2 opacity-40">
                  {showPass ? <EyeOff size={16} color="#FAFAFA" /> : <Eye size={16} color="#FAFAFA" />}
                </button>
              </div>
              <div className="flex gap-3">
                <input data-testid="self-age-input" type="number" min="14" max="99" placeholder="Age" value={form.age} onChange={e => u('age', e.target.value)} className={inputClass} style={{ ...inputStyle, flex: '0 0 100px' }} />
                {badge && (
                  <div className="flex items-center gap-2 flex-1 px-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
                    <span className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full" style={{ fontFamily: 'JetBrains Mono, monospace', background: badge.color, color: '#050505' }}>{badge.label}</span>
                  </div>
                )}
              </div>

              {/* Country */}
              <div className="relative">
                <button data-testid="self-country-selector" onClick={() => setShowCountryDrop(!showCountryDrop)}
                  className={`${inputClass} text-left flex items-center justify-between`} style={inputStyle}>
                  <span style={{ opacity: form.country ? 1 : 0.3 }}>
                    {selectedCountry ? `${selectedCountry.flag_emoji} ${selectedCountry.country_name}` : 'Select country'}
                  </span>
                  <ChevronDown size={16} style={{ color: 'rgba(250,250,250,0.3)' }} />
                </button>
                {showCountryDrop && (
                  <div className="absolute left-0 right-0 mt-1 rounded-xl overflow-hidden z-20 max-h-48 overflow-y-auto"
                    style={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.12)', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
                    {countries.map(c => (
                      <button key={c.country_code} data-testid={`self-country-${c.country_code}`} onClick={() => selectCountry(c)}
                        className="w-full text-left px-4 py-2.5 text-sm flex items-center gap-2 hover:bg-white/5"
                        style={{ fontFamily: 'Outfit, sans-serif', color: c.country_name === form.country ? '#CCFF00' : '#FAFAFA' }}>
                        <span>{c.flag_emoji}</span><span>{c.country_name}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {cities.length > 0 && (
                <select data-testid="self-city-select" value={form.city} onChange={e => u('city', e.target.value)}
                  className={inputClass} style={{ ...inputStyle, appearance: 'none' }}>
                  <option value="">Select city (optional)</option>
                  {cities.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              )}
            </div>

            <div className="mt-auto">
              <button data-testid="flow-b-step1-next" onClick={() => setStep(2)} disabled={!canStep1}
                className={btnPrimary} style={{ background: canStep1 ? '#CCFF00' : 'rgba(204,255,0,0.15)', color: '#050505', fontFamily: 'Syne, sans-serif', opacity: canStep1 ? 1 : 0.4 }}>
                Next: Pick your identity <ArrowRight size={18} />
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 2: Username + Avatar */}
        {step === 2 && (
          <motion.div key="b2" {...slideIn} className="flex-1 flex flex-col">
            <h2 className="text-2xl font-bold mb-1" style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}>Your identity</h2>
            <p className="text-sm opacity-40 mb-6" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>Choose a username and avatar.</p>

            {/* Username */}
            <div className="relative mb-4">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-base opacity-30" style={{ color: '#FAFAFA', fontFamily: 'JetBrains Mono, monospace' }}>@</span>
              <input data-testid="self-username-input" placeholder="username" value={form.username}
                onChange={e => u('username', e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
                className={inputClass} style={{ ...inputStyle, paddingLeft: '2.5rem', fontFamily: 'JetBrains Mono, monospace' }} />
              {usernameStatus && (
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-bold" style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  color: usernameStatus === 'available' ? '#39FF14' : usernameStatus === 'taken' ? '#FF2A6D' : 'rgba(250,250,250,0.3)',
                }}>
                  {usernameStatus === 'checking' ? '...' : usernameStatus === 'available' ? 'available' : 'taken'}
                </span>
              )}
            </div>

            {/* Avatar grid */}
            <p className="text-xs font-bold tracking-wider uppercase mb-3 opacity-40" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FAFAFA' }}>CHOOSE YOUR AVATAR</p>
            <div className="grid grid-cols-4 gap-3 mb-6">
              {avatarOptions.map((av, i) => (
                <button key={av.seed} data-testid={`avatar-option-${i}`}
                  onClick={() => u('avatar_url', av.url)}
                  className="aspect-square rounded-2xl overflow-hidden transition-all"
                  style={{
                    border: form.avatar_url === av.url ? '3px solid #CCFF00' : '2px solid rgba(255,255,255,0.08)',
                    background: 'rgba(255,255,255,0.04)',
                    transform: form.avatar_url === av.url ? 'scale(1.05)' : 'scale(1)',
                  }}>
                  <img src={av.url} alt={`Avatar ${i + 1}`} className="w-full h-full" />
                </button>
              ))}
            </div>

            {/* Terms */}
            <label className="flex items-start gap-3 cursor-pointer mb-6" onClick={() => u('consent_terms', !form.consent_terms)}>
              <div data-testid="self-consent-terms" className="w-5 h-5 rounded-md flex-shrink-0 flex items-center justify-center mt-0.5"
                style={{ background: form.consent_terms ? '#CCFF00' : 'transparent', border: form.consent_terms ? 'none' : '1px solid rgba(255,255,255,0.2)' }}>
                {form.consent_terms && <Check size={13} color="#050505" strokeWidth={3} />}
              </div>
              <span className="text-xs" style={{ fontFamily: 'Outfit, sans-serif', color: 'rgba(250,250,250,0.6)' }}>I agree to The Drop's Terms of Service and Privacy Policy.</span>
            </label>

            <div className="mt-auto">
              <button data-testid="flow-b-submit" onClick={handleSubmit} disabled={!canStep2 || loading}
                className={btnPrimary} style={{ background: canStep2 ? '#CCFF00' : 'rgba(204,255,0,0.15)', color: '#050505', fontFamily: 'Syne, sans-serif', opacity: canStep2 ? 1 : 0.4 }}>
                {loading ? 'Creating account...' : "Let's go"} {!loading && <Sparkles size={18} />}
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Welcome Screen */}
        {step === 3 && (
          <motion.div key="b3" {...slideIn} className="flex-1 flex flex-col items-center justify-center text-center">
            <motion.div initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.1, type: 'spring' }}
              className="w-24 h-24 rounded-full overflow-hidden mb-6 border-4" style={{ borderColor: '#CCFF00' }}>
              {form.avatar_url && <img src={form.avatar_url} alt="Avatar" className="w-full h-full" />}
            </motion.div>

            <motion.h1 initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}
              className="text-3xl font-bold mb-2" style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}>
              You're in.
            </motion.h1>
            <motion.p initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}
              className="text-lg mb-8 opacity-60" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>
              The Drop is live.
            </motion.p>

            {/* Top 3 stories preview */}
            {topArticles.length > 0 && (
              <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4 }}
                className="w-full mb-8">
                <p className="text-xs font-bold tracking-wider uppercase mb-3 opacity-40" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FAFAFA' }}>TODAY'S TOP STORIES</p>
                <div className="space-y-2">
                  {topArticles.map((a, i) => (
                    <div key={a.id} className="px-4 py-3 rounded-xl text-left" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
                      <p className="text-sm font-medium" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>
                        {a.rewrite?.title || a.original_title}
                      </p>
                      <p className="text-xs opacity-40 mt-1" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FAFAFA' }}>{a.source}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.5 }}
              className="w-full space-y-3">
              <button data-testid="welcome-go-to-feed" onClick={() => navigate('/feed')}
                className={btnPrimary} style={{ background: '#CCFF00', color: '#050505', fontFamily: 'Syne, sans-serif' }}>
                Start Reading <ArrowRight size={18} />
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ━━━━━━━━━━━━━━━━━━━ LOGIN FORM ━━━━━━━━━━━━━━━━━━━
function LoginForm({ setPhase, setToken, setUserData, navigate, error, setError }) {
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    if (!email || !password) { setError('Enter email and password'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${BACKEND_URL}/api/auth/login`, { email, password });
      setToken(res.data.token);
      setUserData(res.data.user);
      navigate('/feed');
    } catch (e) {
      setError(e.response?.data?.detail || 'Login failed');
    }
    setLoading(false);
  };

  return (
    <motion.div {...slideIn} className="flex-1 flex flex-col justify-center">
      <div className="flex items-center gap-3 mb-6">
        <button data-testid="login-back" onClick={() => setPhase('gate')}
          className="p-2 rounded-xl" style={{ background: 'rgba(255,255,255,0.06)' }}>
          <ArrowLeft size={18} color="#FAFAFA" />
        </button>
        <span className="text-xs font-bold tracking-[0.2em] uppercase" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#CCFF00' }}>
          LOG IN
        </span>
      </div>

      <h2 className="text-3xl font-bold mb-2" style={{ fontFamily: 'Syne, sans-serif', color: '#FAFAFA' }}>Welcome back</h2>
      <p className="text-sm opacity-40 mb-8" style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>Pick up where you left off.</p>

      {error && <div data-testid="auth-error" className="mb-4 px-4 py-3 rounded-xl text-sm" style={{ background: 'rgba(255,42,109,0.1)', border: '1px solid rgba(255,42,109,0.2)', color: '#FF2A6D', fontFamily: 'Outfit, sans-serif' }}>{error}</div>}

      <div className="space-y-3 mb-8">
        <div className="relative">
          <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 opacity-30" color="#FAFAFA" />
          <input data-testid="login-email" type="email" placeholder="Email" value={email} onChange={e => { setEmail(e.target.value); setError(''); }}
            className={inputClass} style={{ ...inputStyle, paddingLeft: '2.8rem' }} />
        </div>
        <div className="relative">
          <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 opacity-30" color="#FAFAFA" />
          <input data-testid="login-password" type={showPass ? 'text' : 'password'} placeholder="Password" value={password}
            onChange={e => { setPassword(e.target.value); setError(''); }}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
            className={inputClass} style={{ ...inputStyle, paddingLeft: '2.8rem', paddingRight: '3rem' }} />
          <button onClick={() => setShowPass(!showPass)} className="absolute right-4 top-1/2 -translate-y-1/2 opacity-40">
            {showPass ? <EyeOff size={16} color="#FAFAFA" /> : <Eye size={16} color="#FAFAFA" />}
          </button>
        </div>
      </div>

      <button data-testid="login-submit-btn" onClick={handleLogin} disabled={loading}
        className={btnPrimary} style={{ background: '#CCFF00', color: '#050505', fontFamily: 'Syne, sans-serif' }}>
        {loading ? 'Logging in...' : 'Log In'} {!loading && <ArrowRight size={18} />}
      </button>

      <button onClick={() => setPhase('gate')} className="mt-6 text-sm opacity-50 hover:opacity-80 transition-opacity text-center"
        style={{ fontFamily: 'Outfit, sans-serif', color: '#FAFAFA' }}>
        Don't have an account? <span style={{ color: '#CCFF00' }}>Sign up</span>
      </button>
    </motion.div>
  );
}
