import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

export async function handleRequest(
  request: NextRequest, 
  { params }: { params: Promise<{ path?: string[] }> }
) {
  try {
    const supabase = await createClient();
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
    }

    if (!BACKEND_API_KEY) {
      return NextResponse.json({ error: 'Server configuration error' }, { status: 500 });
    }

    // Await params because Next.js 15+ dynamic APIs require it to be awaited
    // Even if using older Next.js, it's safer to resolve it if it's a promise, but in Next.js app router `params` is not a promise in standard route handlers unless it's Next.js 15. Let's stick to standard object unwrapping to avoid type errors.
    const resolvedParams = await params;
    const pathArray = resolvedParams?.path || [];
    const pathString = pathArray.join('/');
    
    // We proxy to /api/brokers since the backend router is mounted at /api/brokers
    const searchParams = request.nextUrl.search;
    const hasTrailingSlash = request.nextUrl.pathname.endsWith('/');
    const slash = !pathString || hasTrailingSlash ? '/' : '';
    const backendPath = `/api/brokers${pathString ? `/${pathString}` : ''}${slash}${searchParams}`;
    
    const hasBody = ['POST', 'PUT', 'PATCH'].includes(request.method);
    let body;
    if (hasBody) {
      try {
        body = await request.json();
      } catch {
        // Body might be empty
      }
    }

    const backendResponse = await fetch(`${BACKEND_URL}${backendPath}`, {
      method: request.method,
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'X-API-Key': BACKEND_API_KEY,
        ...(hasBody && { 'Content-Type': 'application/json' })
      },
      body: hasBody ? JSON.stringify(body) : undefined,
      redirect: 'manual'
    });

    let data;
    const contentType = backendResponse.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      data = await backendResponse.json();
      return NextResponse.json(data, { status: backendResponse.status });
    } else if (backendResponse.status === 307 || backendResponse.status === 302) {
        // If it's a redirect (like for Kite login)
        return NextResponse.redirect(backendResponse.headers.get('location') as string);
    } else {
      const textData = await backendResponse.text();
      return new NextResponse(textData, { status: backendResponse.status, headers: { 'Content-Type': contentType || 'text/plain' } });
    }

  } catch (err: any) {
    console.error('Brokers proxy error:', err.message);
    return NextResponse.json({ error: 'Failed to reach backend' }, { status: 502 });
  }
}

export const GET = handleRequest;
export const POST = handleRequest;
export const PUT = handleRequest;
export const DELETE = handleRequest;
