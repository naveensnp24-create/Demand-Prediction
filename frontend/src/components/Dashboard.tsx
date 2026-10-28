import { ReactNode, ReactElement, cloneElement, useId } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, Loader2, Database } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Button } from './ui/Button'

export function PageHeader({
  title,
  description,
  children,
}: {
  title: string
  description: string
  children?: ReactNode
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="mt-2 text-muted-foreground max-w-3xl">{description}</p>
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  )
}
export function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}
export function Metric({
  label,
  value,
  detail,
}: {
  label: string
  value: ReactNode
  detail?: string
}) {
  return (
    <Card>
      <div className="p-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold mt-2">{value}</p>
        {detail && <p className="text-xs text-muted-foreground mt-2">{detail}</p>}
      </div>
    </Card>
  )
}
export function RequestState({
  loading,
  error,
  retry,
}: {
  loading: boolean
  error: string
  retry: () => void
}) {
  if (loading)
    return (
      <div role="status" className="flex items-center gap-3 p-8 text-muted-foreground">
        <Loader2 className="animate-spin w-5 h-5" />
        Calculating from your data...
      </div>
    )
  if (error)
    return (
      <div role="alert" className="rounded-xl border border-red-300 p-5 space-y-3">
        <p className="flex gap-2">
          <AlertCircle className="shrink-0 w-5 h-5" />
          {error}
        </p>
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={retry}>
            Try again
          </Button>
          <Link to="/settings" className="text-primary underline">
            Manage data
          </Link>
        </div>
      </div>
    )
  return null
}
export function Empty({
  message = 'Load a demonstration dataset or upload your CSV files to start exploring.',
}: {
  message?: string
}) {
  return (
    <div className="rounded-xl border border-dashed p-10 text-center space-y-4">
      <Database className="w-10 h-10 mx-auto text-primary" />
      <h2 className="text-xl font-semibold">Ready for your data</h2>
      <p className="text-muted-foreground">{message}</p>
      <Link
        to="/settings"
        className="inline-block px-4 py-2 rounded-lg bg-primary text-primary-foreground"
      >
        Set up data
      </Link>
    </div>
  )
}
export function DataTable({
  headers,
  rows,
  empty = 'No records match this selection.',
}: {
  headers: string[]
  rows: ReactNode[][]
  empty?: string
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead>
          <tr className="border-b">
            {headers.map((header) => (
              <th
                key={header}
                scope="col"
                className="p-3 font-medium text-muted-foreground whitespace-nowrap"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b last:border-0 hover:bg-muted/50">
              {row.map((cell, i) => (
                <td key={i} className="p-3">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <p className="p-6 text-muted-foreground">{empty}</p>}
    </div>
  )
}
export const fieldClass =
  'h-10 rounded-lg border bg-background px-3 text-sm w-full focus:outline-none focus:ring-2 focus:ring-primary'
export function Field({
  label,
  children,
}: {
  label: string
  children: ReactElement<{ id?: string }>
}) {
  const generated = useId()
  const id = children.props.id || generated
  return (
    <div className="flex flex-col gap-2 text-sm font-medium min-w-0">
      <label htmlFor={id}>{label}</label>
      {cloneElement(children, { id })}
    </div>
  )
}
