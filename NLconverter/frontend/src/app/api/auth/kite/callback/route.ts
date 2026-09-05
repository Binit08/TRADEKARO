import { NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

export async function POST(request: Request) {
  try {
    const supabase = await createClient();
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
    }

    if (!BACKEND_API_KEY) {
      console.error('BACKEND_API_KEY environment variable is not set');
      return NextResponse.json({ error: 'Server configuration error' }, { status: 500 });
    }

    const body = await request.json();

    const backendResponse = await fetch(`${BACKEND_URL}/api/auth/kite/callback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
        'X-API-Key': BACKEND_API_KEY,
      },
      body: JSON.stringify(body),
    });

    const data = await backendResponse.json();
    return NextResponse.json(data, { status: backendResponse.status });

  } catch (err: any) {
    console.error('Kite callback proxy error:', err.message);
    return NextResponse.json({ detail: 'Failed to reach backend' }, { status: 502 });
  }
}
