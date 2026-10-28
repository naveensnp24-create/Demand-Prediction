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
import { useData, Prediction, Profile, number, money, exportCSV } from '@/lib/api'

export function Customer() {
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState('')
  const [horizon, setHorizon] = useState(30)
  const customers = useData<{
    customers: { customer_id: string; name: string; email: string }[]
    total: number
  }>(`/customers?q=${encodeURIComponent(search)}`)
  const profile = useData<Profile>(selected ? `/customers/${encodeURIComponent(selected)}` : null)
  const prediction = useData<Prediction>(
    selected ? `/predict/customer/${encodeURIComponent(selected)}?horizon_days=${horizon}` : null,
  )
  const data = prediction.data
  return (
    <div className="space-y-6">
      <PageHeader
        title="Customer intelligence"
        description="Find a customer, understand their history, and explore personalized product recommendations."
      />
      <Panel title="Find a customer">
        <form
          className="flex flex-wrap items-end gap-3"
          onSubmit={(e) => {
            e.preventDefault()
            setSearch(query.trim())
          }}
        >
          <div className="flex-1 min-w-48">
            <Field label="Search by name, email, or customer ID">
              <input
                className={fieldClass}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. CUST_000001"
              />
            </Field>
          </div>
          <Button type="submit">Search</Button>
        </form>
        <RequestState
          loading={customers.loading}
          error={customers.error}
          retry={customers.refresh}
        />
        {customers.data && (
          <>
            <p className="text-xs text-muted-foreground mt-4">
              Showing {customers.data.customers.length} of {customers.data.total} matches. Refine
              your search to find a specific customer.
            </p>
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-2 mt-3">
              {customers.data.customers.map((customer) => (
                <button
                  key={customer.customer_id}
                  onClick={() => setSelected(customer.customer_id)}
                  aria-pressed={selected === customer.customer_id}
                  className={`text-left rounded-lg border p-3 ${selected === customer.customer_id ? 'border-primary bg-primary/10' : 'hover:bg-accent'}`}
                >
                  <span className="font-medium block">{customer.name}</span>
                  <span className="block text-xs text-muted-foreground">
                    {customer.customer_id}
                  </span>
                </button>
              ))}
            </div>
            {!customers.data.customers.length && (
              <p className="py-4 text-muted-foreground">
                No customers found. Try another search or import customers in Settings.
              </p>
            )}
          </>
        )}
      </Panel>
      <RequestState loading={profile.loading} error={profile.error} retry={profile.refresh} />
      {profile.data && (
        <Panel title={profile.data.name}>
          <div className="flex flex-wrap justify-between gap-4">
            <div>
              <p>{profile.data.email}</p>
              <p className="text-muted-foreground text-sm mt-1">
                {profile.data.customer_id} | {profile.data.city} | Joined{' '}
                {profile.data.signup_date.slice(0, 10)}
              </p>
            </div>
            <Field label="Recommendation horizon">
              <select
                className={fieldClass}
                value={horizon}
                onChange={(e) => setHorizon(Number(e.target.value))}
              >
                {[7, 30, 60, 90].map((days) => (
                  <option key={days} value={days}>
                    {days} days
                  </option>
                ))}
              </select>
            </Field>
          </div>
        </Panel>
      )}
      <RequestState
        loading={prediction.loading}
        error={prediction.error}
        retry={prediction.refresh}
      />
      {data && (
        <>
          <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <Metric label="Behavior segment" value={data.segment.replaceAll('_', ' ')} />
            <Metric
              label="Recency"
              value={`${number(data.rfm_scores.recency)} days`}
              detail={`As of ${data.as_of}`}
            />
            <Metric label="Purchase sessions" value={number(data.rfm_scores.frequency)} />
            <Metric label="Historical spend" value={money(data.rfm_scores.monetary)} />
          </div>
          <Panel title="Recommended products">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-muted-foreground">
                Estimated purchase probability over {horizon} days.
              </p>
              <Button
                variant="outline"
                onClick={() =>
                  exportCSV(
                    'recommendations.csv',
                    ['Product', 'Probability', 'Expected quantity', 'Expected revenue INR'],
                    data.recommendations.map((row) => [
                      row.product_name,
                      row.purchase_probability,
                      row.expected_quantity,
                      row.expected_revenue,
                    ]),
                  )
                }
              >
                Export recommendations
              </Button>
            </div>
            <DataTable
              headers={[
                'Product',
                'Price',
                'Probability',
                'Expected units',
                'Expected revenue',
                'Main drivers',
              ]}
              rows={data.recommendations.map((row) => [
                <div key="name">
                  <p className="font-medium">{row.product_name}</p>
                  <p className="text-xs text-muted-foreground">{row.category}</p>
                </div>,
                money(row.price),
                `${(row.purchase_probability * 100).toFixed(1)}%`,
                row.expected_quantity.toFixed(2),
                money(row.expected_revenue),
                <details key="drivers">
                  <summary className="cursor-pointer text-primary">
                    {row.shap_explanations.length ? 'Explain prediction' : 'History baseline'}
                  </summary>
                  <div className="space-y-1 mt-2 min-w-48">
                    {row.shap_explanations.map((item) => (
                      <p key={item.feature} className="text-xs">
                        {item.feature.replaceAll('_', ' ')}: {item.shap_value > 0 ? '+' : ''}
                        {item.shap_value.toFixed(3)}
                      </p>
                    ))}
                    {!row.shap_explanations.length && (
                      <p className="text-xs">Not enough history to train a temporal model.</p>
                    )}
                  </div>
                </details>,
              ])}
            />
          </Panel>
          <div className="bg-muted rounded-lg p-4 text-sm space-y-2">
            <p>
              <strong>Method:</strong> {data.model_report.method.replaceAll('_', ' ')}.{' '}
              {data.model_report.note}
            </p>
            <p>
              Drivers are independent-feature linear SHAP contributions to 30-day log odds. Expected
              units and revenue include purchase probability. Horizon adjustment assumes a constant
              purchase hazard.
            </p>
            {data.model_report.validation.roc_auc !== undefined && (
              <p>
                Temporal holdout ROC AUC: {data.model_report.validation.roc_auc.toFixed(3)} | Brier
                score: {data.model_report.validation.brier_score?.toFixed(4)}
              </p>
            )}
          </div>
        </>
      )}
      {profile.data && (
        <Panel title="Recent activity">
          <DataTable
            headers={['Date', 'Event', 'Product', 'Value']}
            rows={profile.data.timeline.map((row) => [
              row.date.slice(0, 16).replace('T', ' '),
              row.event.replaceAll('_', ' '),
              row.product,
              money(row.value),
            ])}
            empty="This customer has no recorded browsing activity."
          />
        </Panel>
      )}
    </div>
  )
}
