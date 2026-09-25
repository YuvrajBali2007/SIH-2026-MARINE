import { Streamlit } from 'streamlit-component-lib'

let requestId = 0

export const checkApiHealth = async () => {
  return {
    status: 'ok',
  }
}

export const runOptimization = async (parameters) => {
  requestId += 1

  Streamlit.setComponentValue({
    type: 'optimization_request',
    request_id: requestId,
    parameters,
  })

  return new Promise(() => {})
}