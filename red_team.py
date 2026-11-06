from copy import deepcopy
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import sys
import unittest

from contract import RobotEconomyContract as VulnerableContract


def load_blue_contract():
    path = Path(__file__).resolve().with_name("robot_economy_contractBlueTeam")
    loader = SourceFileLoader("blue_team_contract", str(path))
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module.RobotEconomyContract


BlueContract = load_blue_contract()


def snapshot(contract):
    """Capture business state; rejected operations may still append events."""
    return deepcopy({
        "balances": contract.balances,
        "deliveries": contract.deliveries,
        "paused": contract.is_paused,
        "emergency_funds": getattr(contract, "emergency_funds", 0),
    })


def total_tokens(contract):
    # Original: treasury is the admin balance. Blue: separate treasury.
    return sum(contract.balances.values()) + getattr(contract, "emergency_funds", 0)


def describe(state):
    total = sum(state["balances"].values()) + state["emergency_funds"]
    return (
        f"balances={state['balances']}, paused={state['paused']}, "
        f"separate_treasury={state['emergency_funds']}, total={total}"
    )


class BeforeAfterTests(unittest.TestCase):
    def setUp(self):
        self.original = VulnerableContract()
        self.blue = BlueContract("admin")

    def compare_attack(self, attack, *, balances=None, paused=None,
                       expected_exception=None, repetitions=1):
        original_before = snapshot(self.original)
        blue_before = snapshot(self.blue)
        expected = deepcopy(original_before)
        if balances is not None:
            expected["balances"].update(balances)
        if paused is not None:
            expected["paused"] = paused

        for _ in range(repetitions):
            if expected_exception is None:
                result = attack(self.original)
                self.assertNotEqual(result, "error", "Original unexpectedly rejected attack")
            else:
                with self.assertRaises(expected_exception) as caught:
                    attack(self.original)
                self.assertEqual(caught.exception.args, ("robot_99",))

            events_before = len(self.blue.events)
            result = attack(self.blue)
            self.assertEqual(result, "error", "Blue must explicitly reject the attack")
            self.assertEqual(snapshot(self.blue), blue_before,
                             "Blue rejection must preserve balances, deliveries and pause state")
            self.assertEqual(len(self.blue.events), events_before + 1)
            self.assertEqual(self.blue.events[-1]["event"], "operation_rejected")

        self.assertEqual(snapshot(self.original), expected,
                         "Original exploit must produce the expected state change")
        print(f"\n  ORIGINAL before: {describe(original_before)}")
        print(f"  ORIGINAL after:  {describe(snapshot(self.original))}")
        if expected_exception is not None:
            print(f"  ORIGINAL raised {expected_exception.__name__} after changing state.")
        print(f"  BLUE before:     {describe(blue_before)}")
        print(f"  BLUE after:      {describe(snapshot(self.blue))}")
        print(f"  BLUE response: 'error' for all {repetitions} attempt(s).")

    def test_01_negative_amount(self):
        self.compare_attack(
            lambda c: c.pay_robot("bob", "robot_01", -400),
            balances={"bob": 900, "robot_01": -400},
        )
        self.assertEqual(total_tokens(self.original), 11500)

    def test_02_spend_more_than_balance(self):
        self.compare_attack(
            lambda c: c.pay_robot("alice", "robot_01", 9999),
            balances={"alice": -8999, "robot_01": 9999},
        )
        self.assertEqual(total_tokens(self.original), 11500)
        self.assertEqual(total_tokens(self.blue), 11500)
        print("  Unfunded payment: Alice is negative; original total remains 11500.")

    def test_03_repeated_fake_refund(self):
        self.compare_attack(
            lambda c: c.request_refund("alice", "fake_delivery", 500),
            balances={"alice": 3500},
            repetitions=5,
        )
        self.assertEqual(total_tokens(self.original), 14000)
        self.assertEqual(total_tokens(self.blue), 11500)
        print("  Original total increases from 11500 to 14000 without a payment.")

    def test_04_unauthorized_pause(self):
        self.compare_attack(lambda c: c.pause_contract("bob"), paused=True)

    def test_05_unauthorized_withdrawal(self):
        for contract in (self.original, self.blue):
            contract.pause_contract("admin")
            self.assertTrue(contract.is_paused)
        self.compare_attack(
            lambda c: c.withdraw_emergency_funds("bob", 5000),
            balances={"bob": 5500, "admin": 5000},
        )
        self.assertEqual(total_tokens(self.original), 11500)
        self.assertEqual(total_tokens(self.blue), 11500)

    def test_06_nonexistent_robot(self):
        self.compare_attack(
            lambda c: c.pay_robot("alice", "robot_99", 100),
            balances={"alice": 900},
            expected_exception=KeyError,
        )
        self.assertEqual(total_tokens(self.original), 11400)
        self.assertEqual(total_tokens(self.blue), 11500)

    def test_07_payment_while_paused(self):
        for contract in (self.original, self.blue):
            contract.pause_contract("admin")
            self.assertTrue(contract.is_paused)
        self.compare_attack(
            lambda c: c.pay_robot("alice", "robot_01", 100),
            balances={"alice": 900, "robot_01": 100},
        )
        print("  Original payment succeeds despite paused=True; Blue rejects it.")

    def test_08_valid_payment(self):
        for contract in (self.original, self.blue):
            with self.subTest(contract=type(contract).__module__):
                result = contract.pay_robot("alice", "robot_01", 100)
                self.assertNotEqual(result, "error")
                self.assertEqual(contract.balances["alice"], 900)
                self.assertEqual(contract.balances["robot_01"], 100)
                self.assertEqual(total_tokens(contract), 11500)
        self.assertEqual(self.blue.deliveries[0]["status"], "pending")


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout, verbosity=2))
