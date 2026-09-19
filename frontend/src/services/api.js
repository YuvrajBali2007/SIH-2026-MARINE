const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'https://sih-2026-marine.vercel.app'

export const checkApiHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/`)

  if (!response.ok) {
    throw new Error('Backend API is offline')
  }

  return response.json()
}

export const runOptimization = async (parameters) => {
  const response = await fetch(
    `${API_BASE_URL}/api/optimization/run`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(parameters),
    },
  )

  if (!response.ok) {
    const errorText = await response.text()

    throw new Error(
      `Optimization request failed: ${response.status} ${errorText}`,
    )
  }

  return response.json()
}