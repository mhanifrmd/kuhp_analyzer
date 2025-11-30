'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { Send, FileText, AlertCircle, CheckCircle } from 'lucide-react'

interface AnalysisResponse {
  response: string
  is_relevant: boolean
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

export default function Home() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResponse | null>(null)
  const [error, setError] = useState('')

  // Log API URL untuk debugging
  useEffect(() => {
    console.log('Environment API URL:', process.env.NEXT_PUBLIC_API_URL)
    console.log('Final API URL:', API_URL)
  }, [])

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
      console.log('Using API URL:', API_URL)
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <FileText className="h-12 w-12 text-indigo-600 mr-3" />
              <h1 className="text-4xl font-bold text-gray-900">
                KUHP Analyzer
              </h1>
            </div>
            <p className="text-xl text-gray-600">
              Analisis Perbedaan KUHP Lama dan Baru dengan Google ADK
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Masukkan pasal atau kata kunci untuk mengetahui perbedaan antara KUHP lama dan baru
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
                  Pasal atau Kata Kunci
                </label>
                <div className="relative">
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
                    <Send className="h-5 w-5" />
                    <span>Analisis Perbedaan</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {result && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center mb-4">
                {result.is_relevant ? (
                  <CheckCircle className="h-6 w-6 text-green-500 mr-2" />
                ) : (
                  <AlertCircle className="h-6 w-6 text-yellow-500 mr-2" />
                )}
                <h2 className="text-xl font-semibold text-gray-900">
                  {result.is_relevant ? 'Hasil Analisis' : 'Informasi'}
                </h2>
              </div>
              
              <div className="prose max-w-none">
                <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                  {result.response}
                </div>
              </div>
              
              {!result.is_relevant && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-yellow-800 text-sm">
                    Tip: Coba tanyakan tentang pasal-pasal spesifik, jenis kejahatan, atau konsep hukum yang ada dalam KUHP.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <footer className="mt-12 text-center text-gray-500 text-sm">
        <p>© 2024 KUHP Analyzer - Powered by Google Agent Development Kit</p>
      </footer>
    </div>
  )
}