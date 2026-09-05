'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import Loader from '@/components/ui/Loader'

function KiteCallbackContent() {
  const [status, setStatus] = useState('Connecting to Kite...')
  const [error, setError] = useState<string | null>(null)
  
  const searchParams = useSearchParams()
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const handleCallback = async () => {
      const requestToken = searchParams.get('request_token')
      const action = searchParams.get('action')
      const kiteStatus = searchParams.get('status')
      
      if (!requestToken) {
        setError('Missing request token from Kite Connect.')
        return
      }

      if (kiteStatus !== 'success' || action !== 'login') {
        setError('Kite login failed or was cancelled.')
        return
      }

      try {
        setStatus('Exchanging token with backend...')
        
        // Get the current user session
        const { data: { session } } = await supabase.auth.getSession()
        
        if (!session) {
          setError('You must be logged in to connect Kite.')
          router.push('/login')
          return
        }

        // Call our Next.js proxy route (avoids CORS, handles auth server-side)
        const res = await fetch('/api/v1/brokers/session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ request_token: requestToken })
        })

        if (!res.ok) {
          const errData = await res.json()
          throw new Error(errData.detail || 'Failed to connect Kite.')
        }

        setStatus('Kite connected successfully! Redirecting...')
        
        // Short delay before redirect
        setTimeout(() => {
          router.push('/')
        }, 1500)
        
      } catch (err: any) {
        console.error('Kite callback error:', err)
        setError(err.message || 'An unexpected error occurred.')
      }
    }

    handleCallback()
  }, [searchParams, router, supabase.auth])

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-4">
      <div className="w-full max-w-md space-y-8 rounded-2xl bg-zinc-900 border border-zinc-800 p-10 shadow-2xl text-center">
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Kite Connect
        </h2>
        
        {!error ? (
          <div className="space-y-4">
            <Loader />
            <p className="text-zinc-400 mt-4">{status}</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-md bg-red-900/50 p-4 text-sm text-red-400 border border-red-800">
              {error}
            </div>
            <button
              onClick={() => router.push('/')}
              className="mt-4 flex w-full justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none"
            >
              Return to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function KiteCallbackPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 text-white"><Loader /></div>}>
      <KiteCallbackContent />
    </Suspense>
  )
}
