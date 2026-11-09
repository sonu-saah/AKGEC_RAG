
import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  GraduationCap, Plus, Send, Menu, X, LoaderCircle,
  ExternalLink, MessageSquare, Moon, Sun, Copy, Check,
  RefreshCw, Mic, MicOff, Volume2, VolumeX, Trash2,
  Pencil, Sparkles
} from 'lucide-react'

const API_URL = 'http://127.0.0.1:8000/chat'
const CHAT_KEY = 'akgec-chats-v2'
const THEME_KEY = 'akgec-theme-v2'

const createChat = () => ({
  id: crypto.randomUUID(),
  title: 'New chat',
  messages: []
})

const suggestions = [
  'Which B.Tech branches are offered at AKGEC?',
  'When do first-year B.Tech classes start?',
  'What is the first-year B.Tech fee?',
  'How many placement offers were made in 2026?'
]

function App() {
  const [chats, setChats] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(CHAT_KEY))
      return Array.isArray(saved) ? saved : []
    } catch {
      return []
    }
  })
  const [activeId, setActiveId] = useState(() => localStorage.getItem(`${CHAT_KEY}-active`))
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [theme, setTheme] = useState(
    () => localStorage.getItem(THEME_KEY) || 'light'
  )
  const [listening, setListening] = useState(false)
  const [speakingId, setSpeakingId] = useState(null)
  const [copiedId, setCopiedId] = useState(null)
  const [error, setError] = useState('')

  const bottomRef = useRef(null)
  const recognitionRef = useRef(null)
  const loadingRef = useRef(false)
  const activeIdRef = useRef(activeId)

  const activeChat = chats.find(chat => chat.id === activeId)
  const messages = activeChat?.messages || []
  const dark = theme === 'dark'

  useEffect(() => {
    localStorage.setItem(CHAT_KEY, JSON.stringify(chats))
  }, [chats])

  useEffect(() => {
    if (activeId) localStorage.setItem(`${CHAT_KEY}-active`, activeId)
    else localStorage.removeItem(`${CHAT_KEY}-active`)
  }, [activeId])

  useEffect(() => {
    localStorage.setItem(THEME_KEY, theme)
    document.documentElement.classList.toggle('dark', dark)
  }, [theme, dark])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort()
      window.speechSynthesis?.cancel()
    }
  }, [])

  const updateChat = (id, updater) => {
    setChats(previous =>
      previous.map(chat => chat.id === id ? updater(chat) : chat)
    )
  }

  const stopSpeaking = () => {
    window.speechSynthesis?.cancel()
    setSpeakingId(null)
  }

  const newChat = () => {
    if (loadingRef.current) return
    stopSpeaking()
    recognitionRef.current?.stop()
    const chat = createChat()
    activeIdRef.current = chat.id
    setChats(previous => [chat, ...previous])
    setActiveId(chat.id)
    setInput('')
    setSidebarOpen(false)
  }

  const selectChat = id => {
    if (loadingRef.current) return
    stopSpeaking()
    recognitionRef.current?.stop()
    activeIdRef.current = id
    setActiveId(id)
    setSidebarOpen(false)
  }

  const deleteChat = id => {
    if (loadingRef.current) return
    stopSpeaking()
    setChats(previous => previous.filter(chat => chat.id !== id))
    if (activeIdRef.current === id) {
      activeIdRef.current = null
      setActiveId(null)
    }
  }

  const renameChat = id => {
    const chat = chats.find(item => item.id === id)
    if (!chat) return
    const title = window.prompt('Rename conversation', chat.title)
    if (title?.trim()) {
      updateChat(id, current => ({ ...current, title: title.trim() }))
    }
  }

  const askQuestion = async (question, regenerate = false) => {
    if (!question.trim() || loadingRef.current) return

    loadingRef.current = true
    setLoading(true)
    setError('')
    stopSpeaking()
    recognitionRef.current?.stop()

    let chatId = activeIdRef.current

    if (!chatId) {
      const chat = createChat()
      chatId = chat.id
      activeIdRef.current = chatId
      setActiveId(chatId)
      setChats(previous => [chat, ...previous])
    }

    updateChat(chatId, chat => ({
      ...chat,
      title: chat.messages.length === 0 ? question.slice(0, 42) : chat.title,
      messages: regenerate
        ? chat.messages.slice(0, -1)
        : [...chat.messages, { role: 'user', content: question }]
    }))

    if (!regenerate) setInput('')

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      })

      if (!response.ok) throw new Error('Backend unavailable')
      const data = await response.json()

      updateChat(chatId, chat => ({
        ...chat,
        messages: [...chat.messages, {
          role: 'assistant',
          content: data.answer || 'No answer generated.',
          sources: data.sources || []
        }]
      }))
    } catch {
      updateChat(chatId, chat => ({
        ...chat,
        messages: [...chat.messages, {
          role: 'assistant',
          content: 'Unable to connect to the chatbot backend. Please check FastAPI.',
          sources: []
        }]
      }))
    } finally {
      loadingRef.current = false
      setLoading(false)
    }
  }

  const regenerate = index => {
    if (loadingRef.current || index !== messages.length - 1) return
    if (messages[index]?.role !== 'assistant') return
    const question = messages[index - 1]?.content
    if (question) askQuestion(question, true)
  }

  const copyAnswer = async (content, index) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedId(index)
      setTimeout(() => setCopiedId(null), 1800)
    } catch {
      setError('Clipboard access is unavailable.')
    }
  }


  // Normalize common college-name recognition mistakes.
  const normalizeVoiceText = (text) => text
    .replace(/\b(?:AKGC|AKG\s*EC|A\s*K\s*G\s*E\s*C)\b/gi, 'AKGEC')
    .replace(/\s+/g, ' ')
    .trim()

  // Rebuild from the recognition results each time: never append old results.
  const toggleMicrophone = () => {
    setError('')

    if (recognitionRef.current) {
      recognitionRef.current.stop()
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('Voice input is not supported. Try Chrome or Edge.')
      return
    }

    stopSpeaking()
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.continuous = false
    recognition.interimResults = true
    recognition.maxAlternatives = 1
    const originalInput = input.trim()

    recognition.onresult = (event) => {
      const parts = Array.from(event.results, result => result[0]?.transcript || '')
      const spokenText = normalizeVoiceText(parts.join(' '))
      setInput([originalInput, spokenText].filter(Boolean).join(' '))
    }

    recognition.onerror = (event) => {
      if (!['no-speech', 'aborted'].includes(event.error)) {
        setError(`Microphone error: ${event.error}`)
      }
    }

    recognition.onend = () => {
      if (recognitionRef.current === recognition) recognitionRef.current = null
      setListening(false)
    }

    recognitionRef.current = recognition
    try {
      recognition.start()
      setListening(true)
    } catch {
      recognitionRef.current = null
      setListening(false)
      setError('Unable to start microphone.')
    }
  }

  // Convert AI response into speech
