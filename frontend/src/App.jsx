import { useState } from 'react'
import { GraduationCap, Plus, Send, Menu, X, LoaderCircle, ExternalLink, MessageSquare } from 'lucide-react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000/chat'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const newChat = () => {
    if (loading) return
    setMessages([])
    setInput('')
    setSidebarOpen(false)
  }

  const sendMessage = async (event) => {
    event.preventDefault()
    const question = input.trim()
    if (!question || loading) return

    setMessages(prev => [...prev, { role: 'user', content: question }])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      })

      if (!response.ok) throw new Error('Backend request failed')

      const data = await response.json()

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || []
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Unable to connect to the chatbot backend. Please check that FastAPI is running.',
        sources: []
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      {sidebarOpen && <div className="overlay" onClick={() => setSidebarOpen(false)} />}

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-top">
          <div className="brand"><GraduationCap size={25} /> <span>AKGEC AI</span></div>
          <button className="mobile-close icon-button" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar"><X size={20} /></button>
        </div>

        <button className="new-chat" onClick={newChat} disabled={loading}>
          <Plus size={19} /> New chat
        </button>

        <div className="sidebar-section">
          <span className="section-label">Your conversation</span>
          <div className="history-item"><MessageSquare size={17} /> Current chat</div>
        </div>

        <div className="sidebar-bottom">AKGEC AI Assistant<br /><small>Powered by Hybrid RAG + Gemini</small></div>
      </aside>

      <main className="main">
        <header className="header">
          <div className="header-left">
            <button className="icon-button menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open menu"><Menu size={22} /></button>
            <span>AKGEC AI Assistant</span>
          </div>
          <span className="header-tag">College Information</span>
        </header>

        <section className="conversation">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon"><GraduationCap size={32} /></div>
              <h1>How can I help you today?</h1>
              <p>Ask me about AKGEC courses, fees, academic calendars, admissions and placements.</p>
              <div className="suggestions">
                {[
                  'Which B.Tech branches are offered?',
                  'When do first-year classes start?',
                  'What is the B.Tech first-year fee?',
                  'How many placement offers were made in 2026?'
                ].map(text => (
                  <button key={text} onClick={() => setInput(text)}>{text}</button>
                ))}
              </div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  {message.role === 'assistant' && <div className="assistant-avatar"><GraduationCap size={19} /></div>}
                  <div className="message-body">
                    <div className="message-text">{message.content}</div>
                    {message.sources?.length > 0 && (
                      <div className="sources">
                        <strong>Official sources</strong>
                        {message.sources.map((url, i) => (
                          <a key={i} href={url} target="_blank" rel="noopener noreferrer">
                            <ExternalLink size={13} /> Source {i + 1}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message assistant">
                  <div className="assistant-avatar"><GraduationCap size={19} /></div>
                  <div className="message-body loading"><LoaderCircle size={19} className="spin" /> Searching official AKGEC information...</div>
                </div>
              )}
            </div>
          )}
        </section>

        <div className="composer-area">
          <form className="composer" onSubmit={sendMessage}>
            <textarea
              value={input}
              onChange={event => setInput(event.target.value)}
              onKeyDown={event => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  if (!loading && input.trim()) event.currentTarget.form.requestSubmit()
                }
              }}
              placeholder="Ask anything about AKGEC..."
              rows={2}
              disabled={loading}
            />
            <button type="submit" disabled={!input.trim() || loading} aria-label="Send message">
              {loading ? <LoaderCircle size={19} className="spin" /> : <Send size={19} />}
            </button>
          </form>
          <p className="disclaimer">Answers are generated from retrieved AKGEC sources. Verify important details with the college.</p>
        </div>
      </main>
    </div>
  )
}

export default App
