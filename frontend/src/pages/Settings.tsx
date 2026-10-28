import { useRef, useState } from 'react'
import { PageHeader, Panel, Metric, RequestState, Field, fieldClass } from '@/components/Dashboard'
import { Button } from '@/components/ui/Button'
import { api, API_URL, useData, number } from '@/lib/api'

const tables = ['customers', 'products', 'promotions', 'events', 'orders'] as const
interface Status {
  counts: Record<string, number>
  demo_available: boolean
}
interface ImportResult {
  message: string
  rows_processed: number
  tables_updated: string[]
}
export function Settings() {
  const status = useData<Status>('/data/status')
  const [files, setFiles] = useState<Record<string, File>>({})
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [schemaTable, setSchemaTable] = useState('customers')
  const schema = useData<{ required_columns: string[]; example_row: Record<string, unknown> }>(
    `/upload/schema/${schemaTable}`,
  )
  const form = useRef<HTMLFormElement>(null)
  async function submit(demo = false) {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const body = new FormData()
      Object.entries(files).forEach(([key, file]) => body.append(key, file))
      const result = await api<ImportResult>(demo ? '/data/demo' : '/upload', {
        method: 'POST',
        body: demo ? undefined : body,
      })
      setNotice(`${result.message}. Updated: ${result.tables_updated.join(', ')}.`)
      setFiles({})
      form.current?.reset()
      status.refresh()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Import failed')
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="space-y-6">
      <PageHeader
        title="Data & settings"
        description="Import retail data, inspect CSV schemas, or start with a reproducible demonstration dataset."
      />
      <RequestState loading={status.loading} error={status.error} retry={status.refresh} />
      {status.data && (
        <div className="grid grid-cols-2 xl:grid-cols-5 gap-4">
          {tables.map((table) => (
            <Metric
              key={table}
              label={table.charAt(0).toUpperCase() + table.slice(1)}
              value={number(status.data!.counts[table] || 0)}
            />
          ))}
        </div>
      )}
      {notice && (
        <p role="status" className="rounded-lg border border-green-400 bg-green-500/10 p-4">
          {notice}
        </p>
      )}
      {error && (
        <p role="alert" className="rounded-lg border border-red-400 bg-red-500/10 p-4 break-words">
          {error}
        </p>
      )}
      <div className="grid xl:grid-cols-[2fr_1fr] gap-6">
        <Panel title="Upload CSV files">
          <p className="text-sm text-muted-foreground mb-5">
            Upload one or several tables. Matching IDs update existing records. All files are
            validated and saved together; an error rolls back the entire import. Include parent
            customer, product, and promotion records before dependent orders and events.
          </p>
          <form
            ref={form}
            onSubmit={(e) => {
              e.preventDefault()
              void submit()
            }}
            className="space-y-4"
          >
            {tables.map((table) => (
              <Field key={table} label={`${table.charAt(0).toUpperCase() + table.slice(1)} CSV`}>
                <input
                  type="file"
                  accept=".csv,text/csv"
                  disabled={busy}
                  className="block w-full text-sm file:mr-3 file:rounded-md file:border-0 file:py-2 file:px-3 file:bg-secondary file:text-foreground"
                  onChange={(e) =>
                    setFiles((current) => {
                      const next = { ...current }
                      const file = e.target.files?.[0]
                      if (file) next[table] = file
                      else delete next[table]
                      return next
                    })
                  }
                />
              </Field>
            ))}
            <Button type="submit" disabled={!Object.keys(files).length || busy} loading={busy}>
              Validate and import
            </Button>
            <p className="text-xs text-muted-foreground">
              Default upload limit: 100 MB per file. Currency throughout the dashboard is INR.
            </p>
          </form>
        </Panel>
        <Panel title="Try demonstration data">
          <p className="text-sm text-muted-foreground mb-4">
            Load 120 synthetic customers, 24 products, and 180 days of orders and browsing activity.
            This generates fictional records for testing the complete workflow.
          </p>
          <Button
            onClick={() => void submit(true)}
            disabled={!status.data?.demo_available || busy}
            loading={busy}
          >
            Load demo dataset
          </Button>
          {status.data && !status.data.demo_available && (
            <p className="mt-3 text-xs text-muted-foreground">
              Demo loading is available only for an empty database, to preserve your imported
              records.
            </p>
          )}
          <div className="border-t mt-6 pt-4 space-y-2 text-sm">
            <p className="font-medium">API documentation</p>
            <a
              className="text-primary underline"
              href={API_URL.replace(/\/api\/v1$/, '') + '/docs'}
              target="_blank"
              rel="noreferrer"
            >
              Open interactive API docs
            </a>
            <p className="text-muted-foreground">
              For model evaluation and setup commands, see the project README.
            </p>
          </div>
        </Panel>
      </div>
      <Panel title="CSV schema and templates">
        <div className="max-w-xs mb-4">
          <Field label="Table">
            <select
              className={fieldClass}
              value={schemaTable}
              onChange={(e) => setSchemaTable(e.target.value)}
            >
              {tables.map((table) => (
                <option key={table}>{table}</option>
              ))}
            </select>
          </Field>
        </div>
        <RequestState loading={schema.loading} error={schema.error} retry={schema.refresh} />
        {schema.data && (
          <>
            <p className="text-sm font-medium mb-2">Required columns</p>
            <div className="flex flex-wrap gap-2 mb-4">
              {schema.data.required_columns.map((column) => (
                <code key={column} className="text-xs rounded bg-muted px-2 py-1">
                  {column}
                </code>
              ))}
            </div>
            <a
              className="text-primary underline text-sm"
              href={`${API_URL}/upload/template/${schemaTable}`}
              download
            >
              Download {schemaTable} example CSV
            </a>
            <p className="mt-3 text-sm text-muted-foreground">
              Dates use ISO format. Booleans accept true/false or 1/0. List fields use brackets,
              such as [10, 11, 12]. IDs must match across files. Order statuses: pending, confirmed,
              shipped, delivered, cancelled, returned.
            </p>
          </>
        )}
      </Panel>
    </div>
  )
}
