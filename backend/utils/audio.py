from __future__ import annotations

import gzip
import hashlib
from typing import Any, Dict, Optional, Tuple


def _find_mp3_sync_offset(data: bytes, max_scan: int = 4096) -> Optional[int]:
    if not data or len(data) < 2:
        return None

    scan_len = min(len(data), max_scan)
    for i in range(scan_len - 1):
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            return i
    return None


def _parse_id3v2_tag_end(data: bytes) -> Optional[int]:
    if len(data) < 10 or not data.startswith(b"ID3"):
        return None

    size_bytes = data[6:10]
    if any(b & 0x80 for b in size_bytes):
        return None

    size = (size_bytes[0] << 21) | (size_bytes[1] << 14) | (size_bytes[2] << 7) | size_bytes[3]
    return 10 + size


def validate_and_normalize_mp3(audio_data: bytes) -> Tuple[bool, str, bytes, Dict[str, Any]]:
    debug: Dict[str, Any] = {
        "original_len": 0 if not audio_data else len(audio_data),
        "decompressed": False,
        "id3_present": False,
        "id3_declared_end": None,
        "first_sync_offset": None,
        "trimmed_offset": None,
        "normalized_len": 0,
        "first16_hex": "" if not audio_data else audio_data[:16].hex(),
        "sha256": "",
    }

    if not audio_data:
        return False, "音频数据为空", b"", debug

    if len(audio_data) >= 2 and audio_data[0] == 0x1F and audio_data[1] == 0x8B:
        try:
            audio_data = gzip.decompress(audio_data)
            debug["decompressed"] = True
            debug["first16_hex"] = audio_data[:16].hex()
        except Exception:
            pass

    if audio_data.startswith(b"ID3"):
        debug["id3_present"] = True
        id3_end = _parse_id3v2_tag_end(audio_data)
        debug["id3_declared_end"] = id3_end
        if id3_end is not None and id3_end + 1 < len(audio_data):
            if audio_data[id3_end] == 0xFF and (audio_data[id3_end + 1] & 0xE0) == 0xE0:
                debug["first_sync_offset"] = id3_end
                debug["normalized_len"] = len(audio_data)
                debug["sha256"] = hashlib.sha256(audio_data).hexdigest()
                return True, "有效的MP3文件(ID3标签)", audio_data, debug

    sync_offset = _find_mp3_sync_offset(audio_data)
    debug["first_sync_offset"] = sync_offset

    if sync_offset is None:
        debug["normalized_len"] = len(audio_data)
        debug["sha256"] = hashlib.sha256(audio_data).hexdigest()
        return False, "未检测到MP3同步帧", audio_data, debug

    if sync_offset > 0:
        audio_data = audio_data[sync_offset:]
        debug["trimmed_offset"] = sync_offset
        debug["first16_hex"] = audio_data[:16].hex()

    debug["normalized_len"] = len(audio_data)
    debug["sha256"] = hashlib.sha256(audio_data).hexdigest()
    return True, "有效的MP3文件(包含同步帧)", audio_data, debug


def validate_audio_data(audio_data: bytes) -> Tuple[bool, str]:
    is_valid, msg, _, _ = validate_and_normalize_mp3(audio_data)
    return is_valid, msg
