import asyncio, json, os, subprocess, textwrap, ssl, certifi
certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
_o = ssl.create_default_context
ssl.create_default_context = lambda *a, **k: _o(cafile="/root/.ccr/ca-bundle.crt")
import edge_tts
from PIL import Image, ImageDraw, ImageFont

D = "/tmp/claude-0/vid"; F = f"{D}/frames"; A = f"{D}/audio"; S = f"{D}/stills"; V = f"{D}/seg"
for d in (A, S, V): os.makedirs(d, exist_ok=True)
NAR, CALLER, YOU, BANK = "en-GB-SoniaNeural", "ms-MY-OsmanNeural", "ms-MY-YasminNeural", "en-SG-LunaNeural"

police = json.load(open("/home/claude/next-byte-hack/app/data/scenarios.json"))["scenarios"][0]["lines"]
EN = [
 "Good afternoon, ma'am. I'm Sergeant Tan from Bukit Aman police headquarters, Commercial Crime Investigation Department.",
 "Yes, what is it?",
 "We found your IC number was used to open a bank account involved in a money-laundering case.",
 "What? I never opened another account.",
 "The court has issued an arrest warrant in your name. If you don't cooperate, you'll be arrested within 24 hours.",
 "Oh God, what should I do?",
 "This case is confidential. Don't tell anyone, not even your children. Don't hang up.",
 "To prove you're innocent, move all your savings to a Bank Negara 'safe account' for the investigation.",
 "Write down this account number: 7612 4409 8831. Deposit RM48,000 today.",
]

# (frame, voice, text, caption, pad_after, kind)
segs = [
 ("card_hook", NAR, "Last year, Malaysians lost almost three billion ringgit to scams.", None, 0.8, "card"),
 ("card_story", NAR, "In Kuching, a seventy-two-year-old woman lost one point three million ringgit to a man who said he was Sergeant Tan.", None, 0.8, "card"),
 ("card_gap", NAR, "The warnings exist. But nobody checks them during the call.", None, 0.8, "card"),
 ("police_0", NAR, "This is ScamShield. When a call feels wrong, she puts it on speaker and taps one button.", "This is ScamShield. When a call feels wrong, she puts it on speaker and taps one button.", 0.5, "app"),
]
for i, line in enumerate(police, start=1):
    if i in (4, 6):
        continue  # trimmed for length; the lines still show in the transcript
    voice = CALLER if line["speaker"] == "caller" else YOU
    who = "Caller" if line["speaker"] == "caller" else "Her"
    segs.append((f"police_{i}", voice, line["text"], f"{who}: {EN[i-1]}", 0.35, "app"))
    if i == 7:
        segs.append(("police_7", YOU, "Amaran. Ini mungkin penipuan. Polis dan bank tidak akan minta anda pindahkan wang atau beri kod. Letak telefon sekarang.", "ScamShield (spoken): Warning. This may be a scam. Police and banks will never ask you to move money or give a code. Hang up now.", 0.4, "app"))
        segs.append(("police_7", NAR, "About thirty seconds in, before any money moves, the whole screen turns red, and it tells her, out loud, to hang up.", "About thirty seconds in, before any money moves, the screen turns red and it tells her, out loud, to hang up.", 0.5, "app"))
segs += [
 ("police_numbers", NAR, "The account number the caller read out is checked against reported mule accounts.", "The account number the caller read out is checked against reported mule accounts (sample registry in this prototype).", 0.5, "app"),
 ("card_wa", NAR, "And one tap sends her family a message with the scam type and the number the caller gave.", None, 0.6, "card"),
 ("bank_3", NAR, "It also knows when not to panic. Here, a real bank checks a card payment.", "It also knows when not to panic. Here, a real bank checks a card payment.", 0.4, "app"),
 ("bank_5", BANK, "As a reminder, Maybank will never ask you for your OTP, PIN or password, and will never ask you to transfer money to another account.", "Bank: As a reminder, Maybank will never ask you for your OTP, PIN or password, and will never ask you to transfer money to another account.", 0.4, "app"),
 ("bank_end", NAR, "It only says it will never ask, so ScamShield stays calm.", "It only says it will never ask, so ScamShield stays calm.", 0.6, "app"),
 ("card_how", NAR, "Two analysts read every call: a rules engine built from police scam advisories, and Gemini, which must quote the caller's exact words.", None, 0.7, "card"),
 ("card_res", NAR, "On ten test calls, it flagged all six scams, with no false alarms on the four real ones.", None, 0.7, "card"),
 ("dash", NAR, "After the call, an anonymous report shows which scams are active right now. No recording, no transcript.", "After the call, an anonymous report shows which scams are active right now. No recording, no transcript.", 0.6, "app"),
 ("card_end", NAR, "ScamShield. Letak telefon, before the money moves.", None, 1.6, "card"),
]

