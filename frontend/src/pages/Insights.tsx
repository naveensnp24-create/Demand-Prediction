import { useState } from 'react'
import {
  PageHeader,
  Panel,
  Metric,
  RequestState,
  DataTable,
  Field,
  fieldClass,
} from '@/components/Dashboard'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useData, InsightsData, number, money, exportCSV } from '@/lib/api'

export function Insights() {
  const [horizon, setHorizon] = useState(30)
  const [filter, setFilter] = useState('all')
  const result = useData<InsightsData>(`/insights?days_ahead=${horizon}`)
  const data = result.data
  const rows =
    data?.inventory_recommendations.filter(
      (row) =>
        filter === 'all' ||
        (filter === 'stockout'
          ? row.stockout_risk !== 'low'
          : filter === 'overstock'
            ? row.overstock_risk === 'high'
            : row.trend === filter),
    ) || []
  return (
    <div className="space-y-6">
      <PageHeader
        title="Inventory insights"
        description="Identify stock risks, changing demand, and suggested reorder quantities."
      >
        <Button variant="outline" onClick={result.refresh}>
          Refresh
        </Button>
        <Button
          disabled={!rows.length}
          onClick={() =>
            exportCSV(
              'inventory-plan.csv',
              [
                'Product ID',
                'Product',
                'Current stock',
                'Predicted demand',
                'Stockout risk',
                'Overstock risk',
                'Reorder quantity',
                'Trend',
              ],
              rows.map((row) => [
                row.product_id,
                row.product_name,
                row.current_stock,
                row.predicted_demand,
                row.stockout_risk,
                row.overstock_risk,
                row.suggested_reorder_qty,
                row.trend,
              ]),
            )
          }
        >
          Export inventory plan
        </Button>
      </PageHeader>
      <div className="grid sm:grid-cols-2 gap-4 max-w-2xl">
        <Field label="Planning horizon">
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className={fieldClass}
          >
            {[7, 14, 30, 60, 90].map((days) => (
              <option key={days} value={days}>
                {days} days
              </option>
            ))}
          </select>
        </Field>
        <Field label="Show products">
          <select value={filter} onChange={(e) => setFilter(e.target.value)} className={fieldClass}>
            <option value="all">All products</option>
            <option value="stockout">Stockout risk</option>
            <option value="overstock">Overstock risk</option>
            <option value="rising">Rising demand</option>
            <option value="falling">Falling demand</option>
          </select>
        </Field>
      </div>
      <RequestState loading={result.loading} error={result.error} retry={result.refresh} />
      {data && (
        <>
          <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <Metric
              label="Stockout risks"
              value={data.stockout_risk_products.length}
              detail={`Within ${horizon} days`}
            />
            <Metric
              label="Overstock risks"
              value={data.overstock_risk_products.length}
              detail="More than 90 days of stock"
            />
            <Metric
              label="Suggested reorder units"
              value={number(
                data.inventory_recommendations.reduce(
                  (sum, row) => sum + row.suggested_reorder_qty,
                  0,
                ),
              )}
            />
            <Metric
              label="Potential demand revenue"
              value={money(
                data.inventory_recommendations.reduce((sum, row) => sum + row.revenue_potential, 0),
              )}
              detail="Forecast units multiplied by product price"
            />
          </div>
          <Panel title="Product inventory plan">
            <DataTable
              headers={[
                'Product',
                'Stock',
                'Demand',
                'Stockout risk',
                'Overstock',
                'Reorder units',
                'Trend',
              ]}
              rows={rows.map((row) => [
                <div key="name">
                  <p className="font-medium">{row.product_name}</p>
                  <p className="text-xs text-muted-foreground">{row.category}</p>
                </div>,
                number(row.current_stock),
                number(row.predicted_demand),
                <Badge
                  key="risk"
                  variant={
                    row.stockout_risk === 'high'
                      ? 'destructive'
                      : row.stockout_risk === 'medium'
                        ? 'warning'
                        : 'secondary'
                  }
                >
                  {row.stockout_risk}
                </Badge>,
                row.overstock_risk,
                number(row.suggested_reorder_qty),
                row.trend,
              ])}
            />
          </Panel>
          <p className="text-sm text-muted-foreground rounded-lg bg-muted p-4">
            Data through {data.as_of}. {data.method}. Estimates assume the stock snapshot is current
            for that dataset date. Reorder suggestions are planning quantities; they do not place
            orders.
          </p>
        </>
      )}
    </div>
  )
}
