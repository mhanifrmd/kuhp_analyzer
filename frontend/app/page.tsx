'use client'

import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Send, FileText, AlertCircle, Scale, ArrowRight, MessageCircle, GitCompare, Bot, User } from 'lucide-react'

// ============ INTERFACES ============
interface PasalDetail {
  pasal: string | null
  judul: string | null
  isi: string | null
  sanksi: string | null
}

interface PasalComparison {
  topik: string
  kuhp_lama: PasalDetail | null
  kuhp_baru: PasalDetail | null
  perbedaan: string[] | null
}

interface ComparisonData {
  ringkasan: string | null
  pasal_terkait: PasalComparison[] | null
  analisis_perubahan: string | null
  kesimpulan: string | null
}

interface AnalysisResponse {
  response: string
  is_relevant: boolean
  comparison_data: ComparisonData | null
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ChatResponse {
  response: string
  is_relevant: boolean
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

// ============ COMPARISON TAB ============
function ComparisonTab() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResponse | null>(null)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!query.trim()) {
      setError('Silakan masukkan pasal atau kata kunci')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await axios.post(`${API_URL}/analyze`, {
        query: query.trim()
      })
      setResult(response.data)
    } catch (err) {
      console.error('Error:', err)
      setError('Terjadi kesalahan saat menganalisis. Silakan coba lagi.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Form */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Pasal atau Kata Kunci untuk Dibandingkan
            </label>
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Contoh: Pasal 351, pencurian, pembunuhan, dll."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          {error && (
            <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Menganalisis...</span>
              </>
            ) : (
              <>
                <GitCompare className="h-5 w-5" />
                <span>Bandingkan KUHP</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center mb-4">
              {result.is_relevant ? (
                <Scale className="h-6 w-6 text-indigo-600 mr-2" />
              ) : (
                <AlertCircle className="h-6 w-6 text-yellow-500 mr-2" />
              )}
              <h2 className="text-xl font-semibold text-gray-900">
                {result.is_relevant ? 'Perbandingan KUHP' : 'Informasi'}
              </h2>
            </div>

            {result.comparison_data?.ringkasan && (
              <div className="bg-indigo-50 border-l-4 border-indigo-500 p-4">
                <p className="text-indigo-900 font-medium">{result.comparison_data.ringkasan}</p>
              </div>
            )}
          </div>

          {/* Side-by-Side Comparison */}
          {result.comparison_data?.pasal_terkait && result.comparison_data.pasal_terkait.length > 0 && (
            <div className="space-y-6">
              {result.comparison_data.pasal_terkait.map((pasal, index) => (
                <div key={index} className="bg-white rounded-lg shadow-lg overflow-hidden">
                  <div className="bg-gray-800 text-white px-6 py-3">
                    <h3 className="text-lg font-semibold">{pasal.topik}</h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-200">
                    {/* KUHP Lama */}
                    <div className="p-6 bg-red-50">
                      <div className="flex items-center mb-4">
                        <div className="bg-red-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                          KUHP LAMA
                        </div>
                      </div>
                      {pasal.kuhp_lama ? (
                        <div className="space-y-3">
                          <div>
                            <span className="text-red-800 font-bold text-lg">{pasal.kuhp_lama.pasal}</span>
                            {pasal.kuhp_lama.judul && (
                              <span className="text-red-700 ml-2">- {pasal.kuhp_lama.judul}</span>
                            )}
                          </div>
                          <div className="bg-white rounded-lg p-4 border border-red-200">
                            <p className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
                              {pasal.kuhp_lama.isi}
                            </p>
                          </div>
                          {pasal.kuhp_lama.sanksi && (
                            <div className="bg-red-100 rounded-lg p-3">
                              <span className="text-red-800 font-medium text-sm">Sanksi: </span>
                              <span className="text-red-700 text-sm">{pasal.kuhp_lama.sanksi}</span>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-gray-500 italic">Tidak ada pasal terkait di KUHP Lama</div>
                      )}
                    </div>

                    {/* KUHP Baru */}
                    <div className="p-6 bg-green-50">
                      <div className="flex items-center mb-4">
                        <div className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                          KUHP BARU
                        </div>
                      </div>
                      {pasal.kuhp_baru ? (
                        <div className="space-y-3">
                          <div>
                            <span className="text-green-800 font-bold text-lg">{pasal.kuhp_baru.pasal}</span>
                            {pasal.kuhp_baru.judul && (
                              <span className="text-green-700 ml-2">- {pasal.kuhp_baru.judul}</span>
                            )}
                          </div>
                          <div className="bg-white rounded-lg p-4 border border-green-200">
                            <p className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">
                              {pasal.kuhp_baru.isi}
                            </p>
                          </div>
                          {pasal.kuhp_baru.sanksi && (
                            <div className="bg-green-100 rounded-lg p-3">
                              <span className="text-green-800 font-medium text-sm">Sanksi: </span>
                              <span className="text-green-700 text-sm">{pasal.kuhp_baru.sanksi}</span>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-gray-500 italic">Tidak ada pasal terkait di KUHP Baru</div>
                      )}
                    </div>
                  </div>

                  {pasal.perbedaan && pasal.perbedaan.length > 0 && (
                    <div className="bg-amber-50 px-6 py-4 border-t border-amber-200">
                      <h4 className="text-amber-800 font-semibold mb-2 flex items-center">
                        <ArrowRight className="h-4 w-4 mr-2" />
                        Perbedaan Utama:
                      </h4>
                      <ul className="list-disc list-inside space-y-1">
                        {pasal.perbedaan.map((diff, idx) => (
                          <li key={idx} className="text-amber-900 text-sm">{diff}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Analisis & Kesimpulan */}
          {(result.comparison_data?.analisis_perubahan || result.comparison_data?.kesimpulan) && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              {result.comparison_data?.analisis_perubahan && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Analisis Perubahan</h3>
                  <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {result.comparison_data.analisis_perubahan}
                  </p>
                </div>
              )}
              {result.comparison_data?.kesimpulan && (
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
                  <h3 className="text-blue-900 font-semibold mb-2">Kesimpulan</h3>
                  <p className="text-blue-800">{result.comparison_data.kesimpulan}</p>
                </div>
              )}
            </div>
          )}

          {/* Fallback */}
          {!result.comparison_data && result.is_relevant && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                {result.response}
              </div>
            </div>
          )}

          {!result.is_relevant && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                {result.response}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ============ CHATBOT TAB ============
function ChatbotTab() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!message.trim()) return

    const userMessage = message.trim()
    setMessage('')
    setError('')

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await axios.post<ChatResponse>(`${API_URL}/chat`, {
        message: userMessage
      })

      // Add assistant response
      setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }])
    } catch (err) {
      console.error('Error:', err)
      setError('Terjadi kesalahan. Silakan coba lagi.')
      // Remove the user message if error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden flex flex-col" style={{ height: '600px' }}>
      {/* Chat Header */}
      <div className="bg-indigo-600 text-white px-6 py-4">
        <div className="flex items-center">
          <Bot className="h-6 w-6 mr-2" />
          <div>
            <h2 className="font-semibold">KUHP Assistant</h2>
            <p className="text-indigo-200 text-sm">Tanya apa saja tentang KUHP lama dan baru</p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium">Mulai percakapan</p>
            <p className="text-sm mt-2">Tanyakan tentang pasal-pasal KUHP, sanksi pidana, atau perbedaan KUHP lama dan baru</p>
            <div className="mt-4 space-y-2">
              <p className="text-xs text-gray-400">Contoh pertanyaan:</p>
              <div className="flex flex-wrap justify-center gap-2">
                {['Apa itu KUHP?', 'Jelaskan pasal pencurian', 'Sanksi pembunuhan'].map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setMessage(q)}
                    className="text-xs bg-white border border-gray-200 px-3 py-1 rounded-full hover:bg-indigo-50 hover:border-indigo-300"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex items-start max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                msg.role === 'user' ? 'bg-indigo-600 ml-2' : 'bg-gray-600 mr-2'
              }`}>
                {msg.role === 'user' ? (
                  <User className="h-4 w-4 text-white" />
                ) : (
                  <Bot className="h-4 w-4 text-white" />
                )}
              </div>
              <div className={`rounded-lg px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-800'
              }`}>
                {msg.role === 'user' ? (
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                ) : (
                  <div className="text-sm leading-relaxed prose prose-sm max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-strong:text-gray-900 prose-blockquote:border-indigo-500 prose-blockquote:bg-indigo-50 prose-blockquote:py-1 prose-blockquote:px-3 prose-blockquote:my-2">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 mr-2 flex items-center justify-center">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ketik pertanyaan tentang KUHP..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !message.trim()}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  )
}

// ============ MAIN COMPONENT ============
export default function Home() {
  const [activeTab, setActiveTab] = useState<'comparison' | 'chatbot'>('comparison')

  useEffect(() => {
    console.log('API URL:', API_URL)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <FileText className="h-12 w-12 text-indigo-600 mr-3" />
              <h1 className="text-4xl font-bold text-gray-900">
                KUHP Analyzer
              </h1>
            </div>
            <p className="text-xl text-gray-600">
              Analisis Perbedaan KUHP Lama dan Baru dengan AI
            </p>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow-lg mb-6 p-1">
            <div className="flex">
              <button
                onClick={() => setActiveTab('comparison')}
                className={`flex-1 flex items-center justify-center py-3 px-4 rounded-lg font-medium transition-colors ${
                  activeTab === 'comparison'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <GitCompare className="h-5 w-5 mr-2" />
                Perbandingan Pasal
              </button>
              <button
                onClick={() => setActiveTab('chatbot')}
                className={`flex-1 flex items-center justify-center py-3 px-4 rounded-lg font-medium transition-colors ${
                  activeTab === 'chatbot'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <MessageCircle className="h-5 w-5 mr-2" />
                Chatbot KUHP
              </button>
            </div>
          </div>

          {/* Tab Content */}
          {activeTab === 'comparison' ? <ComparisonTab /> : <ChatbotTab />}
        </div>
      </div>

      <footer className="mt-12 text-center text-gray-500 text-sm pb-8">
        <p>© 2025 KUHP Analyzer - Powered by Google Gemini AI</p>
      </footer>
    </div>
  )
}
