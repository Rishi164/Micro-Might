import { expect, test } from '@playwright/test';

test('customer account, saved address, and Bengaluru COD checkout', async ({ page }) => {
  const email = `shopper-${Date.now()}-${Math.random().toString(36).slice(2)}@example.com`;
  const password = 'GreensTest2026!';

  await page.goto('/login');
  await page.getByTestId('customer-signup-tab').click();
  await page.getByTestId('customer-name-input').fill('Micro Might Shopper');
  await page.getByTestId('customer-phone-input').fill('9900011223');
  await page.getByTestId('customer-email-input').fill(email);
  await page.getByTestId('customer-password-input').fill(password);
  await page.getByTestId('customer-auth-submit-button').click();
  await expect(page).toHaveURL(/\/account$/);

  await page.getByTestId('customer-home-address-input').fill('24 Fresh Harvest Road, Gottigere, Bengaluru');
  await page.getByTestId('customer-home-pincode-input').fill('560083');
  await page.getByTestId('customer-home-distance-input').fill('2.5');
  await page.getByTestId('customer-save-address-button').click();
  await expect(page.getByTestId('customer-save-address-button')).toHaveText(/address saved/i);

  await page.getByTestId('customer-logout-button').click();
  await page.goto('/login');
  await page.getByTestId('customer-email-input').fill(email);
  await page.getByTestId('customer-password-input').fill(password);
  await page.getByTestId('customer-auth-submit-button').click();
  await expect(page).toHaveURL(/\/account$/);
  await expect(page.getByTestId('customer-home-pincode-input')).toHaveValue('560083');

  await page.goto('/microgreens');
  await page.getByRole('button', { name: /add to cart/i }).first().click();
  await page.goto('/checkout');
  await expect(page.getByTestId('checkout-pincode-input')).toHaveValue('560083');

  await page.getByTestId('checkout-pincode-input').fill('110001');
  await expect(page.getByTestId('checkout-payment-cod')).toBeDisabled();
  await page.getByTestId('checkout-pincode-input').fill('560083');
  await expect(page.getByTestId('checkout-payment-cod')).toBeEnabled();
  await page.getByTestId('checkout-payment-cod').click();

  const deliveryDate = new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  await page.getByTestId('checkout-preferred-date-input').fill(deliveryDate);
  await page.getByTestId('checkout-submit-button').click();
  await expect(page.getByTestId('order-success')).toBeVisible();
  await expect(page.getByTestId('order-success-title')).toContainText('Micro Might Shopper');
});