import { test, expect } from '@playwright/test';

test.describe('Work Intake System E2E Workflow', () => {
  const uniqueId = `CRM-E2E-${Date.now()}`;

  test('Happy path: Ingest -> Analyse -> Review AI Insights -> Complete', async ({ page }) => {
    await page.goto('/');

    // 1. Verify dashboard header
    await expect(page.getByText('Work Intake System')).toBeVisible();

    // 2. Open Ingest Modal
    await page.getByRole('button', { name: /Ingest Work Item/i }).click();
    await expect(page.getByRole('heading', { name: 'Ingest New Work Item' })).toBeVisible();

    // 3. Fill out form
    await page.getByPlaceholder('e.g. CRM-12345').fill(uniqueId);
    await page.getByPlaceholder('e.g. Missing income document').fill('Income verification required');
    await page.getByPlaceholder('Detailed description from external business system...').fill(
      'Applicant submitted application without latest payslip.'
    );

    // 4. Submit
    await page.getByRole('button', { name: /Ingest Item/i }).click();

    // 5. Verify item appears in list and is selected
    await expect(page.getByText(uniqueId).first()).toBeVisible();
    await expect(page.getByText(/Received/i).first()).toBeVisible();

    // 6. Trigger AI Analysis
    const triggerBtn = page.getByRole('button', { name: /Trigger AI Analysis/i });
    await expect(triggerBtn).toBeVisible();
    await triggerBtn.click();

    // 7. Verify transition to Ready for Review
    await expect(page.getByText('Ready for Review').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('AI Analysis Insight')).toBeVisible();
    await expect(page.getByText(/HIGH PRIORITY/i)).toBeVisible();
    await expect(page.getByText(/DOCUMENT REQUEST/i)).toBeVisible();

    // 8. Complete the work item
    const completeBtn = page.getByRole('button', { name: /Approve & Complete/i });
    await expect(completeBtn).toBeVisible();
    await completeBtn.click();

    // 9. Verify transition to Completed
    await expect(page.getByText('Completed').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Work Item Completed')).toBeVisible();
  });

  test('Failure & Retry Flow: AI failure transitions to FAILED and enables Retry', async ({ page }) => {
    const failId = `CRM-FAIL-${Date.now()}`;
    await page.goto('/');

    // 1. Ingest item with failure trigger
    await page.getByRole('button', { name: /Ingest Work Item/i }).click();
    await page.getByPlaceholder('e.g. CRM-12345').fill(failId);
    await page.getByPlaceholder('e.g. Missing income document').fill('Failed timeout test [SIMULATE_TIMEOUT]');
    await page.getByPlaceholder('Detailed description from external business system...').fill(
      'Testing simulated timeout handling'
    );
    await page.getByRole('button', { name: /Ingest Item/i }).click();

    // 2. Select the item
    await page.getByText(failId).first().click();

    // 3. Trigger analysis
    await page.getByRole('button', { name: /Trigger AI Analysis/i }).click();

    // 4. Verify transition to FAILED
    await expect(page.getByRole('heading', { name: 'AI Analysis Failed' })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Failed').first()).toBeVisible();
    await expect(page.getByText(/timed out/i).first()).toBeVisible();

    // 5. Verify Retry button is visible
    const retryBtn = page.getByRole('button', { name: /Retry Failed Analysis/i });
    await expect(retryBtn).toBeVisible();
  });

  test('Idempotency: Re-submitting existing externalId does not create duplicate', async ({ page }) => {
    const idempotentId = `CRM-IDEM-${Date.now()}`;
    await page.goto('/');

    // First ingestion
    await page.getByRole('button', { name: /Ingest Work Item/i }).click();
    await page.getByPlaceholder('e.g. CRM-12345').fill(idempotentId);
    await page.getByPlaceholder('e.g. Missing income document').fill('Original Title');
    await page.getByPlaceholder('Detailed description from external business system...').fill('Original Desc');
    await page.getByRole('button', { name: /Ingest Item/i }).click();

    await expect(page.getByText(idempotentId).first()).toBeVisible();

    // Second ingestion with duplicate externalId
    await page.getByRole('button', { name: /Ingest Work Item/i }).click();
    await page.getByPlaceholder('e.g. CRM-12345').fill(idempotentId);
    await page.getByPlaceholder('e.g. Missing income document').fill('Modified Title Should Not Overwrite');
    await page.getByPlaceholder('Detailed description from external business system...').fill('Modified Desc');
    await page.getByRole('button', { name: /Ingest Item/i }).click();

    // Verify only one entry exists for this externalId in list
    const items = page.locator(`text=${idempotentId}`);
    await expect(items).toHaveCount(2); // One in list row, one in detail header
    await expect(page.getByRole('heading', { name: 'Original Title', level: 2 })).toBeVisible();
  });
});
