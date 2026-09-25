import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { Streamlit, withStreamlitConnection } from 'streamlit-component-lib'
import App from './App'
import './index.css'

const StreamlitApp = withStreamlitConnection(() => {
  useEffect(() => {
    Streamlit.setFrameHeight()
  })

  return <App />
})

Streamlit.setComponentReady()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <StreamlitApp />
  </React.StrictMode>,
)