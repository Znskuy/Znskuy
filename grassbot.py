import asyncio
import json
import ssl
import time
import uuid
import aiohttp
from loguru import logger

async def connect_to_wss(user_id):
    device_id = str(uuid.uuid4())
    logger.info(f"Device ID: {device_id}")

    while True:
        try:
            await asyncio.sleep(1)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            uri = "wss://proxy.wynd.network:4650/"
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.ws_connect(uri, ssl=ssl_context, headers=custom_headers) as websocket:
                        logger.info("Connected to WebSocket")

                        async def send_ping():
                            while True:
                                send_message = json.dumps({
                                    "id": str(uuid.uuid4()),
                                    "version": "1.0.0",
                                    "action": "PING",
                                    "data": {}
                                })
                                logger.debug(f"Sending PING: {send_message}")
                                try:
                                    await websocket.send_str(send_message)
                                    await asyncio.sleep(20)
                                except aiohttp.client_exceptions.ClientConnectionResetError:
                                    logger.error("Connection reset while sending PING. Reconnecting...")
                                    break  # Break the loop to reconnect

                        asyncio.create_task(send_ping())

                        while True:
                            try:
                                response = await websocket.receive()
                                message = json.loads(response.data)  # Tidak perlu decode jika sudah string
                                logger.info(f"Received message: {message}")

                                if message.get("action") == "AUTH":
                                    auth_response = {
                                        "id": message["id"],
                                        "origin_action": "AUTH",
                                        "result": {
                                            "browser_id": device_id,
                                            "user_id": user_id,
                                            "user_agent": custom_headers['User-Agent'],
                                            "timestamp": int(time.time()),
                                            "device_type": "desktop",
                                            "version": "2.5.0",
                                            "ip_address": "",
                                            "ip_score": 100,
                                            "agg_uptime": 223935,
                                            "ipString": "",
                                            "ipType": "IPv4"
                                        }
                                    }
                                    logger.debug(f"Sending AUTH Response: {auth_response}")
                                    await websocket.send_json(auth_response)

                                elif message.get("action") == "PONG":
                                    pong_response = {"id": message["id"], "origin_action": "PONG"}
                                    logger.debug(f"Sending PONG: {pong_response}")
                                    await websocket.send_json(pong_response)

                            except asyncio.CancelledError:
                                break  # Exit the loop if the connection is canceled
                            except Exception as e:
                                logger.error(f"Error receiving message: {e}")
                                break  # Break the loop to reconnect

                except aiohttp.ClientConnectionError as e:
                    logger.error(f"WebSocket connection error: {e}")
                    await asyncio.sleep(5)  # Wait for a while before reconnecting
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error: {e}")

async def main():
    _user_id = 'ID_MU'
    await connect_to_wss(_user_id)

if __name__ == '__main__':
    asyncio.run(main())
