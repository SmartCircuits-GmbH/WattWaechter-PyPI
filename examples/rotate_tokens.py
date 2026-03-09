"""Example: Rotate API tokens.

The token rotation is a two-phase process:
1. Generate new tokens (pending for 60 seconds)
2. Confirm with the new WRITE token to activate them

This prevents lockout if the response to step 1 is lost.

Note: This requires a WRITE token (authentication must be enabled).
"""

import asyncio

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    # Token rotation requires an existing WRITE token
    async with Wattwaechter("192.168.1.100", token="your-write-token") as client:
        # Phase 1: Generate new tokens
        result = await client.generate_tokens()
        print(f"New READ token:  {result.token_read}")
        print(f"New WRITE token: {result.token_write}")
        print(f"Expires in:      {result.expires_in}s")
        print()

        confirm = input("Confirm token rotation? (y/N): ")
        if confirm.lower() != "y":
            print("Cancelled. Old tokens remain active.")
            return

        # Phase 2: Confirm with the new WRITE token
        success = await client.confirm_tokens(result.token_write)
        if success:
            print("Tokens activated! Save your new tokens:")
            print(f"  READ:  {result.token_read}")
            print(f"  WRITE: {result.token_write}")
        else:
            print("Confirmation failed. Old tokens remain active.")


if __name__ == "__main__":
    asyncio.run(main())
