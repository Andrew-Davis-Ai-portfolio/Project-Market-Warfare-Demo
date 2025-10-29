#!/usr/bin/env python3
"""
Market Warfare Demo — Failure AI Simulation Engine
Project Checkmate • Flame Division

How to run:
    python market_warfare_demo.py            # interactive
    python market_warfare_demo.py --auto     # auto-play demo
    python market_warfare_demo.py --auto --seed 42 --rounds 12 --difficulty hard
"""

import argparse, random, textwrap, sys

# ---------- Config ----------
ACTIONS = {
    "1": {
        "name": "Raise Prices",
        "effects": {"cash": +9, "rep": -3, "eff": +1, "risk": +3, "score": +3},
        "copy": "You raise prices. Margin improves, but churn risk rises."
    },
    "2": {
        "name": "Expand to New Market",
        "effects": {"cash": -10, "rep": +3, "eff": -1, "risk": +6, "score": +5},
        "copy": "You expand geographically. Big upside, big exposure."
    },
    "3": {
        "name": "Launch Marketing Push",
        "effects": {"cash": -6, "rep": +6, "eff": 0, "risk": +2, "score": +4},
        "copy": "You push brand spend. Demand grows if runway holds."
    },
    "4": {
        "name": "Cut Costs Aggressively",
        "effects": {"cash": +7, "rep": -4, "eff": +5, "risk": +1, "score": +2},
        "copy": "You cut deeply. Runway extends, experience suffers."
    },
    "5": {
        "name": "Hold Position",
        "effects": {"cash": 0, "rep": 0, "eff": +1, "risk": 0, "score": +1},
        "copy": "You hold. Calm mind, small compounding edge."
    },
}

DIFFICULTY = {
    "easy":   {"pressure_mu": 3,  "risk_cap": 22},
    "normal": {"pressure_mu": 6,  "risk_cap": 18},
    "hard":   {"pressure_mu": 9,  "risk_cap": 15},
}

FAILURE_SENTENCES = {
    "cash": "You ran out of cash. Markets do not negotiate.",
    "risk": "Exposure exceeded tolerance. One shock toppled the system.",
    "rep":  "Customers rejected the value. Demand collapsed.",
    "eff":  "Operations buckled. The machine could not carry the load.",
}

