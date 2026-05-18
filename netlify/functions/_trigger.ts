const OWNER = 'Phil-Lord'
const REPO = 'wright-move'
const WORKFLOW = 'scrape.yml'

export async function triggerScrape(): Promise<Response> {
  const token = process.env.GITHUB_DISPATCH_TOKEN
  if (!token) {
    return new Response('missing GITHUB_DISPATCH_TOKEN', { status: 500 })
  }

  const res = await fetch(
    `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'wright-move-netlify',
      },
      body: JSON.stringify({ ref: 'main' }),
    },
  )

  if (!res.ok) {
    return new Response(`github: ${res.status} ${await res.text()}`, { status: 502 })
  }
  return new Response('ok', { status: 202 })
}
