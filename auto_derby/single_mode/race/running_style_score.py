# pyright: strict
# -*- coding=UTF-8 -*-
from __future__ import annotations

from typing import Text, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import Context
    from .race import Race

from ... import mathtools, app


def compute(
    ctx: Context,
    race: Race,
    status: Tuple[int, Text],
    block_factor: float,
    hp_factor: float,
    wisdom_factor: float,
) -> float:
    """Score standard:

    No1 P90: 10000
    No2 P90: 9000
    No3 P90: 7000
    No5 P90: 6500
    50% P90: 5000
    """
    spd = ctx.speed
    sta = ctx.stamina
    pow_ = ctx.power
    gut = ctx.guts
    wis = ctx.wisdom

    spd *= ctx.mood.race_rate
    sta *= ctx.mood.race_rate
    pow_ *= ctx.mood.race_rate
    gut *= ctx.mood.race_rate
    wis *= ctx.mood.race_rate

    base_speed_coefficient = 1
    course = None if len(race.courses) != 1 else race.courses[0]
    if course:
        for i in course.target_statuses:
            base_speed_coefficient *= 1 + 0.1 * min(
                2,
                int(
                    {
                        course.TARGET_STATUS_SPEED: ctx.speed,
                        course.TARGET_STATUS_POWER: ctx.power,
                        course.TARGET_STATUS_STAMINA: ctx.stamina,
                        course.TARGET_STATUS_GUTS: ctx.guts,
                        course.TARGET_STATUS_WISDOM: ctx.wisdom,
                    }[i]
                    / 300
                ),
            )
        spd *= base_speed_coefficient

    # TODO: race field affect

    # https://bbs.nga.cn/read.php?tid=26010713
    single_mode_bonus = 400
    spd += single_mode_bonus
    sta += single_mode_bonus
    pow_ += single_mode_bonus
    gut += single_mode_bonus
    wis += single_mode_bonus

    # proper ground
    # from master.mdb `race_proper_ground_rate` table
    ground = race.courses[0].ground_status(ctx)
    ground_rate = {
        "S": 1.05,
        "A": 1.0,
        "B": 0.9,
        "C": 0.8,
        "D": 0.7,
        "E": 0.5,
        "F": 0.3,
        "G": 0.1,
    }[ground[1]]

    # proper distance
    # from master.mdb `race_proper_distance_rate` table
    distance = race.courses[0].distance_status(ctx)
    d_spd_rate, d_pow_rate = {
        "S": (1.05, 1.0),
        "A": (1.0, 1.0),
        "B": (0.9, 1.0),
        "C": (0.8, 1.0),
        "D": (0.6, 1.0),
        "E": (0.4, 0.6),
        "F": (0.2, 0.5),
        "G": (0.1, 0.4),
    }[distance[1]]

    # spell-checker: word runningstyle
    # proper running style
    # from master.mdb `race_proper_runningstyle_rate` table

    style_rate = {
        "S": 1.1,
        "A": 1.0,
        "B": 0.85,
        "C": 0.75,
        "D": 0.6,
        "E": 0.4,
        "F": 0.2,
        "G": 0.1,
    }[status[1]]

    # https://umamusume.cygames.jp/#/help?p=3

    # 距離適性が低い距離のコースを走るとうまくスピードに乗れず、上位争いをすることが難しいことが多い。
    spd *= d_spd_rate
    pow_ *= d_pow_rate

    # 適性が低い作戦で走ろうとすると冷静に走れないことが多い。
    wis *= style_rate

    # バ場適性が合わないバ場を走ると力強さに欠けうまく走れないことが多い。
    pow_ *= ground_rate

    sta *= hp_factor
    wis *= wisdom_factor

    gut_as_sta = mathtools.interpolate(
        int(gut),
        (
            (0, 0),
            (1200, 100),
            (1600, 150),
        ),
    )
    sta += gut_as_sta
    wis_as_spd = mathtools.interpolate(
        int(gut),
        (
            (0, 0),
            (900, 200),
            (1600, 350),
        ),
    )
    spd += wis_as_spd
    wis_as_sta = mathtools.interpolate(
        int(gut),
        (
            (0, 0),
            (900, 100),
            (1600, 200),
        ),
    )
    sta += wis_as_sta

    hp = race.courses[0].distance + hp_factor * 0.8 * sta
    expected_spd = (
        mathtools.interpolate(
            ctx.turn_count(),
            (
                (0, 700),
                (24, 700),
                (48, 900),
                (72, 1100),
            ),
        )
        * {
            race.GRADE_G1: 1,
            race.GRADE_G2: 0.9,
            race.GRADE_G3: 0.8,
            race.GRADE_PRE_OP: 0.7,
            race.GRADE_OP: 0.7,
            race.GRADE_NOT_WINNING: 0.6,
            race.GRADE_DEBUT: 0.6,
        }[race.grade]
        * mathtools.interpolate(
            race.courses[0].distance,
            (
                (0, 1.1),
                (1200, 1.05),
                (1600, 1.0),
                (3200, 0.9),
            ),
        )
    )
    expected_hp = (
        race.courses[0].distance
        * mathtools.interpolate(
            ctx.turn_count(),
            (
                (0, 1.0),
                (24, 1.4),
                (48, 1.6),
                (72, 1.8),
                (75, 2.0),
            ),
        )
        * {
            race.GRADE_G1: 1,
            race.GRADE_G2: 0.9,
            race.GRADE_G3: 0.85,
            race.GRADE_PRE_OP: 0.8,
            race.GRADE_OP: 0.8,
            race.GRADE_NOT_WINNING: 0.7,
            race.GRADE_DEBUT: 0.7,
        }[race.grade]
    )
    expected_pow = (
        mathtools.interpolate(
            ctx.turn_count(),
            (
                (0, 550),
                (24, 700),
                (48, 850),
                (72, 1000),
            ),
        )
        * mathtools.interpolate(
            race.courses[0].distance,
            (
                (0, 0.8),
                (1600, 1),
                (3200, 1.2),
                (4800, 1.4),
            ),
        )
        * {
            race.GRADE_G1: 1,
            race.GRADE_G2: 0.95,
            race.GRADE_G3: 0.9,
            race.GRADE_PRE_OP: 0.8,
            race.GRADE_OP: 0.8,
            race.GRADE_NOT_WINNING: 0.6,
            race.GRADE_DEBUT: 0.6,
        }[race.grade]
    )

    expected_wis = mathtools.interpolate(
        ctx.turn_count(),
        (
            (0, 500),
            (24, 650),
            (48, 700),
            (72, 750),
        ),
    )

    block_rate = (
        mathtools.interpolate(
            int(pow_ / expected_pow * 10000),
            (
                (0, 10.0),
                (6000, 1.0),
                (7000, 0.6),
                (8000, 0.4),
                (10000, 0.1),
                (12000, 0.01),
            ),
        )
        * mathtools.interpolate(
            int(spd / expected_spd * 10000),
            (
                (6000, 10.0),
                (8000, 2.0),
                (10000, 1.0),
                (12000, 0.8),
            ),
        )
        * mathtools.interpolate(
            race.courses[0].distance,
            (
                (0, 2.0),
                (1200, 2.0),
                (2000, 1.0),
                (3200, 0.6),
            ),
        )
        * block_factor
    )
    block_rate = min(1.0, block_rate)
    block_penalty = mathtools.interpolate(
        int(block_rate * 10000),
        (
            (0, 0),
            (1000, 0.2),
            (2000, 0.5),
            (3000, 0.7),
        ),
    )

    hp_penalty = mathtools.interpolate(
        int(hp / expected_hp * 10000),
        (
            (0, 1.0),
            (5000, 0.6),
            (8000, 0.4),
            (9000, 0.2),
            (10000, 0),
        ),
    )
    hp_penalty = min(1, hp_penalty)

    wis_penalty = mathtools.interpolate(
        int(wis / expected_wis * 10000),
        (
            (0, 0.3),
            (7000, 0.2),
            (9000, 0.1),
            (10000, 0.0),
        ),
    )

    ret = spd / expected_spd * 10000
    ret *= 1 - block_penalty
    ret *= 1 - hp_penalty
    ret *= 1 - wis_penalty

    app.log.text(
        (
            "style: "
            "score=%d "
            "block_rate=%.2f "
            "block_penalty=%.2f "
            "hp_penalty=%0.2f "
            "wis_penalty=%0.2f "
            "spd=%0.2f/%0.2f "
            "sta=%0.2f "
            "hp=%0.2f/%0.2f "
            "pow=%0.2f/%0.2f "
            "gut=%0.2f "
            "wis=%0.2f"
        )
        % (
            ret,
            block_rate,
            block_penalty,
            hp_penalty,
            wis_penalty,
            spd,
            expected_spd,
            sta,
            hp,
            expected_hp,
            pow_,
            expected_pow,
            gut,
            wis,
        ),
        level=app.DEBUG,
    )
    return ret