const speakAnswer = (content, index) => {
  if (!window.speechSynthesis) {
    setError('Text-to-Speech is not supported in this browser.')
    return
  }

  // Stop if the same answer is already speaking
  if (speakingId === index) {
    stopSpeaking()
    return
  }

  stopSpeaking()
  setError('')

  // Remove Markdown symbols and source references
  const plainText = content
    .replace(/\[Source\s*\d+(?:\s*,\s*Source\s*\d+)*\]/gi, '')
    .replace(/[*_#`]/g, '')
    .trim()

  if (!plainText) return

  const utterance = new SpeechSynthesisUtterance(plainText)

  utterance.lang = 'en-IN'
  utterance.rate = 0.9
  utterance.pitch = 1
  utterance.volume = 1

  utterance.onstart = () => {
    setSpeakingId(index)
  }

  utterance.onend = () => {
    setSpeakingId(null)
  }

  utterance.onerror = (event) => {
    setSpeakingId(null)

    if (event.error !== 'canceled' && event.error !== 'interrupted') {
      setError(`Voice playback error: ${event.error}`)
    }
  }

  window.speechSynthesis.speak(utterance)
}

  const iconButton = `flex h-9 w-9 items-center justify-center rounded-xl
    transition-colors ${dark
      ? 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
      : 'text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900'}`

  return (
    <div className={`flex h-screen overflow-hidden font-sans ${
      dark ? 'bg-[#111113] text-zinc-100' : 'bg-white text-zinc-900'
    }`}>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col
        border-r transition-transform duration-300 lg:static lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        ${dark
          ? 'border-zinc-800 bg-[#18181b]'
          : 'border-zinc-200 bg-[#f8f9fb]'}`}>

        <div className="flex h-18 items-center justify-between px-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-500/20">
              <GraduationCap size={23} />
            </div>
            <div>
              <div className="text-base font-bold tracking-tight">AKGEC AI</div>
              <div className="text-[11px] text-zinc-500">College Assistant</div>
            </div>
          </div>
          <button
            className={`${iconButton} lg:hidden`}
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={19} />
          </button>
        </div>

        <div className="px-4 pt-4">
          <button
            onClick={newChat}
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-indigo-500/20 transition hover:bg-indigo-500 disabled:opacity-50"
          >
            <Plus size={18} /> New chat
          </button>
        </div>

        <div className="mt-7 flex-1 overflow-y-auto px-3">
          <div className="mb-3 px-3 text-[11px] font-semibold uppercase tracking-[0.15em] text-zinc-500">
            Recent conversations
          </div>

          {chats.length === 0 && (
            <p className="px-3 text-xs leading-6 text-zinc-500">
              Your conversations will appear here.
            </p>
          )}

          <div className="space-y-1">
            {chats.map(chat => (
              <div
                key={chat.id}
                className={`group flex items-center gap-1 rounded-xl px-2 py-1
                  ${chat.id === activeId
                    ? dark ? 'bg-zinc-800' : 'bg-indigo-50'
                    : dark ? 'hover:bg-zinc-800/70' : 'hover:bg-zinc-200/60'}`}
              >
                <button
                  onClick={() => selectChat(chat.id)}
                  disabled={loading}
                  className="flex min-w-0 flex-1 items-center gap-2.5 py-2 text-left text-sm"
                >
                  <MessageSquare size={16} className="shrink-0 text-zinc-500" />
                  <span className="truncate">{chat.title}</span>
                </button>
                <button
                  onClick={() => renameChat(chat.id)}
                  className={`${iconButton} h-7 w-7 opacity-60 hover:opacity-100`}
                  title="Rename"
                >
                  <Pencil size={13} />
                </button>
                <button
                  onClick={() => deleteChat(chat.id)}
                  className={`${iconButton} h-7 w-7 opacity-60 hover:opacity-100`}
                  title="Delete"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className={`border-t px-5 py-5 ${
          dark ? 'border-zinc-800' : 'border-zinc-200'
        }`}>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
              <Sparkles size={18} />
            </div>
            <div>
              <p className="text-xs font-semibold">Hybrid RAG + Gemini</p>
              <p className="mt-0.5 text-[11px] text-zinc-500">
                Powered by AKGEC sources
              </p>
            </div>
          </div>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className={`flex h-17 shrink-0 items-center justify-between
          border-b px-4 sm:px-7 ${
            dark ? 'border-zinc-800' : 'border-zinc-100'
          }`}>
          <div className="flex items-center gap-3">
            <button
              className={`${iconButton} lg:hidden`}
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu size={21} />
            </button>
            <div>
              <h2 className="text-sm font-semibold sm:text-base">
                AKGEC AI Assistant
              </h2>
              <p className="hidden text-[11px] text-zinc-500 sm:block">
                Your intelligent campus companion
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className={`hidden items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium sm:flex ${
              dark ? 'bg-emerald-500/10 text-emerald-400' : 'bg-emerald-50 text-emerald-700'
            }`}>
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              College Information
            </span>
            <button
              onClick={() => setTheme(dark ? 'light' : 'dark')}
              className={iconButton}
              aria-label="Toggle theme"
              title="Toggle theme"
            >
              {dark ? <Sun size={19} /> : <Moon size={19} />}
            </button>
          </div>
        </header>

        <section className="min-h-0 flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center px-5 py-10 text-center">
              <div className="mb-7 flex h-18 w-18 items-center justify-center rounded-[26px] bg-linear-to-br from-indigo-500 to-violet-600 text-white shadow-xl shadow-indigo-500/20">
                <GraduationCap size={34} />
              </div>
              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
                How can I help you today?
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-7 text-zinc-500 sm:text-base">
                Explore AKGEC courses, admissions, fees, academic calendars,
                placements and more using official college information.
              </p>

              <div className="mt-10 grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
                {suggestions.map(text => (
                  <button
                    key={text}
                    onClick={() => setInput(text)}
                    className={`rounded-2xl border p-4 text-left text-sm leading-6 transition
                      ${dark
                        ? 'border-zinc-800 bg-zinc-900 hover:border-indigo-500/50 hover:bg-zinc-800'
                        : 'border-zinc-200 bg-white shadow-sm hover:border-indigo-300 hover:bg-indigo-50/50'}`}
                  >
                    <Sparkles size={16} className="mb-3 text-indigo-500" />
                    {text}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-8 px-4 py-8 sm:px-7">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white">
                      <GraduationCap size={19} />
                    </div>
                  )}

                  <div className={`min-w-0 ${
                    message.role === 'user' ? 'max-w-[85%]' : 'flex-1'
                  }`}>
                    <div className={
                      message.role === 'user'
                        ? `rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-7 ${
                            dark ? 'bg-zinc-800' : 'bg-[#f1f2f5]'
                          }`
                        : `text-sm leading-7 ${
                            dark ? 'text-zinc-200' : 'text-zinc-800'
                          }`
                    }>
                      {message.role === 'assistant' ? (
                        <div className={`wrap-break-word [&_p]:mb-3 [&_ul]:mb-3 [&_ul]:list-disc [&_ul]:pl-6 [&_ol]:mb-3 [&_ol]:list-decimal [&_ol]:pl-6 [&_li]:mb-1 [&_strong]:font-semibold [&_h2]:mb-3 [&_h2]:text-lg [&_h2]:font-bold [&_h3]:mb-2 [&_h3]:font-semibold [&_a]:text-indigo-500 [&_a]:underline [&_table]:block [&_table]:overflow-x-auto [&_th]:border [&_th]:p-2 [&_td]:border [&_td]:p-2 ${
                          dark ? '[&_th]:border-zinc-700 [&_td]:border-zinc-700' : '[&_th]:border-zinc-200 [&_td]:border-zinc-200'
                        }`}>
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content.replace(/\\\*/g, '*')}
                          </ReactMarkdown>
                        </div>
                      ) : message.content}
                    </div>

                    {message.sources?.length > 0 && (
                      <div className={`mt-4 rounded-xl border p-3 ${
                        dark ? 'border-zinc-800 bg-zinc-900' : 'border-zinc-200 bg-zinc-50'
                      }`}>
                        <p className="mb-2 text-xs font-semibold">
                          Official sources
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {message.sources.map((url, i) => (
                            <a
                              key={i}
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs transition ${
                                dark
                                  ? 'border-zinc-700 text-indigo-300 hover:bg-zinc-800'
                                  : 'border-indigo-100 bg-white text-indigo-600 hover:bg-indigo-50'
                              }`}
                            >
                              <ExternalLink size={12} /> Source {i + 1}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {message.role === 'assistant' && (
                      <div className="mt-3 flex items-center gap-1">
                        <button
                          onClick={() => copyAnswer(message.content, index)}
                          className={iconButton}
                          title="Copy answer"
                        >
                          {copiedId === index
                            ? <Check size={16} />
                            : <Copy size={16} />}
                        </button>
                        <button
                          onClick={() => speakAnswer(message.content, index)}
                          className={iconButton}
                          title={speakingId === index ? 'Stop voice' : 'Read aloud'}
                        >
                          {speakingId === index
                            ? <VolumeX size={17} />
                            : <Volume2 size={17} />}
                        </button>
                        {index === messages.length - 1 && (
                          <button
                            onClick={() => regenerate(index)}
                            disabled={loading}
                            className={iconButton}
                            title="Regenerate"
                          >
                            <RefreshCw size={16} />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex items-center gap-3 text-sm text-zinc-500">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white">
                    <GraduationCap size={19} />
                  </div>
                  <LoaderCircle size={17} className="animate-spin" />
                  Searching official AKGEC information...
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </section>

        <div className="shrink-0 px-4 pb-4 pt-2 sm:px-7">
          <div className="mx-auto max-w-3xl">
            {error && (
              <p className="mb-2 text-xs text-red-500">{error}</p>
            )}

            <form
              onSubmit={event => {
                event.preventDefault()
                askQuestion(input.trim())
              }}
              className={`rounded-2xl border p-3 shadow-lg ${
                dark
                  ? 'border-zinc-700 bg-zinc-900 shadow-black/20'
                  : 'border-zinc-200 bg-white shadow-zinc-200/50'
              }`}
            >
              <textarea
                value={input}
                onChange={event => setInput(event.target.value)}
                onKeyDown={event => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    if (!loading && input.trim()) {
                      event.currentTarget.form.requestSubmit()
                    }
                  }
                }}
                placeholder="Ask anything about AKGEC..."
                rows={2}
                disabled={loading}
                className="w-full resize-none bg-transparent px-2 py-1 text-sm leading-6 outline-none placeholder:text-zinc-500 disabled:opacity-60"
              />

              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={toggleMicrophone}
                    className={`flex h-10 w-10 items-center justify-center rounded-xl transition ${
                      listening
                        ? 'animate-pulse bg-red-500 text-white'
                        : dark
                          ? 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
                          : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
                    }`}
                    title={listening ? 'Stop microphone' : 'Voice input'}
                  >
                    {listening ? <MicOff size={19} /> : <Mic size={19} />}
                  </button>
                  <span className="text-xs text-zinc-500">
                    {listening ? 'Listening...' : 'Voice input'}
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={!input.trim() || loading}
                  className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
                  title="Send message"
                >
                  {loading
                    ? <LoaderCircle size={19} className="animate-spin" />
                    : <Send size={19} />}
                </button>
              </div>
            </form>

            <p className="mt-3 text-center text-[11px] leading-5 text-zinc-500">
              AKGEC AI can make mistakes. Verify important details with official college sources.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
