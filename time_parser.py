"""Strict timestamps and SMPTE timecodes; range ends are exclusive."""
import math
import re


def parse_time(text, framerate=30.0):
    if not text or not math.isfinite(framerate) or framerate <= 0:
        return None
    text = text.strip().lower()
    timebase = round(framerate)
    tc = re.fullmatch(r'(\d+):(\d{2}):(\d{2})([:;])(\d{2})', text)
    if tc:
        h, m, s, sep, f = tc.groups()
        h, m, s, f = map(int, (h, m, s, f))
        if m >= 60 or s >= 60 or f >= timebase: return None
        frames = (h * 3600 + m * 60 + s) * timebase + f
        if sep == ';':
            if not (abs(framerate - 30000/1001) < .01 or abs(framerate - 60000/1001) < .01): return None
            dropped = 2 if timebase == 30 else 4
            if m % 10 and s == 0 and f < dropped: return None
            total_minutes = h * 60 + m
            frames -= dropped * (total_minutes - total_minutes // 10)
        return frames / framerate
    if ':' in text:
        parts = text.split(':')
        if len(parts) not in (2, 3) or not all(re.fullmatch(r'\d+(?:\.\d+)?' if i == len(parts)-1 else r'\d+', p) for i, p in enumerate(parts)):
            return None
        values = list(map(float, parts))
        if values[-1] >= 60 or (len(parts) == 3 and values[1] >= 60): return None
        return sum(v * 60**i for i, v in enumerate(reversed(values)))
    if re.fullmatch(r'\d+(?:\.\d+)?s?', text): return float(text.rstrip('s'))
    match = re.fullmatch(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s?)?', text)
    if match and any(match.groups()):
        h, m, s = (float(v or 0) for v in match.groups())
        return h*3600 + m*60 + s
    return None


def parse_time_range(text, framerate=30.0):
    parts = re.split(r'[-–—]', text.strip())
    if len(parts) != 2: return None
    start, end = (parse_time(part, framerate) for part in parts)
    return (start, end) if start is not None and end is not None and end > start else None


def parse_timecodes(text, framerate=30.0):
    ranges, errors = [], []
    for index, line in enumerate(text.splitlines(), 1):
        if not line.strip(): continue
        value = parse_time_range(line, framerate)
        if value: ranges.append(value)
        else: errors.append(f"Line {index}: '{line}' - invalid format")
    return sorted(ranges), errors


def format_seconds(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f'{h:02d}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'


def frames_to_timecode(frames, fps, drop_frame=False):
    frames, nominal = max(0, round(frames)), round(fps)
    if drop_frame:
        if nominal not in (30, 60): raise ValueError('Drop-frame requires 29.97 or 59.94 fps')
        drop = 2 if nominal == 30 else 4
        per_minute, per_ten = nominal * 60 - drop, nominal * 600 - drop * 9
        tens, rem = divmod(frames, per_ten)
        frames += drop * 9 * tens + drop * max(0, (rem - drop) // per_minute)
    seconds, f = divmod(frames, nominal)
    minutes, s = divmod(seconds, 60)
    h, m = divmod(minutes, 60)
    sep = ';' if drop_frame else ':'
    return f'{h:02d}:{m:02d}:{s:02d}{sep}{f:02d}'
