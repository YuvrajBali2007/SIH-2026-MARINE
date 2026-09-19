const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const normalizeParameters = (parameters) => ({
  ...parameters,
  cargo_type: parameters.cargo_type === 'Coal Ore' ? 'Coal' : parameters.cargo_type,
  market_event: parameters.market_event === 'None' ? 'None' : parameters.market_event,
})

export const checkApiHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/`)
  if (!response.ok) throw new Error('Backend API is offline')
  return response.json()
}

export const runOptimization = async (parameters) => {
  const response = await fetch(`${API_BASE_URL}/api/optimization/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(normalizeParameters(parameters)),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Optimization request failed: ${response.status} ${errorText}`)
  }

  return response.json()
}