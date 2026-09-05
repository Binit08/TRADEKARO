import { createClient } from '@/lib/supabase/server';
/**
 * Fix 1: Server-side proxy route for /api/backtest (POST).
 * The API key is injected server-side from BACKEND_API_KEY.
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

    const backendResponse = await fetch(`${BACKEND_URL}/api/backtest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        'X-API-Key': BACKEND_API_KEY,
      },
      body: JSON.stringify(body),
    });

    const text = await backendResponse.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      console.error('Backend returned non-JSON:', text.substring(0, 200));
      return NextResponse.json(
        { detail: 'Backend returned invalid JSON: ' + text.substring(0, 100) },
        { status: 502 }
      );
    }
    return NextResponse.json(data, { status: backendResponse.status });
  } catch {
    return NextResponse.json(
      { detail: 'Failed to reach backend' },
      { status: 502 }
    );
  }
}
