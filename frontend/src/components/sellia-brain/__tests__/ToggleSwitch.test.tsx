import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ToggleSwitch } from '../ToggleSwitch'
import { AutomationToggleResponse } from '@/lib/api/toggles'

const mockToggle: AutomationToggleResponse = {
  id: '123' as any,
  business_id: '456' as any,
  toggle_key: 'agent:lead_scorer',
  category: 'agent',
  display_name: 'Lead Scorer IA',
  description: 'Califica automáticamente leads',
  icon: '🎯',
  is_enabled: true,
  monthly_limit: 1000,
  current_month_usage: 750,
  enabled_at: '2026-09-01T00:00:00Z',
  disabled_at: null,
  created_at: '2026-09-01T00:00:00Z',
  updated_at: '2026-09-01T00:00:00Z',
}

describe('ToggleSwitch', () => {
  const mockOnToggle = jest.fn()
  const mockOnLimitChange = jest.fn()
  const mockOnShowAudit = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders toggle with display name and description', () => {
    render(
      <ToggleSwitch
        toggle={mockToggle}
        onToggle={mockOnToggle}
        onShowAudit={mockOnShowAudit}
      />
    )

    expect(screen.getByText('Lead Scorer IA')).toBeInTheDocument()
    expect(screen.getByText('Califica automáticamente leads')).toBeInTheDocument()
  })

  test('displays usage bar with correct percentage', () => {
    render(
      <ToggleSwitch
        toggle={mockToggle}
        onToggle={mockOnToggle}
        onShowAudit={mockOnShowAudit}
      />
    )

    expect(screen.getByText('750 / 1000')).toBeInTheDocument()
    // 75% usage
    const progressBar = screen.getByRole('progressbar', { hidden: true })
    expect(progressBar).toHaveStyle('width: 75%')
  })

  test('calls onToggle when toggle button clicked', async () => {
    render(
      <ToggleSwitch
        toggle={mockToggle}
        onToggle={mockOnToggle}
        onShowAudit={mockOnShowAudit}
      />
    )

    const toggleButton = screen.getByRole('button', { name: /desactivar/i })
    fireEvent.click(toggleButton)

    await waitFor(() => {
      expect(mockOnToggle).toHaveBeenCalledWith(false)
    })
  })

  test('calls onShowAudit when audit button clicked', () => {
    render(
      <ToggleSwitch
        toggle={mockToggle}
        onToggle={mockOnToggle}
        onShowAudit={mockOnShowAudit}
      />
    )

    const auditButton = screen.getByTitle('Ver historial de cambios')
    fireEvent.click(auditButton)

    expect(mockOnShowAudit).toHaveBeenCalled()
  })

  test('shows limit form when limit button clicked', async () => {
    render(
      <ToggleSwitch
        toggle={mockToggle}
        onToggle={mockOnToggle}
        onLimitChange={mockOnLimitChange}
        onShowAudit={mockOnShowAudit}
      />
    )

    const limitButton = screen.getByText('Límite')
    fireEvent.click(limitButton)

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Límite')).toBeInTheDocument()
    })
  })

  test('displays correct usage color based on percentage', () => {
    // High usage (> 90%)
    const highUsageToggle = { ...mockToggle, current_month_usage: 950 }
    render(
      <ToggleSwitch
        toggle={highUsageToggle}
        onToggle={mockOnToggle}
        onShowAudit={mockOnShowAudit}
      />
    )

    const highUsageBar = screen.getByRole('progressbar', { hidden: true })
    expect(highUsageBar).toHaveClass('bg-red-500')
  })

  test('renders icon correctly', () => {
    render(
      <ToggleSwitch
        toggle={mockToggle}
        onToggle={mockOnToggle}
        onShowAudit={mockOnShowAudit}
      />
    )

    expect(screen.getByText('🎯')).toBeInTheDocument()
  })

  test('disables toggle button when loading', () => {
    render(
      <ToggleSwitch
        toggle={mockToggle}
        loading={true}
        onToggle={mockOnToggle}
        onShowAudit={mockOnShowAudit}
      />
    )

    const toggleButton = screen.getByRole('button', { name: /desactivar/i })
    expect(toggleButton).toBeDisabled()
  })

  test('handles toggle without monthly limit', () => {
    const noLimitToggle = { ...mockToggle, monthly_limit: null }
    render(
      <ToggleSwitch
        toggle={noLimitToggle}
        onToggle={mockOnToggle}
        onShowAudit={mockOnShowAudit}
      />
    )

    // Should not show usage bar
    expect(screen.queryByText('Uso mensual')).not.toBeInTheDocument()
  })
})
