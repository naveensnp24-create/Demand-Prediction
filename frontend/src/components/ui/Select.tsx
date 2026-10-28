import { forwardRef, SelectHTMLAttributes, useId } from 'react'
import { clsx } from 'clsx'
interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
}
export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const generated = useId()
    const fieldId = id || generated
    return (
      <div>
        <label htmlFor={fieldId} className="block text-sm mb-2">
          {label}
        </label>
        <select
          ref={ref}
          id={fieldId}
          aria-invalid={!!error}
          aria-describedby={error ? `${fieldId}-error` : undefined}
          className={clsx('h-10 rounded-lg border bg-background px-3 w-full', className)}
          {...props}
        />
        {error && (
          <p id={`${fieldId}-error`} className="text-red-500 text-sm">
            {error}
          </p>
        )}
      </div>
    )
  },
)
Select.displayName = 'Select'
