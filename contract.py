class RobotEconomyContract:
    def __init__(self):
        self.admin = "admin"
        self.balances = {
            "alice": 1000,
            "bob": 500,
            "robot_01": 0,
            "robot_02": 0,
            "admin": 10000
        }
        self.is_paused = False
        self.deliveries = {}  # tracks: delivery_id -> {caller, amount, refunded}

    def pay_robot(self, caller, robot, amount):
        # BUG: no pause check
        # BUG: no positive amount check
        # BUG: no balance check
        # BUG: no robot existence check
        self.balances[caller] -= amount
        self.balances[robot] += amount
        return f"Paid {amount} tokens to {robot}"

    def request_refund(self, caller, delivery_id, amount):
        # BUG: no delivery verification
        # BUG: no limit on refund amount
        # BUG: can be called infinite times
        self.balances[caller] += amount
        return "Refund processed"

    def pause_contract(self, caller):
        # BUG: no admin check — anyone can pause!
        self.is_paused = True
        return "Contract paused"

    def withdraw_emergency_funds(self, caller, amount):
        # BUG: no admin check — anyone can drain treasury!
        self.balances[caller] += amount
        self.balances["admin"] -= amount
        return "Funds withdrawn"
