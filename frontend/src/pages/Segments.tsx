import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { PageHeader, Panel, Metric, RequestState, Empty, DataTable } from '@/components/Dashboard'
import { Button } from '@/components/ui/Button'
import { useData, Segment, number, money, exportCSV } from '@/lib/api'

interface Member {
  customer_id: string
  first_name: string
  last_name: string
  recency: number
  frequency: number
  monetary: number
}
export function Segments() {
  const result = useData<{
    segments: Segment[]
    total_customers: number
    as_of: string
    method: string
  }>('/segments')
  const [selected, setSelected] = useState('')
  const [offset, setOffset] = useState(0)
  const members = useData<{ total: number; customers: Member[] }>(
    selected ? `/segments/${selected}/customers?limit=20&offset=${offset}` : null,
  )
  const data = result.data
  return (
    <div className="space-y-6">
      <PageHeader
        title="Customer segments"
        description="Behavioral groups built from recency, purchase frequency, and monetary value."
      >
        <Button variant="outline" onClick={result.refresh}>
          Refresh
        </Button>
        <Button
          disabled={!data?.total_customers}
          onClick={() =>
            data &&
            exportCSV(
              'segments.csv',
              ['Segment', 'Customers', 'Recency days', 'Frequency', 'Monetary INR'],
              data.segments.map((row) => [
                row.label,
                row.size,
                row.avg_recency,
                row.avg_frequency,
                row.avg_monetary,
              ]),
            )
          }
        >
          Export segments
        </Button>
      </PageHeader>
      <RequestState loading={result.loading} error={result.error} retry={result.refresh} />
      {data &&
        (data.total_customers ? (
          <>
            <div className="grid sm:grid-cols-3 gap-4">
              <Metric label="Customers analyzed" value={number(data.total_customers)} />
              <Metric label="Behavior groups" value={data.segments.length} />
              <Metric label="Dataset date" value={data.as_of} />
            </div>
            <Panel title="Segment distribution">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.segments}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip contentStyle={{ background: 'hsl(var(--card))' }} />
                    <Bar
                      isAnimationActive={false}
                      dataKey="size"
                      fill="#0ea5e9"
                      name="Customers"
                      radius={[5, 5, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Panel>
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
              {data.segments.map((segment) => (
                <Panel key={segment.segment} title={segment.label}>
                  <p className="text-2xl font-semibold">
                    {number(segment.size)}{' '}
                    <span className="text-sm text-muted-foreground">({segment.percentage}%)</span>
                  </p>
                  <dl className="text-sm space-y-2 my-4">
                    <div className="flex justify-between gap-2">
                      <dt>Average recency</dt>
                      <dd>{number(segment.avg_recency)} days</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt>Average purchases</dt>
                      <dd>{number(segment.avg_frequency)}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt>Average spend</dt>
                      <dd>{money(segment.avg_monetary)}</dd>
                    </div>
                  </dl>
                  <p className="text-sm text-muted-foreground mb-4">
                    {segment.characteristics.join(' ')}
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSelected(segment.segment)
                      setOffset(0)
                    }}
                  >
                    View customers
                  </Button>
                </Panel>
              ))}
            </div>
            <p className="text-sm text-muted-foreground">
              {data.method}. Customers without purchases are grouped separately; recency then
              measures time since signup.
            </p>
          </>
        ) : (
          <Empty />
        ))}
      <RequestState loading={members.loading} error={members.error} retry={members.refresh} />
      {members.data && (
        <Panel title={`${selected.replaceAll('_', ' ')} customers`}>
          <DataTable
            headers={['Customer', 'Name', 'Recency days', 'Purchases', 'Spend']}
            rows={members.data.customers.map((row) => [
              row.customer_id,
              `${row.first_name} ${row.last_name}`,
              number(row.recency),
              number(row.frequency),
              money(row.monetary),
            ])}
          />
          <div className="flex flex-wrap items-center justify-between gap-3 mt-4">
            <p className="text-sm text-muted-foreground">
              {offset + 1}-{Math.min(offset + 20, members.data.total)} of {members.data.total}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={offset === 0}
                onClick={() => setOffset(offset - 20)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                disabled={offset + 20 >= members.data.total}
                onClick={() => setOffset(offset + 20)}
              >
                Next
              </Button>
            </div>
            <Link className="text-primary text-sm underline" to="/customer">
              Explore a customer
            </Link>
          </div>
        </Panel>
      )}
    </div>
  )
}
