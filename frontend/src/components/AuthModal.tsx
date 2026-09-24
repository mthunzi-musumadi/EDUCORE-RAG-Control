import React, { useState } from 'react';
import { ApiService } from '../services/api';
import { AuthService } from '../services/auth';
import { User } from '../types';
import { Shield, Lock, Mail, User as UserIcon, Building2, AlertCircle, Eye, EyeOff } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose?: () => void;
  onSuccess: (user: User) => void;
}

const DEMO_ACCOUNTS = [
  { label: 'Admin', email: 'admin@localhost', password: 'admin123', tier: 'Executive' },
  { label: 'Faculty', email: 'teacher-s@sentinel-kabitaka.com', password: 'password123', tier: 'Staff' },
  { label: 'Student', email: 'student@trident-college.com', password: 'password123', tier: 'Public' },
  { label: 'Counselor', email: 'counselor@sentinel-kabitaka.com', password: 'password123', tier: 'Pastoral' },
  { label: 'Finance', email: 'financialcoordinator@educoreservices.com', password: 'password123', tier: 'Finance' },
];

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [campus, setCampus] = useState('all');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'signin') {
        const resp = await ApiService.signIn(email, password);
        AuthService.setToken(resp.token);
        AuthService.setUser(resp.user);
        onSuccess(resp.user);
      } else {
        const resp = await ApiService.signUp(name, email, password, campus);
        AuthService.setToken(resp.token);
        AuthService.setUser(resp.user);
        onSuccess(resp.user);
      }
      if (onClose) onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (acc: typeof DEMO_ACCOUNTS[0]) => {
    setEmail(acc.email);
    setPassword(acc.password);
    setError(null);
    setLoading(true);

    try {
      const resp = await ApiService.signIn(acc.email, acc.password);
      AuthService.setToken(resp.token);
      AuthService.setUser(resp.user);
      onSuccess(resp.user);
      if (onClose) onClose();
    } catch (err: any) {
      setError(err.message || 'Demo sign in failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-card border border-border rounded-2xl shadow-2xl p-6 sm:p-8 animate-in fade-in duration-200">
        {/* Header with Institutional Branding */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="relative mb-3">
            <img 
              src="/educore-rag-e.png" 
              alt="Educore" 
              className="h-12 w-12 object-contain"
              onError={(e) => {
                // fallback to colored badge if image missing
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
            <div className="absolute -bottom-1 -right-1 bg-background rounded-full p-0.5 border border-border">
              <Shield className="h-4 w-4 text-foreground/70" />
            </div>
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-foreground">
            Educore Enterprise RAG
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Governed Institutional Knowledge | ISO/IEC 42001
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-lg bg-muted p-1 mb-5">
          <button
            type="button"
            onClick={() => { setMode('signin'); setError(null); }}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
              mode === 'signin' 
                ? 'bg-background text-foreground shadow-sm' 
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setMode('signup'); setError(null); }}
            className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
              mode === 'signup' 
                ? 'bg-background text-foreground shadow-sm' 
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2 text-xs text-red-500">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-medium text-foreground mb-1">Full Name</label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Dr. Mwape Phiri"
                  className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-foreground transition"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-foreground mb-1">Institutional Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@educore.ac.zm"
                className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-foreground transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-foreground mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-10 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-foreground transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-medium text-foreground mb-1">Campus Affiliation</label>
              <div className="relative">
                <Building2 className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <select
                  value={campus}
                  onChange={(e) => setCampus(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-foreground transition appearance-none"
                >
                  <option value="all">Global / Central Services</option>
                  <option value="SKAB S">Sentinel Kabitaka Secondary</option>
                  <option value="SKAB P">Sentinel Kabitaka Primary</option>
                  <option value="TCL">Trident College Solwezi</option>
                  <option value="TPS">Trident Prep Solwezi</option>
                  <option value="TPK">Trident Prep Kalumbila</option>
                  <option value="TPL">Trident Prep Lusaka</option>
                  <option value="SKAL">Sentinel Kalumbila</option>
                  <option value="Frontier Nkisu">Frontier Nkisu</option>
                </select>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2 px-4 bg-foreground text-background font-medium text-sm rounded-lg hover:opacity-90 active:scale-[0.99] transition disabled:opacity-50 flex items-center justify-center"
          >
            {loading ? (
              <span className="inline-block h-4 w-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
            ) : mode === 'signin' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        {/* Quick Demo Login Pills for Testing */}
        <div className="mt-6 pt-5 border-t border-border">
          <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-2.5 text-center">
            Institutional Seed Accounts (1-Click Test)
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.label}
                type="button"
                onClick={() => handleDemoLogin(acc)}
                className="py-1.5 px-2 bg-muted/60 hover:bg-muted text-foreground border border-border/60 rounded-md text-xs font-medium text-left flex flex-col transition"
              >
                <span className="font-semibold text-[11px]">{acc.label}</span>
                <span className="text-[9px] text-muted-foreground truncate">{acc.tier}</span>
              </button>
            ))}
          </div>
        </div>

        {onClose && (
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={onClose}
              className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2"
            >
              Continue as Guest (Public Clearance)
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
