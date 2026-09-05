import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

export async function GET(request: Request, props: { params: Promise<{ id: string }> }) {
    const params = await props.params;
    const sessionId = params.id;
    
    const supabase = await createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    try {
        if (!BACKEND_API_KEY) {
            console.error('BACKEND_API_KEY environment variable is not set');
            return NextResponse.json({ detail: 'Server configuration error' }, { status: 500 });
        }

        const backendResponse = await fetch(`${BACKEND_URL}/api/paper_trade/${sessionId}/status`, {
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
        console.error('Proxy error (paper_trade_status):', err.message);
        return NextResponse.json({ detail: 'Failed to reach backend' }, { status: 502 });
    }
}
