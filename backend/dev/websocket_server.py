# path: backend/dev/websocket_server.py
# version: v1
"""
WebSocketサーバー: Dashboardと接続してリアルタイムログ送信
"""
import asyncio, json, websockets, os

async def send_logs(websocket, path):
    print("📡 Client connected:", path)
    log_path = "./logs/self_healing_daemon.log"
    last_size = 0

    while True:
        await asyncio.sleep(2)
        if not os.path.exists(log_path):
            continue
        current_size = os.path.getsize(log_path)
        if current_size > last_size:
            with open(log_path, "r", encoding="utf-8") as f:
                f.seek(last_size)
                new_data = f.read().strip()
                if new_data:
                    for line in new_data.splitlines():
                        await websocket.send(line)
            last_size = current_size

async def main():
    async with websockets.serve(send_logs, "localhost", 8765):
        print("🌐 WebSocket server running at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
