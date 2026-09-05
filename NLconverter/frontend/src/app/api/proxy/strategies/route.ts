import { createClient } from '@/lib/supabase/server';
/**
 * Fix 1: Server-side proxy route for /api/strategies (GET).
 * The API key is injected server-side from BACKEND_API_KEY.
 */
import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

export async function GET(request: Request) {
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

    const url = new URL(request.url);
    const limit = url.searchParams.get('limit') || '10';
    const offset = url.searchParams.get('offset') || '0';

    const backendResponse = await fetch(`${BACKEND_URL}/api/strategies?limit=${limit}&offset=${offset}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        'X-API-Key': BACKEND_API_KEY,
      },
    });

    const data = await backendResponse.json();
    return NextResponse.json(data, { status: backendResponse.status });
  } catch (err: any) {
    console.error('Proxy error (strategies):', err.message);
    return NextResponse.json(
      { detail: 'Failed to reach backend' },
      { status: 502 }
    );
  }
}
