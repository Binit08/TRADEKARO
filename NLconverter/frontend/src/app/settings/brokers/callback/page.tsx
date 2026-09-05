'use client';
import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle2, Loader2, XCircle } from 'lucide-react';
import Loader from '@/components/ui/Loader';

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const requestToken = searchParams.get('request_token');
    
    if (!requestToken) {
      setStatus('error');
      setErrorMsg('No request token found in URL.');
      setTimeout(() => router.push('/settings/brokers'), 3000);
      return;
    }

    const generateSession = async () => {
      try {
        const res = await fetch('/api/v1/brokers/session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ request_token: requestToken })
        });
        
        if (res.ok) {
          setStatus('success');
          setTimeout(() => router.push('/'), 1500);
        } else {
          const data = await res.json();
          setStatus('error');
          setErrorMsg(data.detail || 'Failed to generate session.');
          setTimeout(() => router.push('/settings/brokers'), 3000);
        }
      } catch (err) {
        setStatus('error');
        setErrorMsg('Network error.');
        setTimeout(() => router.push('/settings/brokers'), 3000);
      }
    };

    generateSession();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-black/95 flex items-center justify-center font-sans">
      <div className="bg-zinc-900/50 backdrop-blur-xl border border-zinc-800/60 rounded-2xl p-8 shadow-2xl max-w-md w-full text-center space-y-6">
        
        {status === 'loading' && (
          <div className="flex flex-col items-center space-y-4 animate-in fade-in">
            <Loader />
            <h2 className="text-xl font-semibold text-zinc-100 mt-4">Securing Connection...</h2>
            <p className="text-zinc-400 text-sm">Exchanging tokens with Zerodha Kite. Please wait.</p>
          </div>
        )}

        {status === 'success' && (
          <div className="flex flex-col items-center space-y-4 animate-in zoom-in-95 fade-in">
            <CheckCircle2 className="w-12 h-12 text-emerald-500" />
            <h2 className="text-xl font-semibold text-zinc-100">Login Successful!</h2>
            <p className="text-zinc-400 text-sm">Redirecting back to your dashboard...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center space-y-4 animate-in zoom-in-95 fade-in">
            <XCircle className="w-12 h-12 text-red-500" />
            <h2 className="text-xl font-semibold text-zinc-100">Login Failed</h2>
            <p className="text-zinc-400 text-sm">{errorMsg}</p>
          </div>
        )}

      </div>
    </div>
  );
}

export default function BrokerCallback() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-black/95" />}>
      <CallbackContent />
    </Suspense>
  );
}
