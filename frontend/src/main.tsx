console.log("main.tsx: Execution started");
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { store } from './store.ts'
import './index.css'
import App from './App.tsx'

console.log("main.tsx: Rendering App...");

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </StrictMode>,
)
