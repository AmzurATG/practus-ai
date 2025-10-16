import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import Login from './pages/Login'
import Home from './pages/Home'
import Visualization from './pages/Visualization'
import ActionableItems from './pages/Insights'
import Chat from './pages/Chat'
import Layout from './components/Layout'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'))

  const login = (newToken) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={token ? <Navigate to="/" /> : <Login onLogin={login} />} />
        <Route path="/" element={token ? <Layout onLogout={logout} /> : <Navigate to="/login" />}>
          <Route index element={<Home />} />
          <Route path="visualization" element={<Visualization />} />
          <Route path="chat" element={<Chat />} />
          <Route path="insights" element={<ActionableItems />} />
        </Route>
      </Routes>
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#4ade80',
              secondary: '#fff',
            },
          },
        }}
      />
    </BrowserRouter>
  )
}

export default App

