# path: tools/webui_debugger.py
# version: v0.1
import asyncio
import json
import os
import sys
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

async def debug_webui(url: str, output_dir: str):
    print(f"--- Starting WebUI Debugger for {url} ---")
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_filepath = os.path.join(output_dir, f"webui_debug_{timestamp}.json")
    screenshot_filepath = os.path.join(output_dir, f"webui_debug_{timestamp}.png")

    debug_data = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "console_logs": [],
        "network_requests": [],
        "screenshot_path": screenshot_filepath,
        "error": None
    }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Capture console logs
            page.on("console", lambda msg: debug_data["console_logs"].append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            }))

            # Capture network requests
            page.on("request", lambda request: debug_data["network_requests"].append({
                "url": request.url,
                "method": request.method,
                "headers": request.headers,
                "post_data": request.post_data
            }))
            page.on("response", lambda response: debug_data["network_requests"][-1].update({ # Update last request
                "status": response.status,
                "status_text": response.status_text,
                "response_headers": response.headers,
                "response_body_preview": response.text() if response.ok else None # Get body only if successful
            }) if debug_data["network_requests"] else None)

            await page.goto(url, wait_until="networkidle")
            
            # Capture screenshot
            await page.screenshot(path=screenshot_filepath)
            print(f"Screenshot saved to {screenshot_filepath}")

            await browser.close()

    except PlaywrightTimeoutError:
        debug_data["error"] = f"Navigation to {url} timed out."
        print(f"⚠️ Error: {debug_data['error']}")
    except Exception as e:
        debug_data["error"] = f"An unexpected error occurred: {e}"
        print(f"⚠️ Error: {debug_data['error']}")
    finally:
        with open(log_filepath, "w", encoding="utf-8") as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)
        print(f"Debug log saved to {log_filepath}")
        print("--- WebUI Debugger Complete ---")

if __name__ == "__main__":
    # Default values for debugging
    target_url = os.getenv("WEBUI_URL", "http://localhost:3000")
    output_log_dir = os.getenv("WEBUI_DEBUG_LOG_DIR", os.path.join(os.path.dirname(__file__), "..", "webui_debug_logs"))
    
    # Ensure the output directory exists
    os.makedirs(output_log_dir, exist_ok=True)

    asyncio.run(debug_webui(target_url, output_log_dir))
