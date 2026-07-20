import { NextRequest, NextResponse } from 'next/server';

const VERIFY_TOKEN = process.env.META_WEBHOOK_VERIFY_TOKEN;

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const mode = searchParams.get('hub.mode');
  const token = searchParams.get('hub.verify_token');
  const challenge = searchParams.get('hub.challenge');

  if (mode === 'subscribe' && token === VERIFY_TOKEN) {
    return new NextResponse(challenge, { status: 200 });
  }
  return new NextResponse('Forbidden', { status: 403 });
}

export async function POST(req: NextRequest) {
  const body = await req.json();

  // Forward to backend if configured
  const backendUrl = process.env.BACKEND_URL;
  if (backendUrl) {
    fetch(`${backendUrl}/api/v1/webhooks/whatsapp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).catch(() => {});
  }

  return NextResponse.json({ status: 'ok' });
}
