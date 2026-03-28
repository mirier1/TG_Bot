from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

STAT_ORDER = ("moral", "knowledge", "finance", "health", "connections")


class GameEngine:
    def __init__(self, path: str | Path = "data/scenario.json") -> None:
        with open(path, encoding="utf-8") as f:
            self._data: dict = json.load(f)

        self.score_labels: dict[str, str] = self._data["score_labels"]
        self.initial_scores: dict[str, int] = dict(self._data["initial_scores"])
        self.checkpoints: list[int] = self._data["checkpoint_after_questions"]
        self.questions: dict[str, dict] = self._data["questions"]
        self.flow: list[str] = self._data["question_flow"]
        self.finale_cfg: dict = self._data["finale_calculation"]
        self.epilogue_text: str = self._data["epilogue_text"]
        self.endings: list[dict] = self._data["endings"]
        self.endings_order: list[str] = self._data["endings_check_order"]

    # ── свойства ─────────────────────────────────────────────

    @property
    def title(self) -> str:
        return self._data["meta"]["title"]

    @property
    def intro_text(self) -> str:
        i = self._data["intro"]
        return f"{i['story_text']}\n\n{i['score_system_text']}"

    # ── утилиты ──────────────────────────────────────────────

    @staticmethod
    def _apply(scores: dict[str, int], effects: dict[str, int]) -> dict[str, int]:
        out = dict(scores)
        for s, v in effects.items():
            if s in out:
                out[s] += v
        return out

    @staticmethod
    def _roll(chance: int) -> bool:
        return random.randint(1, 100) <= chance

    @staticmethod
    def _cmp(value: int, op: str, target: int) -> bool:
        ops = {
            ">=": value >= target,
            "<=": value <= target,
            ">": value > target,
            "<": value < target,
            "==": value == target,
        }
        return ops.get(op, False)

    def _fmt_effects(
        self,
        effects: dict[str, int],
        override: list[str] | None = None,
    ) -> str:
        if override:
            return "\n".join(override)
        lines: list[str] = []
        for s in STAT_ORDER:
            v = effects.get(s, 0)
            if v == 0:
                continue
            sign = "+" if v > 0 else ""
            lines.append(f"{self.score_labels[s]} {sign}{v}")
        return "\n".join(lines)

    def format_scores(self, sc: dict[str, int]) -> str:
        return (
            f"🧭 Мораль: {sc['moral']}\n"
            f"📚 Знания: {sc['knowledge']}\n"
            f"💰 Финансы: {sc['finance']}\n"
            f"❤️ Здоровье: {sc['health']}\n"
            f"🤝 Связи: {sc['connections']}"
        )

    # ── отображение вопроса ──────────────────────────────────

    def question_display(self, q: dict) -> str:
        parts = [q["text"], "\nВарианты:"]
        for o in q["options"]:
            parts.append(f"{o['label']}) {o['text']}")
        return "\n\n".join(parts)

    # ── pre_condition (Q28) ──────────────────────────────────

    def check_pre_condition(
        self, qid: str, choices: dict[str, str]
    ) -> dict | None:
        q = self.questions.get(qid)
        if not q:
            return None
        pc = q.get("pre_condition")
        if not pc:
            return None
        if pc["type"] == "choice_check":
            if choices.get(pc["question_id"]) == pc["choice_label"]:
                return {
                    "skip": True,
                    "text": pc["true_text"],
                    "effects": pc.get("true_effects", {}),
                }
        return None

    # ── requirement (Q39) ────────────────────────────────────

    @staticmethod
    def check_requirement(option: dict, scores: dict[str, int]) -> bool:
        req = option.get("requirement")
        if not req:
            return True
        return scores[req["stat"]] >= req["min_value"]

    def requirement_text(self, option: dict) -> str:
        req = option.get("requirement")
        if not req:
            return ""
        return (
            f"Недостаточно! Требуется "
            f"{self.score_labels[req['stat']]} ≥ {req['min_value']}"
        )

    # ── обработка выбора ─────────────────────────────────────

    def process_choice(
        self,
        qid: str,
        label: str,
        scores: dict[str, int],
        choices: dict[str, str],
        bonuses: int,
    ) -> dict[str, Any]:
        q = self.questions[qid]
        opt = next((o for o in q["options"] if o["label"] == label), None)
        if not opt:
            return {
                "scores": scores,
                "result_text": "⚠️ Вариант не найден.",
                "finale_bonuses": bonuses,
            }

        parts: list[str] = []
        sc = dict(scores)
        fb = bonuses

        effects = opt.get("effects", {})
        edisp = opt.get("effects_display")

        # stat_check BEFORE
        stc = opt.get("stat_check")
        stc_result: bool | None = None
        if stc and stc.get("timing") == "before_effects":
            stc_result = self._cmp(sc[stc["stat"]], stc["operator"], stc["value"])

        # эффекты
        etxt = self._fmt_effects(effects, edisp)
        if etxt:
            parts.append(etxt)
        sc = self._apply(sc, effects)

        # stat_check AFTER
        if stc and stc.get("timing") == "after_effects":
            stc_result = self._cmp(sc[stc["stat"]], stc["operator"], stc["value"])

        # результат stat_check
        if stc and stc_result is not None:
            if stc_result:
                sc = self._apply(sc, stc.get("true_effects", {}))
                parts.append(stc["true_text"])
            else:
                sc = self._apply(sc, stc.get("false_effects", {}))
                parts.append(f"Итог: {stc['false_text']}")

        # choice_check
        cc = opt.get("choice_check")
        if cc:
            if choices.get(cc["question_id"]) == cc["choice_label"]:
                sc = self._apply(sc, cc.get("true_effects", {}))
                parts.append(cc["true_text"])
            else:
                sc = self._apply(sc, cc.get("false_effects", {}))
                parts.append(f"Итог: {cc['false_text']}")

        # dice
        dice = opt.get("dice")
        if dice:
            hit = self._roll(dice["chance"])
            if hit:
                sc = self._apply(sc, dice.get("success_effects", {}))
                parts.append(dice.get("success_text", ""))
                if "success_finale_bonus" in dice:
                    fb += dice["success_finale_bonus"]
            else:
                sc = self._apply(sc, dice.get("fail_effects", {}))
                parts.append(dice.get("fail_text", ""))
                if "fail_finale_bonus" in dice:
                    fb += dice["fail_finale_bonus"]

        # обычный outcome
        if not stc and not dice and not cc:
            ot = opt.get("outcome_text", "")
            if ot:
                parts.append(f"Итог: {ot}")

        # скрытый бонус к финалу
        if "finale_bonus" in opt:
            fb += opt["finale_bonus"]

        return {
            "scores": sc,
            "result_text": "\n\n".join(p for p in parts if p),
            "finale_bonuses": fb,
        }

    # ── навигация ────────────────────────────────────────────

    def _resolved_flow(self, branch: str | None) -> list[str]:
        out: list[str] = []
        for item in self.flow:
            if item == "_BRANCH_46_":
                out.append(f"46{branch}" if branch else item)
            elif item == "_BRANCH_47_":
                out.append(f"47{branch}" if branch else item)
            else:
                out.append(item)
        return out

    def next_qid(self, current: str, branch: str | None) -> str | None:
        flow = self._resolved_flow(branch)
        try:
            idx = flow.index(current)
            return flow[idx + 1] if idx + 1 < len(flow) else None
        except ValueError:
            return None

    def is_checkpoint(self, qid: str) -> bool:
        try:
            return int(qid) in self.checkpoints
        except ValueError:
            return False

    # ── финал ────────────────────────────────────────────────

    def calculate_finale(self, scores: dict[str, int], fb: int) -> str:
        stat_bonus = self._stat_bonus(scores)
        total = self.finale_cfg["base_chance"] + stat_bonus + fb
        total = max(1, min(total, 95))

        if self._roll(total):
            return "A"

        second = self.finale_cfg["second_roll"]["base_chance"] + stat_bonus + fb
        second = max(1, min(second, 95))
        return "B" if self._roll(second) else "C"

    def _stat_bonus(self, scores: dict[str, int]) -> int:
        bonus = 0
        seen: set[str] = set()
        for sb in self.finale_cfg["stat_bonuses"]:
            st = sb["stat"]
            if st in seen:
                continue
            if self._cmp(scores[st], sb["operator"], sb["value"]):
                bonus += sb["bonus"]
                seen.add(st)
        return bonus

    # ── определение концовки ─────────────────────────────────

    def determine_ending(self, scores: dict[str, int]) -> dict:
        for eid in self.endings_order:
            e = next((x for x in self.endings if x["id"] == eid), None)
            if not e:
                continue
            if eid == "default":
                return e
            if eid == "holy_martyr":
                if scores["moral"] >= 15 and (
                    scores["finance"] <= 3 or scores["health"] <= 4
                ):
                    return e
                continue
            conds = e.get("conditions", {})
            if all(
                self._cmp(scores[s], c["operator"], c["value"])
                for s, c in conds.items()
            ):
                return e
        return self.endings[-1]