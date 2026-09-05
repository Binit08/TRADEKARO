import { createClient } from '@/lib/supabase/server';
/**
 * Fix 4: Backtests API routes — proxy to backend (single source of truth).
 * POST handler removed — backend persists backtests directly.
 * GET handler proxies to backend GET /api/backtests.
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
        { success: false, error: 'Server configuration error' },
        { status: 500 }
      );
    }

    const url = new URL(request.url);
    const limit = url.searchParams.get('limit') || '10';
    const offset = url.searchParams.get('offset') || '0';

    const backendResponse = await fetch(`${BACKEND_URL}/api/backtests?limit=${limit}&offset=${offset}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        'X-API-Key': BACKEND_API_KEY,
      },
    });

    const result = await backendResponse.json();

    if (!backendResponse.ok) {
      return NextResponse.json(
        { success: false, error: result.detail || 'Backend error' },
        { status: backendResponse.status }
      );
    }

    // Preserve pagination metadata so the history page can represent the full dataset.
    return NextResponse.json({
      success: true,
      data: result.data,
      has_more: result.has_more,
      total_count: result.total_count,
    });
  } catch (err: any) {
    console.error('API Error (backtests list):', err.message);
    return NextResponse.json(
      { success: false, error: 'Failed to reach backend' },
      { status: 502 }
    );
  }
}
