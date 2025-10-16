import { Outlet, Link, useLocation } from 'react-router-dom'
import { BarChart3, Lightbulb, MessageSquare, LogOut, Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'

export default function Layout({ onLogout }) {
  const location = useLocation()
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light')

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }, [theme])
  
  const navItems = [
    { path: '/', icon: Lightbulb, label: 'Home' },
    { path: '/visualization', icon: BarChart3, label: 'Visualization' },
    { path: '/chat', icon: MessageSquare, label: 'AI Chat' },
    { path: '/insights', icon: Lightbulb, label: 'Actionable Items' },
  ]

  return (
    <div className={"min-h-screen "+(theme==='dark'?'bg-gray-950':'bg-gray-50')}>
      <nav className={(theme==='dark'?"bg-gray-900 border-gray-800":"bg-white")+" shadow-sm border-b"}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-8">
              <div className="flex-shrink-0 flex items-center">
                <div className="flex items-center space-x-3">
                  <img 
                    src="/practus_logo.jpeg" 
                    alt="Practus AI Logo" 
                    className="h-10 w-auto"
                  />
                  <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
                    Practus AI
                  </div>
                </div>
              </div>
              <div className="hidden sm:flex sm:space-x-4">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                        isActive
                          ? (theme==='dark'?'bg-blue-950 text-blue-300':'bg-blue-50 text-blue-700')
                          : (theme==='dark'?'text-gray-300 hover:text-white hover:bg-gray-800':'text-gray-600 hover:text-gray-900 hover:bg-gray-50')
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {item.label}
                    </Link>
                  )
                })}
              </div>
            </div>
            <div className="flex items-center">
              <button
                onClick={() => setTheme(theme==='dark'?'light':'dark')}
                className={(theme==='dark'?"text-gray-300 hover:text-white":"text-gray-700 hover:text-gray-900")+" inline-flex items-center px-3 py-2 text-sm font-medium rounded-md mr-2"}
                title={theme==='dark'?'Switch to light mode':'Switch to dark mode'}
              >
                {theme==='dark' ? <Sun className="w-4 h-4"/> : <Moon className="w-4 h-4"/>}
              </button>
              <button
                onClick={onLogout}
                className={(theme==='dark'?"text-gray-300 hover:text-white hover:bg-gray-800":"text-gray-700 hover:text-gray-900 hover:bg-gray-50")+" inline-flex items-center px-4 py-2 text-sm font-medium rounded-md"}
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className={(theme==='dark'?"text-gray-100":"text-gray-900")+" max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"}>
        <Outlet />
      </main>
    </div>
  )
}

