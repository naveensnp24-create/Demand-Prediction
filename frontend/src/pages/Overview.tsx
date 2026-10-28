import { Link } from 'react-router-dom'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { PageHeader, Panel, Metric, RequestState, Empty, DataTable } from '@/components/Dashboard'
import { Button } from '@/components/ui/Button'
import { useData, OverviewData, number, money, exportCSV } from '@/lib/api'

export function Overview() {
  const { data, loading, error, refresh } = useData<OverviewData>('/overview')
  return (
    <div className="space-y-6">
      <PageHeader
        title="Overview"
        description="A clear view of demand, customers, and sales from your imported history."
      >
        <Button variant="outline" onClick={refresh}>
          Refresh data
        </Button>
        <Button
          disabled={!data?.orders}
          onClick={() =>
            data &&
            exportCSV(
              'category-report.csv',
              ['Category', 'Units', 'Revenue INR'],
              data.categories.map((row) => [row.category, row.units, row.revenue]),
            )
          }
        >
          Export report
        </Button>
      </PageHeader>
      <RequestState loading={loading} error={error} retry={refresh} />
      {data &&
        (data.orders ? (
          <>
            <p className="text-sm text-muted-foreground">
              Data through {data.as_of} | Revenue excludes cancelled, pending, and returned orders.
            </p>
            <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
              <Metric
                label="30-day demand estimate"
                value={number(data.forecast_30d)}
                detail="Units | based on the last 28 days"
              />
              <Metric label="Recorded sales revenue" value={money(data.revenue)} />
              <Metric
                label="Customers"
                value={number(data.customers)}
                detail={`${data.at_risk_customers} in at-risk segments`}
              />
              <Metric
                label="Active history"
                value={number(data.orders)}
                detail={`${data.products} products | ${number(data.events)} behavior events`}
              />
            </div>
            <Panel title="Daily demand - last 90 days">
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.trend}>
                    <defs>
                      <linearGradient id="demand" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#0ea5e9" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={45} />
                    <YAxis />
                    <Tooltip
                      contentStyle={{
                        background: 'hsl(var(--card))',
                        borderColor: 'hsl(var(--border))',
                      }}
                    />
                    <Area
                      isAnimationActive={false}
                      type="monotone"
                      dataKey="demand"
                      stroke="#0ea5e9"
                      fill="url(#demand)"
                      name="Units"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Panel>
            <div className="grid xl:grid-cols-[2fr_1fr] gap-6">
              <Panel title="Category performance">
                <DataTable
                  headers={['Category', 'Units sold', 'Revenue']}
                  rows={data.categories.map((row) => [
                    row.category,
                    number(row.units),
                    money(row.revenue),
                  ])}
                />
              </Panel>
              <Panel title="Explore your business">
                <div className="space-y-4">
                  {[
                    [
                      '/forecast',
                      'Plan future demand',
                      'Compare forecasting models and uncertainty ranges.',
                    ],
                    [
                      '/customer',
                      'Understand customers',
                      'Explore purchase probabilities and behavioral drivers.',
                    ],
                    [
                      '/insights',
                      'Plan inventory',
                      'Find stock risks and suggested reorder quantities.',
                    ],
                  ].map(([href, title, description]) => (
                    <Link
                      key={href}
                      to={href}
                      className="block rounded-lg border p-4 hover:bg-accent"
                    >
                      <p className="font-semibold text-primary">{title} &rarr;</p>
                      <p className="text-sm mt-1 text-muted-foreground">{description}</p>
                    </Link>
                  ))}
                </div>
              </Panel>
            </div>
          </>
        ) : (
          <Empty />
        ))}
    </div>
  )
}
