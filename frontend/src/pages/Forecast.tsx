import { useState } from 'react'
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import {
  PageHeader,
  Panel,
  Metric,
  RequestState,
  Empty,
  DataTable,
  Field,
  fieldClass,
} from '@/components/Dashboard'
import { Button } from '@/components/ui/Button'
import { useData, Product, ForecastData, number, exportCSV } from '@/lib/api'

export function Forecast() {
  const catalog = useData<{ products: Product[] }>('/products?limit=2000')
  const categories = useData<{ categories: string[] }>('/categories')
  const [mode, setMode] = useState('product')
  const [selection, setSelection] = useState('')
  const [horizon, setHorizon] = useState(30)
  const [model, setModel] = useState('ensemble')
  const options =
    mode === 'product'
      ? catalog.data?.products.map((p) => ({ id: p.product_id, name: p.name })) || []
      : categories.data?.categories.map((c) => ({ id: c, name: c })) || []
  const selected = options.some((option) => option.id === selection) ? selection : options[0]?.id
  const request = useData<ForecastData>(
    selected
      ? `/forecast/${mode}/${encodeURIComponent(selected)}?horizon=${horizon}&model=${model}`
      : null,
  )
  const data = request.data
  const chart = data
    ? [
        ...data.historical_data.slice(-60).map((row) => ({ date: row.date, actual: row.demand })),
        ...data.forecast.map((row) => ({
          date: row.date,
          forecast: row.predicted_demand,
          range: [row.lower, row.upper],
        })),
      ]
    : []
  return (
    <div className="space-y-6">
      <PageHeader
        title="Demand forecast"
        description="Compare daily forecasts against chronological holdout data. Choose a product or category to begin."
      >
        <Button
          disabled={!data}
          variant="outline"
          onClick={() =>
            data &&
            exportCSV(
              'forecast.csv',
              ['Date', 'Predicted units', 'Lower', 'Upper'],
              data.forecast.map((row) => [row.date, row.predicted_demand, row.lower, row.upper]),
            )
          }
        >
          Download CSV
        </Button>
      </PageHeader>
      <Panel title="Forecast controls">
        <div className="grid sm:grid-cols-2 xl:grid-cols-5 gap-4">
          <Field label="Forecast level">
            <select
              className={fieldClass}
              value={mode}
              onChange={(e) => {
                setMode(e.target.value)
                setSelection('')
              }}
            >
              <option value="product">Product</option>
              <option value="category">Category</option>
            </select>
          </Field>
          <Field label={mode === 'product' ? 'Product' : 'Category'}>
            <select
              className={fieldClass}
              value={selected || ''}
              onChange={(e) => setSelection(e.target.value)}
            >
              {!options.length && <option value="">No data available</option>}
              {options.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Forecast horizon">
            <select
              className={fieldClass}
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
            >
              {[7, 14, 30, 60, 90].map((days) => (
                <option key={days} value={days}>
                  {days} days
                </option>
              ))}
            </select>
          </Field>
          <Field label="Model">
            <select className={fieldClass} value={model} onChange={(e) => setModel(e.target.value)}>
              {[
                ['ensemble', 'Weighted ensemble'],
                ['ma', 'Moving average'],
                ['prophet', 'Prophet'],
                ['xgboost', 'XGBoost'],
                ['lightgbm', 'LightGBM'],
              ].map(([id, label]) => (
                <option key={id} value={id}>
                  {label}
                </option>
              ))}
            </select>
          </Field>
          <div className="flex items-end">
            <Button
              className="w-full"
              onClick={request.refresh}
              disabled={!selected}
              loading={request.loading}
            >
              Refresh forecast
            </Button>
          </div>
        </div>
      </Panel>
      <RequestState
        loading={catalog.loading || categories.loading}
        error={catalog.error || categories.error}
        retry={() => {
          catalog.refresh()
          categories.refresh()
        }}
      />
      <RequestState loading={request.loading} error={request.error} retry={request.refresh} />
      {!catalog.loading && !catalog.error && catalog.data?.products.length === 0 && <Empty />}
      {data && (
        <>
          <div className="grid sm:grid-cols-3 gap-4">
            <Metric
              label={`${horizon}-day predicted demand`}
              value={number(data.forecast.reduce((sum, row) => sum + row.predicted_demand, 0))}
              detail={data.product_name || data.category}
            />
            <Metric
              label="Forecast starts after"
              value={data.as_of}
              detail="Last observation in the dataset"
            />
            <Metric
              label="Model used"
              value={data.model_used}
              detail={`${data.validation_days} holdout days`}
            />
          </div>
          <Panel title="Historical and predicted daily units">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chart}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={45} />
                  <YAxis />
                  <Tooltip contentStyle={{ background: 'hsl(var(--card))' }} />
                  <Legend />
                  <Area
                    isAnimationActive={false}
                    dataKey="range"
                    stroke="none"
                    fill="#0ea5e9"
                    fillOpacity={0.15}
                    name="Residual range"
                  />
                  <Line
                    isAnimationActive={false}
                    dataKey="actual"
                    stroke="#64748b"
                    dot={false}
                    name="Actual"
                  />
                  <Line
                    isAnimationActive={false}
                    dataKey="forecast"
                    stroke="#0ea5e9"
                    dot={false}
                    name="Forecast"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Panel>
          <Panel title="Model validation">
            <DataTable
              headers={['Model', 'MAE (units)', 'RMSE (units)', 'MAPE', 'WMAPE']}
              rows={Object.entries(data.model_metrics).map(([name, score]) => [
                name,
                number(score.mae),
                number(score.rmse),
                score.mape === undefined ? 'Unavailable' : `${number(score.mape)}%`,
                score.wmape === undefined ? 'Unavailable' : `${number(score.wmape)}%`,
              ])}
              empty="At least 14 days of history are needed for holdout metrics."
            />
            <p className="text-sm text-muted-foreground mt-4">
              Lower error is better. MAPE excludes zero-demand days. Weighted error is unavailable
              when holdout demand is zero.
            </p>
          </Panel>
          <div className="rounded-lg bg-muted p-4 text-sm text-muted-foreground space-y-2">
            {data.notes.map((note) => (
              <p key={note}>{note}</p>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
