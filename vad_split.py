"""对 assets/菲比啾比.mp3 进行 VAD 并分成三个片段"""
import os
import sys
import struct
import math
import subprocess
import wave

FFMPEG = r"D:\Program Files\ffmpeg\bin\ffmpeg.exe"
INPUT = os.path.join("assets", "菲比啾比.mp3")
OUTPUT_DIR = "assets"
SAMPLE_RATE = 16000


def get_duration(path):
    """用 ffmpeg 获取音频时长"""
    result = subprocess.run(
        [FFMPEG, "-i", path, "-hide_banner"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    for line in result.stderr.split("\n"):
        if "Duration:" in line:
            time_str = line.split("Duration:")[1].split(",")[0].strip()
            parts = time_str.split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 0


def to_wav(mp3_path, wav_path):
    """用 ffmpeg 将 mp3 转为 mono 16-bit wav"""
    subprocess.run([
        FFMPEG, "-y", "-i", mp3_path,
        "-ar", str(SAMPLE_RATE), "-ac", "1", "-sample_fmt", "s16",
        wav_path
    ], capture_output=True, check=True)


def read_wav_samples(wav_path):
    """读取 wav 文件的 PCM 采样数据"""
    with wave.open(wav_path, "rb") as wf:
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    samples = struct.unpack(f"<{n_frames}h", raw)
    return samples


def compute_energy(samples, frame_size, hop_size):
    """计算短时能量（dB）"""
    energies = []
    for i in range(0, len(samples) - frame_size, hop_size):
        frame = samples[i:i + frame_size]
        rms = math.sqrt(sum(s * s for s in frame) / frame_size)
        db = 20 * math.log10(rms / 32768 + 1e-10)
        energies.append(db)
    return energies


def vad_split(energies, hop_size, sr, thresh_db=-40, min_silence_ms=300, min_speech_ms=200):
    """基于能量的 VAD，返回语音段列表 [(start_ms, end_ms), ...]"""
    frame_ms = hop_size / sr * 1000
    min_silence_frames = int(min_silence_ms / frame_ms)
    min_speech_frames = int(min_speech_ms / frame_ms)

    is_speech = [e > thresh_db for e in energies]
    segments = []
    in_speech = False
    start = 0
    silence_count = 0

    for i, s in enumerate(is_speech):
        if s:
            if not in_speech:
                start = i
                in_speech = True
            silence_count = 0
        else:
            silence_count += 1
            if in_speech and silence_count >= min_silence_frames:
                if (i - silence_count - start) >= min_speech_frames:
                    segments.append((start, i - silence_count))
                in_speech = False

    if in_speech and (len(is_speech) - start) >= min_speech_frames:
        segments.append((start, len(is_speech)))

    result = []
    for s, e in segments:
        result.append((int(s * frame_ms), int(e * frame_ms)))
    return result


def export_segment(input_path, output_path, start_ms, end_ms):
    """用 ffmpeg 截取音频片段"""
    duration_ms = end_ms - start_ms
    subprocess.run([
        FFMPEG, "-y", "-i", input_path,
        "-ss", f"{start_ms/1000:.3f}", "-t", f"{duration_ms/1000:.3f}",
        "-acodec", "libmp3lame", "-q:a", "2",
        output_path
    ], capture_output=True, check=True)


if __name__ == "__main__":
    if not os.path.exists(FFMPEG):
        print(f"错误：ffmpeg 不存在 -> {FFMPEG}")
        sys.exit(1)
    if not os.path.exists(INPUT):
        print(f"错误：文件不存在 -> {INPUT}")
        sys.exit(1)

    total_duration = get_duration(INPUT)
    print(f"文件: {INPUT}")
    print(f"总时长: {total_duration:.2f} 秒")

    # 转为 wav 用于分析
    wav_tmp = os.path.join(OUTPUT_DIR, "_tmp_vad.wav")
    print("正在转换为 WAV...")
    to_wav(INPUT, wav_tmp)

    # 读取采样并计算能量
    print("正在分析语音段...")
    samples = read_wav_samples(wav_tmp)
    os.remove(wav_tmp)

    frame_size = int(SAMPLE_RATE * 0.025)  # 25ms
    hop_size = int(SAMPLE_RATE * 0.010)    # 10ms
    energies = compute_energy(samples, frame_size, hop_size)

    # VAD 检测
    THRESH = -40
    segments = vad_split(energies, hop_size, SAMPLE_RATE, thresh_db=THRESH)
    print(f"检测到 {len(segments)} 个语音段 (阈值: {THRESH} dB)")

    if not segments:
        THRESH = -50
        segments = vad_split(energies, hop_size, SAMPLE_RATE, thresh_db=THRESH)
        print(f"降低阈值 {THRESH} dB -> {len(segments)} 个语音段")

    if not segments:
        print("错误：无法检测到语音段")
        sys.exit(1)

    # 合并间隔小于 500ms 的段
    MERGE_GAP = 500
    merged = [list(segments[0])]
    for s, e in segments[1:]:
        if s - merged[-1][1] < MERGE_GAP:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    print(f"合并后: {len(merged)} 个语音段")

    # 分成 3 组
    NUM = 3
    if len(merged) <= NUM:
        total_start = merged[0][0]
        total_end = merged[-1][1]
        seg_len = (total_end - total_start) / NUM
        for i in range(NUM):
            s = total_start + int(seg_len * i)
            e = total_start + int(seg_len * (i + 1)) if i < NUM - 1 else total_end
            out_path = os.path.join(OUTPUT_DIR, f"菲比啾比_{i+1}.mp3")
            export_segment(INPUT, out_path, s, e)
            print(f"  片段 {i+1}: {s/1000:.2f}s - {e/1000:.2f}s ({(e-s)/1000:.2f}s) -> {out_path}")
    else:
        group_size = len(merged) // NUM
        remainder = len(merged) % NUM
        groups = []
        idx = 0
        for i in range(NUM):
            count = group_size + (1 if i < remainder else 0)
            groups.append(merged[idx:idx+count])
            idx += count

        for i, group in enumerate(groups):
            s = group[0][0]
            e = group[-1][1]
            out_path = os.path.join(OUTPUT_DIR, f"菲比啾比_{i+1}.mp3")
            export_segment(INPUT, out_path, s, e)
            print(f"  片段 {i+1}: {s/1000:.2f}s - {e/1000:.2f}s ({(e-s)/1000:.2f}s) -> {out_path}")

    print("VAD 分割完成！")
