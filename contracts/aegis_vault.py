# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class AegisVault(gl.Contract):
    admin: Address
    guardian: Address
    frozen: bool
    freeze_reason: str
    total_locked: u256

    def __init__(self) -> None:
        self.admin = gl.message.sender_address
        self.guardian = gl.message.sender_address
        self.frozen = False
        self.freeze_reason = ""
        self.total_locked = u256(0)

    @gl.public.write
    def deposit(self, amount: u256) -> str:
        assert int(amount) > 0, "AMOUNT_REQUIRED"
        self.total_locked = u256(int(self.total_locked) + int(amount))
        return "DEPOSITED"

    @gl.public.write
    def withdraw(self, amount: u256) -> str:
        assert not self.frozen, "VAULT_FROZEN_BY_THREATLOCK"
        assert int(self.total_locked) >= int(amount), "INSUFFICIENT_TVL"
        self.total_locked = u256(int(self.total_locked) - int(amount))
        return "WITHDRAWN"

    @gl.public.write
    def freeze(self, reason: str) -> str:
        assert gl.message.sender_address == self.admin or gl.message.sender_address == self.guardian, "ONLY_ADMIN_OR_GUARDIAN"
        self.frozen = True
        self.freeze_reason = reason
        return "FROZEN"

    @gl.public.write
    def unfreeze(self, note: str) -> str:
        assert gl.message.sender_address == self.admin or gl.message.sender_address == self.guardian, "ONLY_ADMIN_OR_GUARDIAN"
        self.frozen = False
        self.freeze_reason = note
        return "UNFROZEN"

    @gl.public.write
    def set_guardian(self, new_guardian: Address) -> str:
        assert gl.message.sender_address == self.admin, "ONLY_ADMIN"
        self.guardian = new_guardian
        return "GUARDIAN_UPDATED"

    @gl.public.view
    def is_frozen(self) -> bool:
        return self.frozen

    @gl.public.view
    def total_value_locked(self) -> u256:
        return self.total_locked

    @gl.public.view
    def get_freeze_reason(self) -> str:
        return self.freeze_reason

    @gl.public.view
    def get_admin(self) -> Address:
        return self.admin

    @gl.public.view
    def get_guardian(self) -> Address:
        return self.guardian
