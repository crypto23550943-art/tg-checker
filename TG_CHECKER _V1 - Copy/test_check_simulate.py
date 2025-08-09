# test_check_simulate.py
import os
import sys
import types
import asyncio

# Ensure project root is on sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# -------------------------
# Create minimal stubs if 'telethon' or 'aiogram' are NOT installed.
# -------------------------
try:
    import telethon  # noqa: F401
except Exception:
    errors_mod = types.ModuleType("telethon.errors")

    class FloodWaitError(Exception):
        def __init__(self, seconds):
            self.seconds = seconds
            super().__init__(f"Flood wait {seconds}s")

    class RPCError(Exception):
        pass

    errors_mod.FloodWaitError = FloodWaitError
    errors_mod.RPCError = RPCError
    sys.modules["telethon.errors"] = errors_mod

    contacts_mod = types.ModuleType("telethon.tl.functions.contacts")

    class ImportContactsRequest:
        def __init__(self, contacts):
            self.contacts = contacts

    class DeleteContactsRequest:
        def __init__(self, id):
            self.id = id

    contacts_mod.ImportContactsRequest = ImportContactsRequest
    contacts_mod.DeleteContactsRequest = DeleteContactsRequest
    sys.modules["telethon.tl.functions.contacts"] = contacts_mod

    types_mod = types.ModuleType("telethon.tl.types")

    class InputPhoneContact:
        def __init__(self, client_id=None, phone=None, first_name=None, last_name=None):
            self.client_id = client_id
            self.phone = phone
            self.first_name = first_name
            self.last_name = last_name

    types_mod.InputPhoneContact = InputPhoneContact
    sys.modules["telethon.tl.types"] = types_mod

try:
    import aiogram  # noqa: F401
except Exception:
    aiogram_mod = types.ModuleType("aiogram")

    class Router:
        pass

    class F:
        class text:
            @staticmethod
            def regexp(pattern):
                return pattern

    aiogram_mod.Router = Router
    aiogram_mod.F = F
    sys.modules["aiogram"] = aiogram_mod

    msg_mod = types.ModuleType("aiogram.types")

    class Message:
        def __init__(self, text="", from_user=None):
            self.text = text
            self.from_user = from_user or types.SimpleNamespace(id=0)

    msg_mod.Message = Message
    sys.modules["aiogram.types"] = msg_mod

# -------------------------
# Import your modules
# -------------------------
from utils import session_utils as sus
from utils import check_number as checkmod

# -------------------------
# Ensure sessions dir and a dummy session file exist
# -------------------------
os.makedirs(os.path.join(project_root, "sessions"), exist_ok=True)
dummy_session_path = os.path.join(project_root, "sessions", "9999.session")
if not os.path.exists(dummy_session_path):
    open(dummy_session_path, "w").close()

# -------------------------
# Fake Telethon client
# -------------------------
class FakeUser:
    def __init__(self, phone, id_):
        self.phone = phone
        self.id = id_


class FakeResult:
    def __init__(self, users):
        self.users = users


class FakeClient:
    def __init__(self, registered_set):
        self.registered_set = set(registered_set)
        self.connected = False

    async def connect(self):
        self.connected = True

    async def disconnect(self):
        self.connected = False

    async def is_user_authorized(self):
        # Always authorized in simulation
        return True

    async def __call__(self, request_obj):
        contacts = getattr(request_obj, "contacts", None)
        if not contacts:
            return FakeResult([])
        found = []
        for c in contacts:
            phone_digits = c.phone.lstrip("+")
            if phone_digits in self.registered_set:
                found.append(FakeUser(phone_digits, id_=hash(phone_digits) % 10_000))
        return FakeResult(found)


# Simulated "registered" numbers
registered_numbers = {
    "254792813919",
    "254742635684",
    "254710527431",
    "254757384947",
}

# -------------------------
# Monkeypatch BOTH modules to use the same fake client
# -------------------------
fake_client_instance = FakeClient(registered_numbers)
sus.get_telethon_client = lambda user_id: fake_client_instance
checkmod.get_telethon_client = lambda user_id: fake_client_instance

sus.session_exists = lambda user_id: True
checkmod.session_exists = lambda user_id: True

# Also patch get_check_count -> get_checks_done
sus.get_check_count = getattr(sus, "get_checks_done", lambda uid: 0)

# -------------------------
# Run simulation
# -------------------------
async def main():
    user_id = 9999
    test_numbers = [
        "254792813919", "254742635684", "254710527431", "254757384947",  # registered
        "254757213191", "254769407333", "254793472057", "254707287262",
        "254740644493", "254759229538",  # unregistered
        "123", "+notanumber", "254769400456"  # invalid/unregistered
    ]
    numbers_input = [n if n.startswith("+") else f"+{n}" for n in test_numbers]

    registered, unregistered = await checkmod.check_telegram_numbers(
        user_id, numbers_input, progress_callback=None
    )

    total_checked = len(registered) + len(unregistered)
    remaining_quota = checkmod.MAX_CHECKS_PER_SESSION - sus.get_check_count(user_id)

    # Styled report
    print(f"\n✨ Check Complete! Here is your report:\n")
    print(f"📦 Total Checked: {total_checked}")
    print(f"📉 Remaining Quota: {remaining_quota}/{checkmod.MAX_CHECKS_PER_SESSION}\n")

    print(f"✅ Registered Users ({len(registered)})")
    print("\n".join(registered) if registered else "None")
    print()
    print(f"❌ Not Registered ({len(unregistered)})")
    print("\n".join(unregistered) if unregistered else "None")
    print()


if __name__ == "__main__":
    asyncio.run(main())
