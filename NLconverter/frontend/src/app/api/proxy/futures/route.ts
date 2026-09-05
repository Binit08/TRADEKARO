import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

export async function GET() {
  try {
    const backendResponse = await fetch(`${BACKEND_URL}/api/futures`, {
      method: 'GET',
    });

    const data = await backendResponse.json();
    return NextResponse.json(data, { status: backendResponse.status });
  } catch (err: any) {
    console.error('Proxy error (futures):', err.message);
    return NextResponse.json(
      { detail: 'Failed to reach backend' },
      { status: 502 }
    );
  }
}
