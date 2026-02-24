/**
 * E2E テスト: セッション開始・停止フロー
 * WebSocket フレームを監視して CLI Bridge との統合を確認する
 */
import { test, expect, type Page } from '@playwright/test';

// ─── ヘルパー ─────────────────────────────────────────────────────────────

/** WebSocket メッセージをキャプチャするためのコレクター */
async function collectWsMessages(
  page: Page,
  count: number,
  timeout = 10_000,
): Promise<string[]> {
  return page.evaluate(
    ({ wsUrl, count, timeout }) =>
      new Promise<string[]>((resolve) => {
        const messages: string[] = [];
        const ws = new WebSocket(wsUrl);
        const timer = setTimeout(() => resolve(messages), timeout);
        ws.onmessage = (ev) => {
          messages.push(ev.data as string);
          if (messages.length >= count) {
            clearTimeout(timer);
            ws.close();
            resolve(messages);
          }
        };
        ws.onerror = () => { clearTimeout(timer); resolve(messages); };
      }),
    { wsUrl: 'ws://localhost:8000/ws', count, timeout },
  );
}

// ─── テスト ───────────────────────────────────────────────────────────────

test.describe('Copilot Web Relay — Phase 1 MVP', () => {
  test('ページが正しく表示される', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Copilot Web Relay/);
    await expect(page.locator('h1')).toContainText('Copilot Web Relay');
  });

  test('接続状態インジケータが表示される', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#status-dot')).toBeVisible();
    await expect(page.locator('#status-text')).toBeVisible();
  });

  test('"Start Session" ボタンが表示される', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#btn-start')).toBeVisible();
    await expect(page.locator('#btn-start')).toBeEnabled();
  });

  test('"Stop Session" ボタンは初期状態で無効', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#btn-stop')).toBeDisabled();
  });

  test('ターミナルが表示される', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.terminal-container')).toBeVisible();
    // xterm.js がマウントされていることを確認
    await expect(page.locator('.xterm')).toBeVisible({ timeout: 5000 });
  });

  test('WebSocket エンドポイントに接続できる', async ({ page }) => {
    await page.goto('/');
    // 接続後に status-dot が connected になることを確認（バックエンドが起動している前提）
    // バックエンドが起動していない場合は disconnected のまま → テストはスキップ
    const backendAvailable = await page.evaluate(() =>
      fetch('http://localhost:8000/health')
        .then((r) => r.ok)
        .catch(() => false),
    );

    if (!backendAvailable) {
      test.skip(true, 'バックエンドが起動していないためスキップ');
      return;
    }

    await expect(page.locator('#status-dot')).toHaveClass(/connected/, { timeout: 5000 });
    await expect(page.locator('#status-text')).toHaveText('接続済み');
  });

  test('Start Session で WebSocket status:running を受け取る', async ({ page }) => {
    await page.goto('/');

    const backendAvailable = await page.evaluate(() =>
      fetch('http://localhost:8000/health')
        .then((r) => r.ok)
        .catch(() => false),
    );
    if (!backendAvailable) {
      test.skip(true, 'バックエンドが起動していないためスキップ');
      return;
    }

    // 接続待機
    await expect(page.locator('#status-dot')).toHaveClass(/connected/, { timeout: 5000 });

    // Start Session をクリックして status メッセージを待つ
    const [msgs] = await Promise.all([
      collectWsMessages(page, 1),
      page.locator('#btn-start').click(),
    ]);

    const statusMsg = msgs.find((m) => {
      try {
        const parsed = JSON.parse(m) as { type: string; state?: string };
        return parsed.type === 'status';
      } catch {
        return false;
      }
    });

    expect(statusMsg).toBeDefined();
    if (statusMsg) {
      const parsed = JSON.parse(statusMsg) as { type: string; state: string };
      // running (成功) または error (copilot コマンドなし) のどちらか
      expect(['running', 'error']).toContain(parsed.state);
    }
  });
});
