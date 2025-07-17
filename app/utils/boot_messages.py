import random

BOOT_MESSAGES = [
    "🚀 Pied Piper: Compressing your STL… middle-out.",
    "🦄 Hooli printer detected: preparing to sabotage.",
    "📈 Jared is optimizing your layer adhesion… kindly.",
    "👓 Erlich demanded a 10% stake in your nozzle.",
    "🍯 Jian-Yang claims your print is ‘hot dog or not hot dog.’",
    "📦 Gavin Belson: ‘We’re making the world a better place… through stringing.’",
    "💻 Gilfoyle rewrote your slicer in Bash just to spite you.",
    "🕵️ Dinesh’s printer security: compromised.",
    "🎯 Pied Piper: Now printing at 5x compression ratio.",
    "🏠 Aviato! The official travel partner for Benchies.",
    "🐖 Gavin’s Signature Layer Shift™ in progress.",
    "🛑 ‘If we can’t print at scale, we don’t deserve to print at all.’",
    "🧼 Jared is cleaning your nozzle with gentle affirmation.",
    "📡 Hooli printer telemetry: spying on your G-code.",
    "📉 Dinesh’s print: still stringy despite higher infill.",
    "🧪 Erlich invested your filament budget in a blockchain printer.",
    "📠 ‘Hot dog? Not hot dog.’ Checking filament type.",
    "🔒 Gilfoyle encrypted your STL out of spite.",
    "🎨 Gavin’s Visionary Overhang™ failing gracefully.",
    "🕶️ ‘It’s not whether you win or lose. It’s whether you’ve leveled the bed.’ – Jared",
    "💥 Your print failed because of compression conflicts with Nucleus.",
    "📜 Richard rewrote your slicer engine overnight. It now crashes beautifully.",
    "👑 Erlich: ‘You’re welcome for the adhesion. Pay me rent.’",
    "🍔 Jian-Yang printed a dumpling tray instead of your Benchy.",
    "🎮 ‘This printer is worth more dead than alive.’ — Gilfoyle",
]



def random_boot_message() -> str:
    return random.choice(BOOT_MESSAGES)
