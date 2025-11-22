/**
 * Component tests for RemediationProposalCard.
 * 
 * Tests the remediation proposal UI component, including:
 * - "What will happen" section rendering
 * - Confirmation dialog for expensive actions
 * - Button states and actions
 * - Auto-upgrade message handling
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import RemediationProposalCard from '../RemediationProposalCard'
import { RemediationProposal } from '@/lib/api'
import * as issuesApi from '@/lib/api'

// Mock the API
jest.mock('@/lib/api', () => ({
  issuesApi: {
    resolve: jest.fn(),
  },
}))

// Mock useToast hook
jest.mock('@/hooks/useToast', () => ({
  useToast: () => ({
    success: jest.fn(),
    error: jest.fn(),
  }),
}))

const mockQueryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={mockQueryClient}>
    {children}
  </QueryClientProvider>
)

describe('RemediationProposalCard', () => {
  const defaultProposal: RemediationProposal = {
    action_type: 'patch_and_rescore',
    description: 'Update ProblemSpec and re-score candidates',
    estimated_impact: 'Will affect all candidates',
    rationale: 'Minor issue can be fixed quickly',
  }

  const defaultProps = {
    proposal: defaultProposal,
    issueId: 'test-issue-id',
    projectId: 'test-project-id',
    chatSessionId: 'test-chat-session-id',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockQueryClient.clear()
  })

  describe('"What will happen" section', () => {
    it('displays action explanation for patch_and_rescore', () => {
      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} />
        </TestWrapper>
      )

      expect(screen.getByText(/what will happen:/i)).toBeInTheDocument()
      expect(screen.getByText(/update the problemspec or worldmodel/i)).toBeInTheDocument()
      expect(screen.getByText(/fast \(seconds to minutes\)/i)).toBeInTheDocument()
      expect(screen.getByText(/low cost/i)).toBeInTheDocument()
    })

    it('displays action explanation for full_rerun', () => {
      const fullRerunProposal = {
        ...defaultProposal,
        action_type: 'full_rerun' as const,
      }

      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} proposal={fullRerunProposal} />
        </TestWrapper>
      )

      expect(screen.getByText(/slow \(several minutes to hours\)/i)).toBeInTheDocument()
      expect(screen.getByText(/high cost/i)).toBeInTheDocument()
    })

    it('displays action explanation for partial_rerun', () => {
      const partialRerunProposal = {
        ...defaultProposal,
        action_type: 'partial_rerun' as const,
      }

      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} proposal={partialRerunProposal} />
        </TestWrapper>
      )

      expect(screen.getByText(/moderate \(minutes\)/i)).toBeInTheDocument()
      expect(screen.getByText(/moderate cost/i)).toBeInTheDocument()
    })

    it('displays action explanation for invalidate_candidates', () => {
      const invalidateProposal = {
        ...defaultProposal,
        action_type: 'invalidate_candidates' as const,
      }

      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} proposal={invalidateProposal} />
        </TestWrapper>
      )

      expect(screen.getByText(/instant/i)).toBeInTheDocument()
      expect(screen.getByText(/no cost/i)).toBeInTheDocument()
    })
  })

  describe('Confirmation dialog for expensive actions', () => {
    it('shows confirmation dialog for full_rerun actions', async () => {
      const fullRerunProposal = {
        ...defaultProposal,
        action_type: 'full_rerun' as const,
      }

      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} proposal={fullRerunProposal} />
        </TestWrapper>
      )

      const approveButton = screen.getByRole('button', { name: /approve & start full run/i })
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(screen.getByText(/confirm full run/i)).toBeInTheDocument()
        expect(screen.getByText(/this will create a completely new run from scratch/i)).toBeInTheDocument()
        expect(screen.getByText(/this may take several minutes to hours/i)).toBeInTheDocument()
      })
    })

    it('does not show confirmation dialog for patch_and_rescore', () => {
      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} />
        </TestWrapper>
      )

      const approveButton = screen.getByRole('button', { name: /approve & apply/i })
      fireEvent.click(approveButton)

      expect(screen.queryByText(/confirm full run/i)).not.toBeInTheDocument()
    })

    it('cancels confirmation dialog when cancel button clicked', async () => {
      const fullRerunProposal = {
        ...defaultProposal,
        action_type: 'full_rerun' as const,
      }

      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} proposal={fullRerunProposal} />
        </TestWrapper>
      )

      const approveButton = screen.getByRole('button', { name: /approve & start full run/i })
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(screen.getByText(/confirm full run/i)).toBeInTheDocument()
      })

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      fireEvent.click(cancelButton)

      await waitFor(() => {
        expect(screen.queryByText(/confirm full run/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Button states and actions', () => {
    it('shows red button for full_rerun actions', () => {
      const fullRerunProposal = {
        ...defaultProposal,
        action_type: 'full_rerun' as const,
      }

      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} proposal={fullRerunProposal} />
        </TestWrapper>
      )

      const approveButton = screen.getByRole('button', { name: /approve & start full run/i })
      expect(approveButton).toHaveClass('bg-red-600')
    })

    it('shows green button for safe actions like patch_and_rescore', () => {
      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} />
        </TestWrapper>
      )

      const approveButton = screen.getByRole('button', { name: /approve & apply/i })
      expect(approveButton).toHaveClass('bg-green-600')
    })

    it('calls resolve API when approve button clicked', async () => {
      const mockResolve = issuesApi.issuesApi.resolve as jest.Mock
      mockResolve.mockResolvedValue({
        status: 'success',
        message: 'Remediation applied successfully',
        issue_id: 'test-issue-id',
        remediation_action: 'patch_and_rescore',
        result: {},
      })

      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} />
        </TestWrapper>
      )

      const approveButton = screen.getByRole('button', { name: /approve & apply/i })
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(mockResolve).toHaveBeenCalledWith(
          'test-issue-id',
          'patch_and_rescore',
          expect.objectContaining({
            problem_spec: undefined,
            world_model: undefined,
          })
        )
      })
    })
  })

  describe('Auto-upgrade message handling', () => {
    it('displays auto-upgrade message when action is upgraded', async () => {
      const mockResolve = issuesApi.issuesApi.resolve as jest.Mock
      mockResolve.mockResolvedValue({
        status: 'success',
        message: 'Issue resolved with action \'full_rerun\'',
        issue_id: 'test-issue-id',
        remediation_action: 'full_rerun',
        original_remediation_action: 'patch_and_rescore',
        action_upgraded: true,
        result: {},
      })

      const { useToast } = require('@/hooks/useToast')
      const mockSuccess = jest.fn()
      useToast.mockReturnValue({
        success: mockSuccess,
        error: jest.fn(),
      })

      render(
        <TestWrapper>
          <RemediationProposalCard {...defaultProps} />
        </TestWrapper>
      )

      const approveButton = screen.getByRole('button', { name: /approve & apply/i })
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(mockSuccess).toHaveBeenCalledWith(
          expect.stringContaining('auto-upgraded')
        )
      })
    })
  })
})

