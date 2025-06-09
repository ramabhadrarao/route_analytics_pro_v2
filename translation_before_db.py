# translation_before_db.py - Add translation before storing to database
# Purpose: Translate any non-English text to English before database storage
# This prevents Unicode issues in PDF generation completely

import re
import os
import sqlite3
from typing import Optional, Dict, Any, List

# Option 1: Google Translate (Recommended - most accurate)
try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    print("⚠️ googletrans not installed. Install with: pip install googletrans==4.0.0rc1")

# Option 2: Deep Translator (Alternative)
try:
    from deep_translator import GoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False
    print("⚠️ deep-translator not installed. Install with: pip install deep-translator")

# Option 3: textblob (Simple option)
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️ textblob not installed. Install with: pip install textblob")

class TextTranslator:
    """Translate text to English before database storage"""
    
    def __init__(self, preferred_method='googletrans'):
        self.preferred_method = preferred_method
        self.translator = None
        self.setup_translator()
        
        # Cache for translated text to avoid repeated API calls
        self.translation_cache = {}
        
    def setup_translator(self):
        """Setup the preferred translation method"""
        if self.preferred_method == 'googletrans' and GOOGLETRANS_AVAILABLE:
            self.translator = Translator()
            print("✅ Using Google Translate (googletrans)")
            
        elif self.preferred_method == 'deep_translator' and DEEP_TRANSLATOR_AVAILABLE:
            self.translator = GoogleTranslator(source='auto', target='en')
            print("✅ Using Deep Translator")
            
        elif self.preferred_method == 'textblob' and TEXTBLOB_AVAILABLE:
            # TextBlob will be used in translate method
            print("✅ Using TextBlob translator")
            
        else:
            print("⚠️ No translation library available, using fallback method")
            self.translator = None
    
    def is_english(self, text: str) -> bool:
        """Check if text is primarily in English"""
        if not text:
            return True
            
        # Check for non-ASCII characters (likely non-English)
        non_ascii_count = sum(1 for char in text if ord(char) > 127)
        total_chars = len(text)
        
        # If more than 20% non-ASCII characters, likely not English
        if total_chars > 0 and (non_ascii_count / total_chars) > 0.2:
            return False
            
        return True
    
    def translate_to_english(self, text: str) -> str:
        """
        Translate text to English if it's not already in English
        
        Args:
            text (str): Text to translate
            
        Returns:
            str: English translation of the text
        """
        if not text or not text.strip():
            return text
            
        text = str(text).strip()
        
        # Check cache first
        if text in self.translation_cache:
            return self.translation_cache[text]
        
        # If already English, return as-is
        if self.is_english(text):
            self.translation_cache[text] = text
            return text
        
        try:
            translated = self._perform_translation(text)
            
            # Cache the result
            self.translation_cache[text] = translated
            
            print(f"🔤 Translated: '{text}' → '{translated}'")
            return translated
            
        except Exception as e:
            print(f"⚠️ Translation failed for '{text}': {e}")
            # Fallback: extract ASCII characters
            fallback = self._extract_ascii_fallback(text)
            self.translation_cache[text] = fallback
            return fallback
    
    def _perform_translation(self, text: str) -> str:
        """Perform the actual translation using available library"""
        
        if self.preferred_method == 'googletrans' and self.translator:
            # Using googletrans
            result = self.translator.translate(text, dest='en')
            return result.text
            
        elif self.preferred_method == 'deep_translator' and self.translator:
            # Using deep-translator
            return self.translator.translate(text)
            
        elif self.preferred_method == 'textblob' and TEXTBLOB_AVAILABLE:
            # Using textblob
            blob = TextBlob(text)
            return str(blob.translate(to='en'))
            
        else:
            # Fallback method
            return self._extract_ascii_fallback(text)
    
    def _extract_ascii_fallback(self, text: str) -> str:
        """Fallback method when no translator is available"""
        # Extract ASCII characters and add note
        ascii_chars = ''.join(char if ord(char) <= 127 else ' ' for char in text)
        ascii_text = ' '.join(ascii_chars.split()).strip()
        
        if ascii_text:
            return f"{ascii_text} [Translated]"
        else:
            return "[Non-English location]"

# PATCH FOR YOUR EXISTING route_analyzer.py
# Add this method to your RouteAnalyzer class:

def setup_translator(self):
    """Setup text translator for non-English content"""
    try:
        self.text_translator = TextTranslator(preferred_method='googletrans')
        print("✅ Text translator initialized")
    except Exception as e:
        print(f"⚠️ Translator setup failed: {e}")
        self.text_translator = None

