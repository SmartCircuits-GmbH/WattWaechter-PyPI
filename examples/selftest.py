"""Example: Run the IR transceiver self-test."""

import asyncio

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    async with Wattwaechter("192.168.1.100", token="your-read-token") as client:
        print("Running IR transceiver self-test...")
        result = await client.selftest()

        if result.success:
            print(f"  PASS: {result.message}")
        else:
            print(f"  FAIL: {result.message}")
            print(f"  Result: {result.result}")
            print()
            print("Possible causes:")
            print("  - IR transceiver not properly connected")
            print("  - Smart meter not responding")
            print("  - Optical head misaligned")


if __name__ == "__main__":
    asyncio.run(main())
