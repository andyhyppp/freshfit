# FreshFit: Personal Outfit & Wardrobe Copilot

FreshFit is a multi-agent CLI assistant built on Google's Agent Developer Kit (ADK). It orchestrates specialized AI agents to help you manage your closet and plan outfits based on real-time weather, occasion, and your personal style history.

## 🚀 Features

### **1. Intelligent Outfit Planning**
- **Context-Aware**: Checks the weather (via Google Search) and your specified occasion (e.g., "date night", "hiking").
- **Wardrobe Rotation**: Prioritizes items you haven't worn recently.
- **Smart Ranking**: Scores outfits based on color harmony, weather suitability, and your past ratings.
- **Explanations**: Tells you *why* a look works ("The wool coat balances the 12°C chill...").

### **2. Wardrobe Management**
- **Natural Language Controls**: "Add this white linen shirt" or "Delete those old ripped jeans."
- **Automatic Tagging**: Infers category, warmth, and formality from your descriptions.

### **3. Feedback Loop**
- **Learning**: Rates outfits (1-5 stars) to refine future suggestions.
- **History**: Tracks what you wore to prevent repetition.

## 🛠️ Installation & Usage

1. **Prerequisites**:
   - Python 3.10+
   - Google Cloud Project with Gemini API enabled

2. **Setup**:
   ```bash
   # Clone the repo
   git clone https://github.com/yourusername/freshfit.git
   cd freshfit

   # Install dependencies
   pip install -r requirements.txt

   # Configure environment
   cp .env.example .env
   # Add your GOOGLE_API_KEY to .env
   ```

3. **Run the Assistant**:
   ```bash
   python main.py
   ```
   You will see the welcome menu:
   ```text
     ______              _       ______ _ _
    |  ____|            | |     |  ____(_) |
    | |__ _ __ ___  ___ | |__   | |__   _| |_
    |  __| '__/ _ \/ __|| '_ \  |  __| | | __|
    | |  | | |  __/\__ \| | | | | |    | | |_
    |_|  |_|  \___||___/|_| |_| |_|    |_|\__|

                Smart Wardrobe Assistant
   ```

## 🤖 Architecture

FreshFit uses a graph of specialized ADK agents:
- **Router**: Directs traffic between "Outfit Flow" and "Wardrobe Management".
- **Weather Agent**: Fetches live forecast data.
- **Wardrobe Cataloger**: Filters your database for available, clean clothes.
- **Outfit Designer**: Composes stylistically valid looks.
- **Preference Ranking**: Re-ranks candidates based on your history.
- **Explanation Agent**: Generates user-friendly rationales.
- **Feedback Agent**: Captures ratings to close the learning loop.

## 📄 License
MIT