# ---------- State ----------
class Game:
    def __init__(self, rounds=12, difficulty="normal", seed=None, auto=False, start_cash=35):
        if seed is not None:
            random.seed(seed)
        self.rounds = rounds
        self.auto = auto
        self.diff = DIFFICULTY[difficulty]
        self.r = 1
        self.state = dict(
            cash=start_cash,   # runway / liquidity
            rep=10,            # market trust
            eff=10,            # operational efficiency
            risk=5,            # cumulative exposure
            score=0,           # success metric
        )

    # market shock for a round
    def market_pressure(self):
        # stochastic pressure around difficulty mean
        base = self.diff["pressure_mu"]
        vol  = 3
        shock = max(0, int(random.gauss(base, vol)))
        return shock

    def apply_action(self, action_key, pressure):
        action = ACTIONS[action_key]
        eff = action["effects"].copy()

        # Market translates pressure into penalties (scaled by exposure)
        # Penalty severity grows when risk is already high.
        exposure = 1 + (self.state["risk"] / max(1, self.diff["risk_cap"]))
        cash_penalty = int(pressure * exposure * 0.8)  # pressure eats cash
        rep_penalty  = int(pressure * 0.3)
        eff_penalty  = int(pressure * 0.2)

        # Apply action effects
        self.state["cash"] += eff["cash"] - cash_penalty
        self.state["rep"]  += eff["rep"]  - rep_penalty
        self.state["eff"]  += eff["eff"]  - eff_penalty
        self.state["risk"] += eff["risk"]
        self.state["score"] += eff["score"] - int(pressure * 0.2)

        return action, {"cash": -cash_penalty, "rep": -rep_penalty, "eff": -eff_penalty}

    def failure_check(self):
        # Hard stops
        if self.state["cash"] <= 0: return "cash"
        if self.state["risk"] >= self.diff["risk_cap"]: return "risk"
        if self.state["rep"]  <= -5: return "rep"
        if self.state["eff"]  <= -5: return "eff"
        return None

    def failure_strike(self, cause):
        # Apply a strike & single-sentence feedback
        self.state["score"] -= 7
        self.state["cash"]  -= 3
        self.state["risk"]  = max(0, self.state["risk"] - 4)  # market forces you to deleverage
        return FAILURE_SENTENCES[cause]

    def coach_hint(self):
        s = self.state
        if s["cash"] < 8: return "Secure runway: choose 1 or 4."
        if s["risk"] > (self.diff["risk_cap"] * 0.7): return "De-risk immediately: 4 or 5."
        if s["rep"] < 5: return "Regain trust: choose 3 or 5."
        if s["eff"] < 5: return "Stabilize ops: 4 or 5."
        return "Balanced field: 1/3 for growth, 5 for patience."

    def auto_choice(self):
        # Greedy heuristic: pick action that maximizes (score gain - projected risk pain),
        # while preventing cash-out and risk-cap breach.
        candidates = []
        for k, a in ACTIONS.items():
            # simulate simple utility score
            util = a["effects"]["score"] + 0.2*a["effects"]["eff"] + 0.15*a["effects"]["rep"] \
                   + 0.1*a["effects"]["cash"] - 0.35*a["effects"]["risk"]
            # bias away from danger if near thresholds
            if self.state["cash"] < 10 and a["effects"]["cash"] < 0: util -= 3
            if self.state["risk"] > (self.diff["risk_cap"]*0.7) and a["effects"]["risk"] > 0: util -= 4
            candidates.append((util, k))
        candidates.sort(reverse=True)
        return candidates[0][1]

    def round_header(self, pressure):
        print(f"\n─ Round {self.r} · Market pressure: {pressure}")
        s = self.state
        print(f"  Cash:{s['cash']:>4} | Rep:{s['rep']:>3} | Eff:{s['eff']:>3} | Risk:{s['risk']:>3} / {self.diff['risk_cap']} | Score:{s['score']:>3}")

    def show_menu(self):
        print("\n  Choose your move:")
        for k, a in ACTIONS.items():
            print(f"   {k}. {a['name']}")
        print(f"  Hint: {self.coach_hint()}")

    def play(self):
        print(textwrap.dedent("""
            ╔════════════════════════════════════════════════════╗
            ║  Market Warfare Demo — Failure AI Simulation       ║
            ║  “Markets do not negotiate.”                       ║
            ╚════════════════════════════════════════════════════╝
        """).strip())

        while self.r <= self.rounds:
            pressure = self.market_pressure()
            self.round_header(pressure)

            # choose action
            if self.auto:
                choice = self.auto_choice()
                print(f"  Auto chose: {choice}. {ACTIONS[choice]['name']}")
            else:
                self.show_menu()
                while True:
                    choice = input("  Enter 1-5: ").strip()
                    if choice in ACTIONS: break
                    print("  Invalid. Enter 1-5.")

            action, mpen = self.apply_action(choice, pressure)
            print(f"  ▶ {action['copy']}")
            print(f"    Market penalties  cash:{mpen['cash']} rep:{mpen['rep']} eff:{mpen['eff']}")

            cause = self.failure_check()
            if cause:
                msg = self.failure_strike(cause)
                print(f"  ❌ FAILURE AI STRIKE: {msg}")
                print(f"    Forced deleverage. New risk: {self.state['risk']}")
                # If cash negative after strike, end immediately
                if self.state["cash"] <= 0:
                    print("\n  Game Over: Insolvent after strike.")
                    return self.finish(False)

            self.r += 1

        # survived
        success = self.state["score"] >= 0 and self.state["cash"] > 0
        return self.finish(success)

    def finish(self, success):
        s = self.state
        print("\n═ Final State ═")
        print(f"  Cash:{s['cash']} | Rep:{s['rep']} | Eff:{s['eff']} | Risk:{s['risk']} | Score:{s['score']}")
        if success:
            print("✅ Victory Protocol Achieved — Positive System Score with runway intact.")
        else:
            print("🛑 Simulation Failed — Negative score or runway lost.")
        return success


def main():
    p = argparse.ArgumentParser(description="Market Warfare Demo — Failure AI Simulation Engine")
    p.add_argument("--rounds", type=int, default=12, help="number of rounds (default: 12)")
    p.add_argument("--difficulty", choices=["easy","normal","hard"], default="normal")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--auto", action="store_true", help="auto-play with heuristic")
    p.add_argument("--starting-cash", type=int, default=35)
    args = p.parse_args()

    game = Game(rounds=args.rounds, difficulty=args.difficulty,
                seed=args.seed, auto=args.auto, start_cash=args.starting_cash)
    success = game.play()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
