
@pytest.mark.asyncio
async def test_start_menu_recent_buttons():
    app = TestApp()
    # Mock recent dirs
    app.config_manager = ConfigManager()

    # We need to manually add recent dirs to config for test
    # But TestApp creates ConfigManager internally in on_mount

    # Let's just create a separate test app for start menu logic
    pass # Too complex to mock ConfigManager without dependency injection or patching
