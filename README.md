# VeinCodecScanner.py  
A full quality-of-life tool that detects broken MP4 files for Vein and auto-fixes them by converting them to the exact codec Vein currently requires.

This is **not** an ad, not promoting anything, and not distributing any copyrighted content.  
This repo only contains **my Python tool and instructions** explaining how to fix *your own* files on *your own system*.

---

# 📌 What This Tool Does

Vein currently only plays MP4 files that use:

- **H.264** video codec  
- **AAC** audio codec  

If your file uses **HEVC (H.265)** or anything else, Vein won’t play it.  
It won’t load, won’t start, and may even crash the game if you add too many broken files.

I tested:
- Full seasons of **South Park**
- Full seasons of **The Walking Dead**
- Movies
- YouTube videos (yes, URLs work 100%)
- Local files, remote files, and shortened links

After a ton of testing, I confirmed:

### ✔ The ONLY thing that matters is the codec.  
File size doesn’t matter.  
Length doesn’t matter.  
Folder structure doesn’t matter.  

Just the codec.

So I wrote this tool to fix that.

---

# 🚀 What VeinCodecScanner.py Does

This Python script:

### 1️⃣ Scans every MP4 in a folder  
Detects if it's “GOOD” or “BAD” for Vein.

### 2️⃣ Shows you exactly which files fail  
HEVC/H.265 = BAD  
H.264 = GOOD

### 3️⃣ One-click converts ALL bad MP4s into Vein-friendly MP4s  
Using:
- **libx264** (video)
- **aac** (audio)

### 4️⃣ Creates fixed MP4s that work 100% in Vein  
After conversion, every episode/movie works flawlessly.

---

# 🖥 Requirements

To use this tool, you need:

- **Python 3.10+**
- Basic programming comfort (copy/paste commands)
- **FFmpeg installed**
- Windows recommended (works on Mac/Linux too)

---

# 📦 Installation Guide (Step-by-Step)

## Step 1: Install Python
Download from:  
https://www.python.org/downloads/

Make sure to check:  
✔ “Add Python to PATH”

---

## Step 2: Install FFmpeg

Download FFmpeg from:  
https://ffmpeg.org/download.html

Add it to PATH or place `ffmpeg.exe` next to your script.

---

## Step 3: Install Required Python Modules

Run in CMD or PowerShell:

```bash
pip install ffmpeg-python
pip install pillow
```

---

# 🛠 Using VeinCodecScanner.py

## Step 1: Put all your MP4s in one folder  
Examples:

```
SouthPark/
    S01E01.mp4
    S01E02.mp4
    ...
WalkingDead/
Movies/
```

## Step 2: Run the script

```bash
python VeinCodecScanner.py
```

The tool will:

- Scan your folder  
- Label each file GOOD or BAD  
- Allow you to **fix all BAD files** with one button  

---

# 🎯 How It Works

The script converts this:

❌ **HEVC + AAC** → Does NOT work in Vein  
to this:  
✔ **H.264 + AAC** → Works PERFECTLY

Conversion uses:

```
-vcodec libx264
-acodec aac
```

Balanced quality, great size, and compatible with Vein.

---

# 🌐 Using Local URLs (The Meta Method)

I discovered the smoothest method for Vein is using local URLs instead of direct files.

## Step 1: Start a local server
In the folder with your MP4s:

```bash
python -m http.server 8000
```

Now open:

```
http://localhost:8000
```

This shows a webpage listing all your episodes.

Vein accepts this URL perfectly.

## Why this is OP:
- Super clean  
- Fully organized  
- Easy to switch between episodes  
- Zero crashes  
- No limits  
- Best performance  

---

# 🔗 Using Shortened YouTube Links

You can also watch YouTube videos in Vein using a simple 3-step method:

### 1. Get a direct MP4 download link  
(Use any YouTube-to-MP4 site)

### 2. Shorten the huge URL  
Using any URL shortener (tinyurl, shorturl, etc.)

### 3. Paste the shortened link into Vein  
Boom — YouTube videos play fine.

This is extremely immersive for:
- Podcasts  
- Shows  
- Vein videos  
- Music  
- Background entertainment  

---

# 🌍 Using ngrok to Watch Remotely or Share With Friends

If you want your friends to access your files or you want to stream your videos from anywhere:

## Step 1: Install ngrok
https://ngrok.com/

## Step 2: Run it on the same port:

```bash
ngrok http 8000
```

It will give you:

```
https://something.ngrok-free.app
```

This is now a **public URL** for all your MP4s.

Paste it into Vein → it works instantly.

Your PC becomes a temporary media server in one command.

Completely free.

---

# 📁 Recommended Folder Organization

```
Media/
   SouthPark/
      Season1/
      Season2/
   WalkingDead/
      Season1/
   Movies/
```

Keeps everything clean and easy to navigate inside Vein.

---

# 🧪 Why This Works

The game engine currently:
- **Only accepts H.264 + AAC**
- Loads MP4s through a web viewer internally
- Treats URLs and local URLs the exact same way

Until Vein universally supports all MP4 formats, this tool is the only reliable way to fix incompatible files.

---

# ⚠ Disclaimer

- I do **not** provide copyrighted content  
- I do **not** provide download links  
- I do **not** host or distribute media  
- Everything here is **strictly educational**  
- You are responsible for any content you use  

This repo only exists to fix codec incompatibility issues for Vein.

---

# ❤️ Final Words

I love this game and I want to see it succeed.  
The media feature is one of my absolute favorites, and fixing these codec issues boosts immersion like crazy.

VeinCodecScanner.py is my personal QoL solution until the game eventually supports all MP4 formats natively.

Enjoy, stay safe, and keep surviving.

---

# 📜 License

This project is released under the **MIT License**.

You can copy it, fork it, modify it, or use it anywhere — just don’t blame me if anything breaks.

