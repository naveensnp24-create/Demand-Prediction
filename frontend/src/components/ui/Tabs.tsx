import {
  createContext,
  useContext,
  useId,
  useState,
  ReactNode,
  HTMLAttributes,
  ButtonHTMLAttributes,
} from 'react'
import { clsx } from 'clsx'
const Context = createContext<{
  value: string
  setValue: (value: string) => void
  id: string
} | null>(null)
export function Tabs({
  defaultValue,
  onValueChange,
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement> & {
  defaultValue: string
  onValueChange?: (value: string) => void
}) {
  const [value, setValue] = useState(defaultValue)
  const id = useId()
  return (
    <Context.Provider
      value={{
        value,
        id,
        setValue: (next) => {
          setValue(next)
          onValueChange?.(next)
        },
      }}
    >
      <div className={className} {...props}>
        {children}
      </div>
    </Context.Provider>
  )
}
export function TabsList(props: HTMLAttributes<HTMLDivElement>) {
  return <div role="tablist" {...props} />
}
export function TabsTrigger({
  value,
  children,
  className,
  ...props
}: Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'value'> & {
  value: string
  children: ReactNode
}) {
  const context = useContext(Context)
  return (
    <button
      {...props}
      type="button"
      role="tab"
      id={`${context?.id}-tab-${value}`}
      aria-controls={`${context?.id}-panel-${value}`}
      aria-selected={context?.value === value}
      className={clsx(
        'px-4 py-2 rounded-lg',
        context?.value === value && 'bg-primary text-primary-foreground',
        className,
      )}
      onClick={() => context?.setValue(value)}
    >
      {children}
    </button>
  )
}
export function TabsContent({
  value,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { value: string }) {
  const context = useContext(Context)
  return context?.value === value ? (
    <div
      role="tabpanel"
      id={`${context.id}-panel-${value}`}
      aria-labelledby={`${context.id}-tab-${value}`}
      {...props}
    >
      {children}
    </div>
  ) : null
}