# UPDATE your existing store_pois method in db_manager.py:
def store_pois_with_translation(self, route_id: str, pois: Dict, poi_type: str, translator=None) -> bool:
    """
    Store points of interest with automatic translation to English
    
    REPLACE your existing store_pois method with this one
    """
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for name, address in pois.items():
                # Translate name and address to English if needed
                if translator:
                    english_name = translator.translate_to_english(name)
                    english_address = translator.translate_to_english(address)
                else:
                    # Fallback: use original text
                    english_name = name
                    english_address = address
                
                # Extract coordinates if available (simplified)
                lat, lng = 0.0, 0.0  # Would be calculated from address
                
                cursor.execute("""
                    INSERT INTO pois 
                    (route_id, poi_type, name, latitude, longitude, address)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (route_id, poi_type, english_name, lat, lng, english_address))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error storing POIs: {e}")
        return False

# UPDATE your RouteAnalyzer.__init__ method:
def __init__(self, api_tracker):
    self.api_tracker = api_tracker
    self.db_manager = api_tracker.db_manager
    
    # Initialize API clients
    self.google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    self.openweather_api_key = os.environ.get('OPENWEATHER_API_KEY')
    
    if self.google_api_key:
        self.gmaps = googlemaps.Client(key=self.google_api_key)
    else:
        self.gmaps = None
        print("⚠️ Google Maps API key not configured")
    
    # ADD THIS LINE: Setup translator
    self.setup_translator()

# UPDATE your _analyze_and_store_pois method:
def _analyze_and_store_pois_with_translation(self, route_id: str, route_points: list):
    """
    Updated method to find and store POIs with automatic English translation
    
    REPLACE your existing _analyze_and_store_pois method with this one
    """
    if not self.gmaps:
        return
    
    # Sample points for POI search
    step = max(1, len(route_points) // 10)
    sampled_points = route_points[::step]
    
    poi_types = {
        'hospital': 'hospital',
        'gas_station': 'gas_station', 
        'school': 'school',
        'restaurant': 'restaurant',
        'police': 'police',
        'fire_station': 'fire_station'
    }
    
    for poi_type, google_type in poi_types.items():
        print(f"🔍 Searching for {poi_type}s...")
        pois_found = {}
        
        for point in sampled_points[:5]:  # Limit search points
            try:
                # Search with English preference first
                places = self._search_nearby_places(point[0], point[1], google_type)
                
                for place in places[:3]:  # Top 3 per location
                    name = place.get('name', 'Unknown')
                    vicinity = place.get('vicinity', 'Unknown location')
                    
                    # Translate to English if needed
                    if self.text_translator:
                        english_name = self.text_translator.translate_to_english(name)
                        english_vicinity = self.text_translator.translate_to_english(vicinity)
                    else:
                        english_name = name
                        english_vicinity = vicinity
                    
                    pois_found[english_name] = english_vicinity
                    
            except Exception as e:
                print(f"Error searching {poi_type}: {e}")
        
        if pois_found:
            # Store with translation capability
            self.db_manager.store_pois_with_translation(route_id, pois_found, poi_type, self.text_translator)
            print(f"✅ Stored {len(pois_found)} {poi_type}s (translated to English)")

# INSTALLATION INSTRUCTIONS:
"""
QUICK SETUP:

1. Install translation library (choose one):
   pip install googletrans==4.0.0rc1    # Recommended
   # OR
   pip install deep-translator            # Alternative
   # OR  
   pip install textblob                   # Simple option

2. Add translator setup to your RouteAnalyzer.__init__ method (see above)

3. Replace your _analyze_and_store_pois method with _analyze_and_store_pois_with_translation

4. Update your db_manager.py store_pois method to store_pois_with_translation

That's it! Now all POI names and addresses will be automatically translated to English 
before being stored in the database, preventing Unicode issues in PDF generation.
"""

# Test function
def test_translator():
    """Test the translation functionality"""
    translator = TextTranslator()
    
    test_texts = [
        "देवी पुलिस स्टेशन",  # Hindi police station
        "মুম্বই হাসপাতাল",      # Bengali hospital
        "சென்னை பெட்ரோல் பங்க்",  # Tamil gas station
        "Regular English Text",
        "రైల్వే స్టేషన్"        # Telugu railway station
    ]
    
    print("🧪 Testing Translation:")
    print("-" * 40)
    
    for text in test_texts:
        translated = translator.translate_to_english(text)
        print(f"'{text}' → '{translated}'")

if __name__ == "__main__":
    test_translator()