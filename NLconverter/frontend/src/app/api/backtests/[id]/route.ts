import { createClient } from '@/lib/supabase/server';
/**
 * Fix 4: Single backtest by ID — proxy to backend (single source of truth).
 * Replaces direct Supabase reads.
 */
import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
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

    const { id } = await params;

    const backendResponse = await fetch(`${BACKEND_URL}/api/backtests/${id}`, {
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
        { success: false, error: result.detail || 'Backtest not found' },
        { status: backendResponse.status }
      );
    }

    // Backend returns { status: "ok", data: {...} }
    return NextResponse.json({
      success: true,
      data: result.data,
    });
  } catch (err: any) {
    console.error('API Error (backtest by id):', err.message);
    return NextResponse.json(
      { success: false, error: 'Failed to reach backend' },
      { status: 502 }
    );
  }
}
