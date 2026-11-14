"""Self-check for hardware codec detection: python3 tests/test_hw.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import quicktube as q

g = q.codec_from_gpu_name
assert g("Intel(R) Core(TM) i7-6500U CPU @ 2.50GHz") == "h264"
assert g("Intel(R) Core(TM) i7-7820HQ CPU") == "vp9"
assert g("Intel(R) Core(TM) i5-1035G1 CPU") == "vp9"
assert g("12th Gen Intel(R) Core(TM) i5-1235U") == "av1"
assert g("Intel(R) UHD Graphics 620") == "h264"  # unknown Intel name -> safe fallback
assert g("NVIDIA GeForce RTX 3060") == "av1"
assert g("NVIDIA GeForce GTX 1060 6GB") == "vp9"
assert g("NVIDIA Quadro P3000") == "h264"
assert g("AMD Radeon RX 6600") == "av1"
assert g("AMD Radeon RX 580") == "h264"
assert g("AMD Radeon RX 5700 XT") == "vp9"
assert g("AMD Ryzen 7 7840U w/ Radeon 780M Graphics") == "av1"
assert g("Microsoft Basic Display Adapter") is None

v = """VAProfileH264High               :	VAEntrypointVLD
VAProfileVP9Profile0            :	VAEntrypointVLD
VAProfileAV1Profile0            :	VAEntrypointEncSlice"""
assert q.codec_from_vainfo(v) == "vp9"  # AV1 encode only does not count
assert q.codec_from_vainfo("") is None

q.CODEC_PREF, q.MAX_HEIGHT = "h264", 1080
assert q.format_sort() == "res:1080,vcodec:h264"
assert q.codec_ok({"vcodec": "avc1.640028"}) and not q.codec_ok({"vcodec": "vp09.00.40.08"})
q.CODEC_PREF, q.MAX_HEIGHT = "av1", None
assert q.format_sort() == ""
print("ok")