MAP = {}
async def tts(i, voice, text):
    import hashlib
    out = f"{A}/" + hashlib.md5((voice + text).encode()).hexdigest() + ".mp3"
    MAP[i] = out
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        rate = "-4%" if voice == NAR else "+0%"
        await edge_tts.Communicate(text, voice, rate=rate).save(out)
    return out

async def all_tts():
    for i, s in enumerate(segs):
        await tts(i, s[1], s[2])
asyncio.run(all_tts())

def dur(p):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).strip())

font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 38)
def still(i, frame, caption):
    im = Image.open(f"{F}/{frame}.jpg").convert("RGB")
    if caption:
        lines = textwrap.wrap(caption, 78)[:3]
        lh = 50; h = lh*len(lines) + 40
        ov = Image.new("RGBA", im.size, (0,0,0,0)); d = ImageDraw.Draw(ov)
        d.rectangle([0, 1080-h, 1920, 1080], fill=(10,18,32,238))
        for k, ln in enumerate(lines):
            w = d.textlength(ln, font=font)
            d.text(((1920-w)/2, 1080-h+20+k*lh), ln, font=font, fill=(255,255,255,255))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    p = f"{S}/{i:02d}.jpg"; im.save(p, quality=92); return p

concat_v, concat_a = [], []
total = 0
for i, (frame, voice, text, cap, pad, kind) in enumerate(segs):
    a = MAP[i]; ad = dur(a)
    lead = 0.25
    T = round(lead + ad + pad, 3)
    img = still(i, frame, cap)
    vf = f"format=yuv420p,loop=-1:1,trim=duration={T},setpts=PTS-STARTPTS"
    if kind == "card" or i == 0:
        vf += f",fade=t=in:st=0:d=0.3"
    if kind == "card" or i == len(segs)-1:
        vf += f",fade=t=out:st={T-0.3}:d=0.3"
    tmp = f"{V}/{i:02d}.tmp.mp4"; out = f"{V}/{i:02d}.mp4"
    subprocess.run(["ffmpeg","-y","-v","error","-framerate","30","-i",img,"-vf",vf,"-r","30","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p","-t",str(T),tmp], check=True)
    os.replace(tmp, out)
    wav = f"{A}/{i:02d}.wav"
    subprocess.run(["ffmpeg","-y","-v","error","-i",a,"-af",f"adelay={int(lead*1000)},apad,atrim=0:{T}","-ar","48000","-ac","2",wav], check=True)
    concat_v.append(out); concat_a.append(wav); total += T
    print(f"{i:02d} {frame:16} {T:6.2f}s  total {total:6.1f}", flush=True)

open(f"{D}/v.txt","w").write("".join(f"file '{p}'\n" for p in concat_v))
open(f"{D}/a.txt","w").write("".join(f"file '{p}'\n" for p in concat_a))
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",f"{D}/v.txt","-c","copy",f"{D}/video_only.mp4"], check=True)
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",f"{D}/a.txt","-af","loudnorm=I=-16:TP=-1.5","-ar","48000",f"{D}/audio.wav"], check=True)
subprocess.run(["ffmpeg","-y","-v","error","-i",f"{D}/video_only.mp4","-i",f"{D}/audio.wav","-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",f"{D}/ScamShield_MY_demo.tmp.mp4"], check=True)
os.replace(f"{D}/ScamShield_MY_demo.tmp.mp4", f"{D}/ScamShield_MY_demo.mp4")
print("TOTAL", total)
