import asyncio
from playwright.async_api import async_playwright

async def test_model_fetch():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))
        
        await page.goto('file:///e:/Projects/Bokeman/index.html')
        await page.click('button[title="模型凭证与API配置"]')
        
        # Verify recommended tags
        for m in ['gemini-3.8-flash', 'gemini-4-argon', 'claude-opus-5.5', 'gpt-6-astra', 'deepseek-chat']:
            btn = await page.is_visible(f'button:has-text("{m}")')
            assert btn, f'Recommended model button {m} not visible'
        
        # Click one of the 2026 models
        await page.click('button:has-text("gemini-3.8-flash")')
        val = await page.input_value('input[placeholder*="gemini-3.8-flash"]')
        assert val == 'gemini-3.8-flash', f'Model input not updated: {val}'
        print('[OK] Clicked 2026 recommended model tag successfully.')
        
        # Test Fetch Models button without key
        await page.fill('input[placeholder="sk-..."]', '')
        await page.click('text=拉取可用模型')
        await page.wait_for_timeout(200)
        err_text = await page.is_visible('text=请先输入 API Key')
        assert err_text, 'Error text missing when fetching without key'
        print('[OK] Empty key validation passed.')
        
        # Mock route for /v1/models
        await page.route('**/models', lambda route: route.fulfill(
            status=200,
            content_type='application/json',
            body='''{"data": [{"id": "gemini-3.8-flash"}, {"id": "claude-opus-5.5"}, {"id": "gpt-6-astra"}, {"id": "qwen-2.5-72b"}]}'''
        ))
        
        await page.fill('input[placeholder="sk-..."]', 'sk-mock-key')
        await page.click('text=拉取可用模型')
        await page.wait_for_selector('text=成功拉取到 4 个可用模型')
        print('[OK] Successfully mocked models API fetch.')
        
        # Verify dropdown list contains models
        assert await page.is_visible('text=qwen-2.5-72b'), 'Fetched model not in list'
        
        # Select from list
        await page.click('text=qwen-2.5-72b')
        new_val = await page.input_value('input[placeholder*="gemini-3.8-flash"]')
        assert new_val == 'qwen-2.5-72b', f'Selected model not set: {new_val}'
        print('[OK] Selecting from fetched model pool works perfectly.')
        
        assert len(errors) == 0, f'Page errors: {errors}'
        await browser.close()
        print('SUCCESS: Dynamic models fetch tests passed!')

if __name__ == '__main__':
    asyncio.run(test_model_fetch())
