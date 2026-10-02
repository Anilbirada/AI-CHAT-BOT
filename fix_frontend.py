from pathlib import Path

path = Path(r'E:\dse ai\dsce-ai-academic-assistant\frontend\src\main.tsx')
content = """import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Bot,
  BookOpen,
  ChevronDown,
  FileText,
  LayoutDashboard,
  Menu,
  MessageSquare,
  Plus,
  Send,
  Settings,
  Sparkles,
  UploadCloud,
  UserRound,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './index.css';

const API = 'http://localhost:8000';

type Msg = {
  role: 'user' | 'assistant';
  content: string;
  sources?: { filename: string; page: number | null }[];
};

type Conversation = {
  id: number;
  title: string;
  updated_at: string;
};

type AuthMode = 'login' | 'register';

function App() {
  const [token, setToken] = useState<string>(localStorage.getItem('dsce_token') || '');
  const [user, setUser] = useState<{ name: string; email: string; role: string } | null>(() => {
    const raw = localStorage.getItem('dsce_user');
    return raw ? JSON.parse(raw) : null;
  });
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [authBusy, setAuthBusy] = useState(false);
  const [status, setStatus] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const [subject, setSubject] = useState('All Subjects');
  const [semester, setSemester] = useState('4');
  const [mode, setMode] = useState('Simple Explanation');
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'STUDENT' });

  useEffect(() => {
    if (!token) {
      setMessages([]);
      setConversations([]);
      setCurrentConversationId(null);
      return;
    }
    void loadConversationList();
  }, [token]);

  async function loadConversationList() {
    try {
      const response = await fetch(`${API}/api/chats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return;
      const data = await response.json();
      const list = Array.isArray(data) ? data : [];
      setConversations(list);
      if (!currentConversationId && list.length > 0) {
        await openConversation(list[0].id);
      }
    } catch {
      setConversations([]);
    }
  }

  async function openConversation(id: number) {
    setCurrentConversationId(id);
    try {
      const response = await fetch(`${API}/api/chats/${id}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return;
      const history = await response.json();
      setMessages(Array.isArray(history) ? history.map((item: any) => ({
        role: item.role,
        content: item.content,
        sources: item.sources || [],
      })) : []);
    } catch {
      setMessages([]);
    }
  }

  async function handleAuth() {
    if (!form.email || !form.password || (authMode === 'register' && !form.name.trim())) {
      setStatus('Please complete all required details.');
      return;
    }

    setAuthBusy(true);
    setStatus('');

    try {
      const endpoint = authMode === 'register' ? '/api/auth/register' : '/api/auth/login';
      const payload = authMode === 'register'
        ? { name: form.name, email: form.email, password: form.password, role: form.role }
        : { email: form.email, password: form.password };

      const response = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Authentication failed.');
      }

      const nextToken = data.access_token || data.token;
      if (!nextToken) {
        throw new Error('No access token was returned by the backend.');
      }

      const nextUser = data.user || {
        name: form.name || 'DSCE User',
        email: form.email,
        role: form.role || 'STUDENT',
      };

      setToken(nextToken);
      setUser(nextUser);
      localStorage.setItem('dsce_token', nextToken);
      localStorage.setItem('dsce_user', JSON.stringify(nextUser));
      setForm({ name: '', email: '', password: '', role: 'STUDENT' });
    } catch (error: any) {
      setStatus(error.message || 'Authentication failed.');
    } finally {
      setAuthBusy(false);
    }
  }

  async function sendMessage() {
    if (!message.trim() || busy || !token) {
      if (!token) setStatus('Please log in before sending a message.');
      return;
    }

    const trimmed = message.trim();
    setMessage('');
    setMessages((current) => [...current, { role: 'user', content: trimmed }]);
    setBusy(true);
    setStatus('');

    try {
      const response = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          conversation_id: currentConversationId,
          message: trimmed,
          subject: subject === 'All Subjects' ? null : subject,
          semester: Number(semester),
          mode,
        }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Unable to process your request.');
      }

      const answer = data.answer || 'I could not generate a response.';
      const assistantAnswer = { role: 'assistant' as const, content: answer, sources: data.sources || [] };
      setMessages((current) => [...current, assistantAnswer]);
      setCurrentConversationId(data.conversation_id || currentConversationId);
      await loadConversationList();
    } catch (error: any) {
      setMessages((current) => [...current, {
        role: 'assistant',
        content: error.message || 'AI service is temporarily unavailable. Please try again.',
      }]);
    } finally {
      setBusy(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem('dsce_token');
    localStorage.removeItem('dsce_user');
    setToken('');
    setUser(null);
    setMessages([]);
    setConversations([]);
    setCurrentConversationId(null);
    setStatus('');
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-[#050b16] text-slate-100 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-5xl grid md:grid-cols-2 gap-6">
          <div className="rounded-3xl border border-white/10 bg-[#0b1220] p-8 shadow-2xl shadow-indigo-950/30">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#5f7cff] to-[#7c4dff] grid place-items-center">
                <Bot size={24} />
              </div>
              <div>
                <div className="text-xl font-bold">DSCE AI</div>
                <div className="text-xs text-slate-400">Academic Assistant</div>
              </div>
            </div>

            <div className="text-xs uppercase tracking-[0.25em] text-blue-300 mb-4">Dayananda Sagar College of Engineering</div>
            <h1 className="text-4xl font-bold leading-tight">Study smarter with your campus AI.</h1>
            <p className="mt-4 text-slate-400 leading-7">
              Ask about courses, notes, debugging issues, code problems, and academic material.
            </p>

            <div className="mt-8 grid gap-3">
              {['Explain this topic simply', 'Prepare a 5-mark answer', 'Debug my code issue'].map((item) => (
                <button key={item} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm text-slate-200 hover:border-blue-400/40">
                  {item}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-[#0b1220] p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold">{authMode === 'login' ? 'Welcome back' : 'Create account'}</h2>
              <button
                className="text-sm text-blue-300"
                onClick={() => setAuthMode((value) => (value === 'login' ? 'register' : 'login'))}
              >
                {authMode === 'login' ? 'Need an account?' : 'Already have one?'}
              </button>
            </div>

            <div className="space-y-4">
              {authMode === 'register' && (
                <label className="block text-sm text-slate-300">
                  Full name
                  <input
                    className="mt-2 w-full rounded-xl border border-white/10 bg-[#131d2d] px-3 py-2.5 outline-none focus:border-blue-400"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="Jane Doe"
                  />
                </label>
              )}

              <label className="block text-sm text-slate-300">
                Email
                <input
                  type="email"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-[#131d2d] px-3 py-2.5 outline-none focus:border-blue-400"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="student@dsce.edu.in"
                />
              </label>

              <label className="block text-sm text-slate-300">
                Password
                <input
                  type="password"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-[#131d2d] px-3 py-2.5 outline-none focus:border-blue-400"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••"
                />
              </label>

              {authMode === 'register' && (
                <div className="grid grid-cols-2 gap-3">
                  <label className="text-sm text-slate-300">
                    Role
                    <select
                      className="mt-2 w-full rounded-xl border border-white/10 bg-[#131d2d] px-3 py-2.5 outline-none focus:border-blue-400"
                      value={form.role}
                      onChange={(e) => setForm({ ...form, role: e.target.value })}
                    >
                      <option>STUDENT</option>
                      <option>FACULTY</option>
                      <option>ADMIN</option>
                    </select>
                  </label>
                  <label className="text-sm text-slate-300">
                    Semester
                    <select
                      className="mt-2 w-full rounded-xl border border-white/10 bg-[#131d2d] px-3 py-2.5 outline-none focus:border-blue-400"
                      value={semester}
                      onChange={(e) => setSemester(e.target.value)}
                    >
                      {['1', '2', '3', '4', '5', '6', '7', '8'].map((option) => (
                        <option key={option}>{option}</option>
                      ))}
                    </select>
                  </label>
                </div>
              )}

              {status && (
                <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                  {status}
                </div>
              )}

              <button
                onClick={handleAuth}
                disabled={authBusy}
                className="w-full rounded-xl bg-gradient-to-r from-blue-500 to-violet-500 px-4 py-3 font-semibold text-white disabled:opacity-70"
              >
                {authBusy ? 'Please wait...' : authMode === 'login' ? 'Login' : 'Register'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex overflow-hidden bg-[#050b16] text-slate-100">
      <aside className={`${sidebarOpen ? 'w-[280px]' : 'w-0'} transition-all overflow-hidden border-r border-white/10 bg-[#080d1b] flex flex-col`}>
        <div className="p-5 flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#5f7cff] to-[#7c4dff] grid place-items-center shadow-lg shadow-blue-900/30">
            <Bot />
          </div>
          <div>
            <div className="font-bold">DSCE AI</div>
            <div className="text-xs text-slate-400">Academic Assistant</div>
          </div>
        </div>

        <div className="px-4">
          <button
            onClick={() => {
              setCurrentConversationId(null);
              setMessages([]);
            }}
            className="w-full py-3 rounded-xl bg-white text-slate-900 font-semibold flex items-center justify-center gap-2"
          >
            <Plus size={18} /> New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {conversations.length === 0 ? (
            <div className="text-sm text-slate-400">No conversations yet.</div>
          ) : (
            <div className="space-y-2">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => void openConversation(conversation.id)}
                  className={`w-full rounded-xl border px-3 py-2 text-left ${currentConversationId === conversation.id ? 'border-blue-400/40 bg-blue-500/10' : 'border-white/10 bg-white/5'}`}
                >
                  <div className="text-sm font-medium truncate">{conversation.title}</div>
                  <div className="text-[10px] uppercase tracking-wider text-slate-500 mt-1">{new Date(conversation.updated_at).toLocaleString()}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="mt-auto p-4 border-t border-white/10">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-3">Your workspace</div>
          <div className="rounded-2xl p-3 flex items-center gap-3 bg-white/5">
            <div className="w-9 h-9 rounded-full bg-indigo-500/20 grid place-items-center">
              <UserRound size={17} />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-medium truncate">{user?.name || 'DSCE User'}</div>
              <div className="text-xs text-slate-500">{user?.role || 'STUDENT'}</div>
            </div>
            <Settings className="ml-auto text-slate-500" size={17} />
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-white/10 flex items-center px-5 gap-4 bg-[#080d1b]/80 backdrop-blur-xl">
          <button onClick={() => setSidebarOpen((value) => !value)} className="p-2 rounded-lg hover:bg-white/5">
            <Menu size={20} />
          </button>
          <div className="font-semibold hidden md:block">DSCE AI Academic Assistant</div>
          <div className="ml-auto flex items-center gap-2">
            <Select value={subject} set={setSubject} opts={['All Subjects', 'Computer Science', 'Mathematics', 'Electronics', 'Mechanical']} />
            <Select value={semester} set={setSemester} opts={['1', '2', '3', '4', '5', '6', '7', '8']} />
            <Select value={mode} set={setMode} opts={['Simple Explanation', 'Detailed Notes', 'Exam Answer', 'Quick Revision']} />
            <button onClick={handleLogout} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-200">Logout</button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          {messages.length === 0 && !busy ? (
            <Welcome onPick={(text) => setMessage(text)} />
          ) : (
            <div className="space-y-4 max-w-4xl mx-auto">
              {messages.map((item, index) => (
                <div key={`${item.role}-${index}`} className={`flex ${item.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-2xl border px-4 py-3 ${item.role === 'user' ? 'bg-blue-500/15 border-blue-400/20 text-slate-100' : 'bg-white/5 border-white/10 text-slate-200'}`}>
                    <div className="prose prose-invert max-w-none text-sm leading-7 break-words">
                      <ReactMarkdown>{item.content}</ReactMarkdown>
                    </div>
                    {item.sources && item.sources.length > 0 && (
                      <div className="mt-3 space-y-1 text-xs text-slate-400">
                        {item.sources.map((source, srcIndex) => (
                          <div key={`${source.filename}-${srcIndex}`}>
                            {source.filename}{source.page ? ` · Page ${source.page}` : ''}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {busy && (
                <div className="flex justify-start">
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
                    AI is thinking…
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="border-t border-white/10 p-4 bg-[#080d1b]/80 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto relative">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={2}
              placeholder="Ask DSCE AI anything..."
              className="w-full resize-none rounded-2xl border border-white/10 bg-[#0d1424] px-4 py-3 pr-14 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-blue-400"
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void sendMessage();
                }
              }}
            />
            <button
              onClick={() => void sendMessage()}
              disabled={busy || !message.trim()}
              className="absolute right-3 bottom-3 p-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-violet-500 disabled:opacity-60"
            >
              <Send size={17} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

function Select({ value, set, opts }: { value: string; set: (x: string) => void; opts: string[] }) {
  return (
    <div className="relative hidden sm:block">
      <select
        value={value}
        onChange={(e) => set(e.target.value)}
        className="appearance-none bg-white/5 border border-white/10 rounded-xl pl-3 pr-8 py-2 text-xs text-slate-300 outline-none"
      >
        {opts.map((option) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
      <ChevronDown className="absolute right-2 top-2.5 pointer-events-none" size={14} />
    </div>
  );
}

function Welcome({ onPick }: { onPick: (x: string) => void }) {
  return (
    <div className="min-h-[65vh] flex flex-col items-center justify-center text-center px-4">
      <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-[#5f7cff] to-[#7c4dff] grid place-items-center shadow-2xl shadow-blue-900/40 mb-7">
        <Sparkles size={36} />
      </div>
      <div className="text-xs uppercase tracking-[.25em] text-blue-300 mb-3">Dayananda Sagar College of Engineering</div>
      <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
        Your Academic AI, <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-violet-300">grounded in DSCE.</span>
      </h1>
      <p className="max-w-2xl text-slate-400 mt-5 leading-7">
        Ask about subjects, syllabus, concepts, code problems, debugging, or uploaded academic documents.
      </p>
      <div className="grid md:grid-cols-3 gap-3 mt-9 w-full max-w-3xl">
        {['Explain this topic simply', 'Give me a 5-mark exam answer', 'Debug my code issue'].map((item) => (
          <button key={item} onClick={() => onPick(item)} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-blue-400/40">
            <div className="text-sm font-medium">{item}</div>
            <div className="text-xs text-slate-500 mt-1">Ask DSCE AI →</div>
          </button>
        ))}
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
""" 
path.write_text(content, encoding='utf-8')
print('updated')
