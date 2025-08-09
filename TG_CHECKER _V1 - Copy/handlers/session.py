# handlers/session.py
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact
from utils.session_utils import get_telethon_client, increment_check_count, get_check_count, delete_user_session
from utils.logger import log_user_action

MAX_CHECKS_PER_SESSION = 120

async def check_telegram_numbers(user_id: int, numbers_list: list[str]) -> str:
    client = get_telethon_client(user_id)
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return "⚠️ Your session is not authorized. Please add your session again."
    except Exception as e:
        log_user_action(user_id, f"❌ Failed to connect Telethon client: {e}")
        return "⚠️ Could not connect to Telegram client. Please try again."

    valid_users = []
    invalid_users = []

    already_checked = get_check_count(user_id)
    remaining = MAX_CHECKS_PER_SESSION - already_checked
    numbers_list = numbers_list[:remaining]

    for batch_index in range(0, len(numbers_list), 10):
        batch = numbers_list[batch_index:batch_index + 10]
        contacts = [
            InputPhoneContact(client_id=idx, phone=number, first_name="Check", last_name="Bot")
            for idx, number in enumerate(batch)
        ]

        try:
            result = await client(ImportContactsRequest(contacts))
        except Exception as e:
            log_user_action(user_id, f"⚠️ Failed to import contacts: {e}")
            invalid_users.extend(batch)
            continue

        imported_users = result.users or []
        valid_batch = [user.phone for user in imported_users if user.phone]
        invalid_batch = [c.phone for c in contacts if c.phone not in valid_batch]

        valid_users.extend(valid_batch)
        invalid_users.extend(invalid_batch)

        if imported_users:
            try:
                await client(DeleteContactsRequest(id=imported_users))
            except Exception as e:
                log_user_action(user_id, f"⚠️ Could not delete contacts: {e}")

        increment_check_count(user_id, len(batch))

        # Auto-logout when limit reached
        if get_check_count(user_id) >= MAX_CHECKS_PER_SESSION:
            delete_user_session(user_id)
            log_user_action(user_id, f"⛔ Session auto-deleted after reaching {MAX_CHECKS_PER_SESSION}/{MAX_CHECKS_PER_SESSION} checks")
            break

    await client.disconnect()

    # Build final report
    report_parts = ["✨ <b>Check Complete! Here is your report:</b>"]

    report_parts.append(f"\n✅ <b>Registered Users ({len(valid_users)})</b>")
    report_parts.extend([f"<code>{v}</code>" for v in valid_users] if valid_users else ["<i>None</i>"])

    report_parts.append(f"\n❌ <b>Not Registered ({len(invalid_users)})</b>")
    report_parts.extend([f"<code>{v}</code>" for v in invalid_users] if invalid_users else ["<i>None</i>"])

    return "\n".join(report_parts)
