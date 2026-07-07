const OWNER = 'Phil-Lord'
const REPO = 'wright-move'
const WORKFLOW = 'scrape.yml'

const COOLDOWN_MS = 60 * 1000 // 1 minute

function githubHeaders(token: string): HeadersInit {
  return {
    'Authorization': `Bearer ${token}`,
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'wright-move-netlify',
  }
}

// Raw dispatch — no auth or cooldown.
// Called by the scheduled function, which is already a trusted server-side caller.
export async function triggerScrape(): Promise<Response> {
  const token = process.env.GITHUB_DISPATCH_TOKEN
  if (!token) {
    return new Response('missing GITHUB_DISPATCH_TOKEN', { status: 500 })
  }

  const res = await fetch(
    `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: 'POST',
      headers: githubHeaders(token),
      body: JSON.stringify({ ref: 'main' }),
    },
  )

  if (!res.ok) {
    return new Response(`github: ${res.status} ${await res.text()}`, { status: 502 })
  }
  return new Response('ok', { status: 202 })
}

// Guarded entrypoint for the public /refresh endpoint:
// shared-secret check, then cooldown, then the raw dispatch.
export async function refreshFromRequest(request: Request): Promise<Response> {
  const token = process.env.GITHUB_DISPATCH_TOKEN
  if (!token) {
    return new Response('missing GITHUB_DISPATCH_TOKEN', { status: 500 })
  }

  if (!hasValidSecret(request)) {
    return new Response('unauthorised', { status: 401 })
  }

  if (await ranWithinCooldown(token)) {
    return new Response('rate limited: a scrape ran recently, try again shortly', {
      status: 429,
    })
  }

  return triggerScrape()
}

// Enforced only when REFRESH_SECRET is set, so local dev works without it.
function hasValidSecret(request: Request): boolean {
  const secret = process.env.REFRESH_SECRET
  return !secret || request.headers.get('x-refresh-secret') === secret
}

async function ranWithinCooldown(token: string): Promise<boolean> {
  const res = await fetch(
    `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/runs?per_page=1`,
    { headers: githubHeaders(token) },
  )
  // If we can't read the run history, don't block the refresh — fail open on the
  // cooldown only (the dispatch itself still has to succeed).
  if (!res.ok) {
    return false
  }

  const data = (await res.json()) as { workflow_runs?: { created_at: string }[] }
  const latest = data.workflow_runs?.[0]
  if (!latest) {
    return false
  }

  const ageMs = Date.now() - new Date(latest.created_at).getTime()
  return ageMs < COOLDOWN_MS
}
