from typing import Optional, Union
import attr
import decimal
import math
import re


def to_zero(dec: decimal.Decimal) -> decimal.Decimal:
    return dec.quantize(decimal.Decimal("1"), rounding=decimal.ROUND_DOWN)


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class Ms:
    days: decimal.Decimal
    hours: decimal.Decimal
    minutes: decimal.Decimal
    seconds: decimal.Decimal
    milliseconds: decimal.Decimal
    microseconds: decimal.Decimal
    nanoseconds: decimal.Decimal


def parse_ms(ms: decimal.Decimal) -> Ms:
    return Ms(
        days=to_zero(ms / 86_400_000),
        hours=to_zero((ms / 3_600_000) % 24),
        minutes=to_zero((ms / 60_000) % 60),
        seconds=to_zero((ms / 1_000) % 60),
        milliseconds=to_zero((ms) % 1_000),
        microseconds=to_zero((ms * 1_000) % 1_000),
        nanoseconds=to_zero((ms * 1_000_000) % 1_000),
    )


def pretty_ms(
    ms: Union[str, float, int, decimal.Decimal], *,
    unit_count: Optional[int] = None,
    compact: bool = False,
    verbose: bool = False,
    sec_digits: int = 1,
    separate_ms: bool = False,
    format_sub_ms: bool = False,
    keep_decimals_on_whole_seconds: bool = True,
) -> str:
    ms = decimal.Decimal(ms)

    if compact:
        sec_digits = 0

    ret = []

    def add(value: Union[int, decimal.Decimal], long: str, short: str, valueString: Optional[str] = None) -> None:
        if value == 0:
            return

        postfix = " " + (long if value == 1 else f"{long}s") if verbose else short

        ret.append(str(valueString or value) + postfix)

    if sec_digits < 1:
        diff = 1000 - (ms % 1000)
        if diff < 500:
            ms += diff

    parsed = parse_ms(ms)

    add(math.trunc(parsed.days / 365), "year", "y")
    add(parsed.days % 365, "day", "d")
    add(parsed.hours, "hour", "h")
    add(parsed.minutes, "minute", "m")

    if separate_ms or format_sub_ms or ms < 1000:
        add(parsed.seconds, "second", "s")

        if format_sub_ms:
            add(parsed.milliseconds, "millisecond", "ms")
            add(parsed.microseconds, "microsecond", "us")
            add(parsed.nanoseconds, "nanosecond", "ns")
        else:
            ms_and_below = parsed.milliseconds + (parsed.microseconds / 1000) + (parsed.nanoseconds / 1_000_000)
            ms_str = str(math.ceil(ms_and_below))
            add(decimal.Decimal(ms_str), "millisecond", "ms", ms_str)
    else:
        sec = ms / 1000 % 60
        sec_fixed = format(sec, f".{sec_digits}f")
        sec_str = re.sub(r"\.0+$", "", sec_fixed)
        add(decimal.Decimal(sec_str), "second", "s", sec_str)

    if not ret:
        return "0" + " milliseconds" if verbose else "ms"

    if compact:
        return "~" + ret[0]

    if unit_count is not None:
        return "~" + " ".join(ret[:unit_count])

    return " ".join(ret)
