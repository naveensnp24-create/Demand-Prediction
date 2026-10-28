import { Outlet, NavLink } from 'react-router-dom'
import { useState, useEffect } from 'react'
import {
  LayoutDashboard,
  TrendingUp,
  Users,
  BarChart3,
  Package,
  Settings,
  Menu,
  X,
  Sun,
  Moon,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Overview', href: '/overview', icon: LayoutDashboard },
  { name: 'Forecast', href: '/forecast', icon: TrendingUp },
  { name: 'Customer', href: '/customer', icon: Users },
  { name: 'Segments', href: '/segments', icon: BarChart3 },
  { name: 'Insights', href: '/insights', icon: Package },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [darkMode, setDarkMode] = useState(
    () =>
      localStorage.getItem('theme') === 'dark' ||
      (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches),
  )
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    localStorage.setItem('theme', darkMode ? 'dark' : 'light')
  }, [darkMode])
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileOpen(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])
  return (
    <div className="min-h-screen bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:z-50 focus:p-4 focus:bg-background"
      >
        Skip to content
      </a>
      {mobileOpen && (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside
        className={clsx(
          'fixed left-0 top-0 z-40 h-screen border-r bg-card transition-all duration-200 flex flex-col',
          collapsed ? 'lg:w-20' : 'lg:w-64',
          'w-64',
          mobileOpen
            ? 'translate-x-0 visible'
            : '-translate-x-full invisible lg:visible lg:translate-x-0',
        )}
      >
        <div className="h-16 px-4 flex items-center justify-between border-b shrink-0">
          <span
            className={clsx(
              'text-xl font-bold tracking-tight text-primary',
              collapsed && 'lg:hidden',
            )}
          >
            DemandPredict
          </span>
          <button
            className="hidden lg:block p-2 hover:bg-accent rounded-lg"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
          <button
            className="lg:hidden p-2"
            aria-label="Close sidebar"
            onClick={() => setMobileOpen(false)}
          >
            <X size={20} />
          </button>
        </div>
        <nav aria-label="Main navigation" className="p-3 flex-1 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              onClick={() => setMobileOpen(false)}
              title={item.name}
              className={({ isActive }) =>
                clsx(
                  'flex gap-3 items-center px-3 py-3 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                )
              }
            >
              <item.icon size={20} className="shrink-0" />
              <span className={collapsed ? 'lg:hidden' : ''}>{item.name}</span>
            </NavLink>
          ))}
        </nav>
        <div className="border-t p-3">
          <button
            aria-label={darkMode ? 'Switch to light theme' : 'Switch to dark theme'}
            className="flex items-center gap-3 w-full px-3 py-3 rounded-lg hover:bg-accent text-muted-foreground"
            onClick={() => setDarkMode(!darkMode)}
          >
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            <span className={collapsed ? 'lg:hidden' : ''}>{darkMode ? 'Light' : 'Dark'} mode</span>
          </button>
        </div>
      </aside>
      <div className={clsx('min-h-screen transition-all', collapsed ? 'lg:ml-20' : 'lg:ml-64')}>
        <header className="sticky top-0 z-20 h-16 border-b bg-background/95 backdrop-blur flex items-center justify-between px-4 sm:px-8">
          <div className="flex items-center gap-3">
            <button
              aria-label="Open navigation"
              aria-expanded={mobileOpen}
              className="lg:hidden p-2 rounded-lg hover:bg-accent"
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={20} />
            </button>
            <span className="text-sm text-muted-foreground">Retail intelligence workspace</span>
          </div>
          <span className="rounded-full bg-primary/10 text-primary px-3 py-1 text-xs font-medium">
            DemandPredict
          </span>
        </header>
        <main id="main-content" className="p-4 sm:p-6 lg:p-8 max-w-screen-2xl mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
