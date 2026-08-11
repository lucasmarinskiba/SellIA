# Phase 26 E2E Tests

End-to-end test suite for Phase 26 (Team Collaboration + Mobile App + Deal Intelligence).

## Test Coverage

### Phase 26a - Collaboration Hub
- `26a-collaboration.spec.ts`
  - Comment posting + real-time display
  - @mention autocomplete
  - Approval workflow (approve/reject)
  - Activity feed
  - Deal selection
  - Shared deals display

### Phase 26b - Mobile App
- `26b-mobile-app.spec.ts`
  - Mobile login (iPhone 12)
  - Dashboard display
  - Tab navigation
  - Touch interactions
  - Tablet responsiveness (iPad Pro)

### Phase 26c - Deal Intelligence
- `26c-deal-intelligence.spec.ts`
  - Intelligence dashboard display
  - KPI cards (at-risk, accuracy, wins, revenue)
  - At-risk deals list
  - Risk level indicators
  - Loss patterns
  - Mobile responsiveness

### API Integration
- `phase26-api.spec.ts`
  - Collaboration endpoints (comment, approval, share)
  - Intelligence endpoints (score, forecast, accuracy)
  - WebSocket connectivity
  - Response validation
  - Error handling

## Setup

Install Playwright:
```bash
npm install -D @playwright/test
```

## Running Tests

### Run all tests
```bash
npx playwright test
```

### Run specific test file
```bash
npx playwright test e2e/26a-collaboration.spec.ts
```

### Run tests in headed mode (browser visible)
```bash
npx playwright test --headed
```

### Run tests in debug mode
```bash
npx playwright test --debug
```

### Run tests on specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
```

### Run tests with UI mode
```bash
npx playwright test --ui
```

## Viewing Results

After running tests:
```bash
npx playwright show-report
```

Reports are generated in `playwright-report/` with screenshots and videos on failure.

## Test Flow

1. **Setup**: Navigate to page, login with test credentials
2. **Action**: Interact with UI (click, type, submit)
3. **Assertion**: Verify expected outcomes (visibility, values, counts)
4. **Cleanup**: Automatic via Playwright fixtures

## Environment Variables

```bash
# Backend API URL
API_URL=http://localhost:8000

# Frontend URL
BASE_URL=http://localhost:50554

# Test credentials
TEST_EMAIL=test@example.com
TEST_PASSWORD=password123
```

## Troubleshooting

### Tests fail to connect to API
- Ensure backend is running: `npm run dev` in backend directory
- Check API_URL in playwright.config.ts

### Tests fail to connect to frontend
- Ensure frontend is running: `npm run dev` in frontend directory
- Check BASE_URL in playwright.config.ts

### Mobile tests fail
- Mobile emulation uses Chromium on desktop
- No physical device required

### WebSocket tests timeout
- WebSocket may not be available in all test environments
- Tests handle gracefully with try/catch

## CI/CD Integration

For GitHub Actions, add to workflow:
```yaml
- name: Run E2E tests
  run: npx playwright test
  
- name: Upload results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: playwright-report
    path: playwright-report/
```

## Performance Benchmarks

Expected test execution times (local machine):
- Phase 26a collaboration tests: ~30s
- Phase 26b mobile tests: ~20s
- Phase 26c intelligence tests: ~25s
- Phase 26 API tests: ~15s

Total: ~90s for full suite

## Known Limitations

1. WebSocket tests may timeout in isolated test environments
2. Push notifications can't be tested in browser automation
3. Offline sync can't be fully tested without network manipulation
4. Some mobile gestures are emulated, not identical to real devices

## Contributing

When adding new tests:
1. Follow existing naming convention: `{phase}-{feature}.spec.ts`
2. Include descriptive test names
3. Add comments for non-obvious assertions
4. Handle async operations with await
5. Clean up resources (logout, reset state)

## Future Improvements

- Add performance profiling tests
- Add accessibility (a11y) tests
- Add security tests (CSRF, XSS)
- Add visual regression tests
- Add load/stress tests
- Add real device testing (via BrowserStack)
