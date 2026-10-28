import { Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { Layout } from './components/Layout'
const Overview = lazy(() =>
  import('./pages/Overview').then((module) => ({ default: module.Overview })),
)
const Forecast = lazy(() =>
  import('./pages/Forecast').then((module) => ({ default: module.Forecast })),
)
const Customer = lazy(() =>
  import('./pages/Customer').then((module) => ({ default: module.Customer })),
)
const Segments = lazy(() =>
  import('./pages/Segments').then((module) => ({ default: module.Segments })),
)
const Insights = lazy(() =>
  import('./pages/Insights').then((module) => ({ default: module.Insights })),
)
const Settings = lazy(() =>
  import('./pages/Settings').then((module) => ({ default: module.Settings })),
)

function App() {
  return (
    <Suspense
      fallback={
        <p role="status" className="p-8">
          Loading workspace...
        </p>
      }
    >
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<Overview />} />
          <Route path="forecast" element={<Forecast />} />
          <Route path="customer" element={<Customer />} />
          <Route path="segments" element={<Segments />} />
          <Route path="insights" element={<Insights />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/overview" replace />} />
      </Routes>
    </Suspense>
  )
}

export default App
