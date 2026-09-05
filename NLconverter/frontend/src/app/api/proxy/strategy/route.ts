import { createClient } from '@/lib/supabase/server';
/**
 * Fix 1: Server-side proxy route for /api/strategy.
 * The API key is injected server-side from BACKEND_API_KEY — never exposed to the browser.
 */
import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

export async function POST(request: Request) {
    const supabase = await createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

  try {
    if (!BACKEND_API_KEY) {
      console.error('BACKEND_API_KEY environment variable is not set');
      return NextResponse.json(
        { detail: 'Server configuration error' },
        { status: 500 }
      );
    }

    const body = await request.json();

    const backendResponse = await fetch(`${BACKEND_URL}/api/strategy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        'X-API-Key': BACKEND_API_KEY,
      },
      body: JSON.stringify(body),
    });

    const data = await backendResponse.json();
    return NextResponse.json(data, { status: backendResponse.status });
  } catch (err: any) {
    console.error('Proxy error (strategy):', err.message);
    if (err.cause) {
        console.error('Fetch failed cause:', err.cause);
    }
    console.error('Attempted URL was:', `${BACKEND_URL}/api/strategy`);
    return NextResponse.json(
      { detail: `Failed to reach backend: ${err.message}` },
      { status: 502 }
    );
  }
}
