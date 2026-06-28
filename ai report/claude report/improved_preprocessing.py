"""
Improved Preprocessing for Sentiment Analysis Comments
=======================================================
Script untuk memperbaiki preprocessing dataset sentiment analysis

Fitur:
- Slang & typo fixing (comprehensive dictionary)
- Better emoji handling dengan sentiment awareness
- Selective stopword removal (preserve critical words)
- Context preservation
- Quality flagging untuk dokumen problematic
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import sys

class ImprovedSentimentPreprocessor:
    """Preprocessor dengan pemeliharaan context dan sentiment signals"""
    
    def __init__(self):
        """Initialize preprocessing dictionaries dan rules"""
        
        # ============ SLANG & TYPO DICTIONARY ============
        # CRITICAL: Top typos dengan frekuensi tinggi
        self.slang_dict = {
            # High frequency slang (CRITICAL)
            'u': 'yang',              # 11,964 kemunkulan!
            'gk': 'tidak',            # 1,362 kemunkulan
            'lo': 'kamu',             # 872
            'sy': 'saya',             # 689
            'elu': 'kamu',            # 671
            'kok': 'mengapa',         # 443
            'gak': 'tidak',           # 192
            'gx': 'tidak',
            'apai': 'apa',            # 180
            'dr': 'dari',             # 178
            'ndak': 'tidak',          # 98
            'nggak': 'tidak',         # 56
            
            # Medium frequency
            'bg': 'bang',             # 46
            'bro': 'saudara',         # 45
            'klo': 'kalau',           # 12
            'klu': 'kalau',           # 38
            'yg': 'yang',             # 14
            'dgn': 'dengan',
            
            # Specific typos
            'danantara': 'dana tatra',  # 35
            'plong': 'kosong',          # 10
            'adai': 'ada',              # 22
            'wk': 'wkwk',               # 30
            'wkwk': 'tertawa',
            'wkwkw': 'tertawa',
            
            # Important context typos
            'suriahi': 'suriah',
            'aerbbmenarik': 'aer menarik',
            'koruptot': 'koruptor',
            'menlanjutkan': 'melanjutkan',
            'iggbii': '1998',
            'korupsii': 'korupsi',
            'indoi': 'indonesia',
            'buruk': 'buruk',  # Keep as is (sentiment word)
            'bernyas': 'mengejar',
            'ngebayangin': 'membayangkan',
            'nyabkmna': 'pikiranya',
            'plong': 'kosong',
            'dini': 'dini',  # Keep
            'jka': 'jika',
        }
        
        # ============ EMOJI SENTIMENT MAPPING ============
        # Map emoji to sentiment-aware labels, bukan generic 'emo_other'
        self.emoji_sentiment_map = {
            # Laugh/amused
            '😂😂': '[LAUGH_POS]', '🤣': '[LAUGH_POS]', '😆': '[LAUGH_POS]',
            '😄': '[HAPPY_POS]', '😃': '[HAPPY_POS]', '😁': '[SMILE_POS]',
            
            # Sad/negative emotions
            '😭': '[SAD_NEG]', '😢': '[SAD_NEG]', '😞': '[SAD_NEG]',
            '😔': '[DISAPPOINTED_NEG]', '😕': '[CONFUSED]',
            
            # Angry/frustrated
            '😡': '[ANGRY_NEG]', '🤬': '[ANGRY_NEG]', '😠': '[ANGRY_NEG]',
            
            # Approval/positive
            '👍': '[APPROVE_POS]', '💪': '[STRONG_POS]', '👏': '[APPLAUSE_POS]',
            '❤️': '[LOVE_POS]', '🎉': '[CELEBRATE_POS]',
            
            # Disapproval/negative
            '👎': '[DISAPPROVE_NEG]', '❌': '[REJECT_NEG]', '⛔': '[BLOCK_NEG]',
            '💔': '[HEARTBREAK_NEG]',
            
            # Thinking/sarcasm
            '🤔': '[THINK]', '😒': '[SARCASM_NEG]', '😑': '[UNIMPRESSED_NEG]',
            
            # Prayer/hope
            '🙏': '[HOPE_POS]',
            
            # Negative symbols
            '💩': '[CRAP_NEG]', '🐀': '[RAT_NEG]',
        }
        
        # ============ CRITICAL SENTIMENT WORDS ============
        # Words yang HARUS dipertahankan karena important untuk sentiment
        self.critical_words = {
            # Negations - SANGAT PENTING
            'tidak', 'bukan', 'tanpa', 'jangan', 'nih', 'aja',
            
            # Intensifiers - important for sentiment strength
            'sangat', 'amat', 'begitu', 'banget', 'sekali', 'luar',
            'banyak', 'sedikit',
            
            # Sentiment adjectives - CORE sentiment words
            'baik', 'buruk', 'bagus', 'jelek', 'bagus', 'busuk',
            'sempurna', 'parah', 'hebat', 'membosankan',
            'indah', 'jelek', 'menakutkan', 'menyenangkan',
            'mengesankan', 'mengecewakan', 'memuaskan',
            
            # Sentiment verbs
            'cinta', 'benci', 'suka', 'duka', 'khawatir',
            'takut', 'marah', 'gembira', 'sedih', 'heran',
            
            # Action words related to sentiment
            'korupsi', 'koruptor', 'suap', 'mati', 'hidup',
            'membunuh', 'menolong', 'merugikan', 'menguntungkan',
        }
        
        # ============ LANGUAGE DETECTION ============
        self.english_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were',
            'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'and', 'or', 'but', 'in', 'on', 'at', 'to', 'from',
            'what', 'how', 'why', 'when', 'where', 'who',
            'can', 'will', 'would', 'should', 'could',
            'power', 'corrupts', 'absolutely', 'absolute',
        }
        
    def fix_slang(self, text: str) -> str:
        """
        Fix slang dan typo menggunakan dictionary
        
        Args:
            text: Input text
            
        Returns:
            Text dengan slang/typo diperbaiki
        """
        # Create regex pattern dengan word boundaries
        pattern = r'\b(' + '|'.join(re.escape(k) for k in self.slang_dict.keys()) + r')\b'
        
        def replace_func(match):
            word = match.group(0)
            return self.slang_dict.get(word.lower(), word)
        
        return re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
    
    def fix_emoji(self, text: str) -> str:
        """
        Better emoji handling dengan sentiment awareness
        
        Args:
            text: Input text dengan emoji
            
        Returns:
            Text dengan emoji diganti sentiment-aware labels
        """
        # Apply known emoji mappings
        for emoji, label in self.emoji_sentiment_map.items():
            text = text.replace(emoji, f' {label} ')
        
        # Handle unknown emojis secara lebih spesifik
        # Emoji ranges di Unicode
        emoji_pattern = r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]'
        
        def replace_unknown_emoji(match):
            emoji = match.group(0)
            # Heuristic: based on emoji character
            if emoji in '😂🤣😆😄😃':
                return '[LAUGH_POS]'
            elif emoji in '😭😢😞':
                return '[SAD_NEG]'
            elif emoji in '👍💪':
                return '[APPROVE_POS]'
            elif emoji in '❌⛔':
                return '[REJECT_NEG]'
            else:
                return '[EMOJI]'
        
        text = re.sub(emoji_pattern, replace_unknown_emoji, text)
        
        return text
    
    def selective_stopword_removal(self, text: str, all_stopwords: set) -> str:
        """
        Remove hanya non-critical stopwords
        Preserve sentiment-critical words
        
        Args:
            text: Input text
            all_stopwords: Set of all stopwords
            
        Returns:
            Text dengan non-critical stopwords dihapus
        """
        # Stopwords yang BOLEH dihapus (non-critical)
        removable_stopwords = all_stopwords - self.critical_words
        
        words = text.split()
        filtered = []
        
        for word in words:
            # Preserve: sentiment labels, numbers, critical words
            if word.startswith('[') and word.endswith(']'):  # Emoji labels
                filtered.append(word)
            elif word.isdigit():  # Numbers
                filtered.append(word)
            elif word.lower() not in removable_stopwords:
                filtered.append(word)
        
        return ' '.join(filtered)
    
    def cleanup_special_chars(self, text: str) -> str:
        """
        Clean special characters tapi preserve punctuation yang penting
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Keep: letters, numbers, underscore, hyphen, brackets (for labels)
        text = re.sub(r'[^\w\s\-\[\]]', ' ', text)
        return text
    
    def cleanup_whitespace(self, text: str) -> str:
        """Clean multiple spaces dan trim"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def detect_language_mix(self, text: str) -> Tuple[float, float]:
        """
        Detect apakah ada campuran English-Indonesian
        
        Returns:
            (english_ratio, indonesian_ratio)
        """
        words = text.lower().split()
        english_count = sum(1 for w in words if w in self.english_words)
        total = len(words)
        
        english_ratio = english_count / total if total > 0 else 0
        indonesian_ratio = 1 - english_ratio
        
        return english_ratio, indonesian_ratio
    
    def is_low_quality(self, text: str) -> Tuple[bool, str]:
        """
        Flag dokumen dengan kualitas rendah
        
        Returns:
            (is_low_quality, reason)
        """
        words = text.split()
        
        # Terlalu pendek
        if len(words) < 3:
            return True, f"too_short ({len(words)} words)"
        
        # Hanya emoji labels
        if all(w.startswith('[') and w.endswith(']') for w in words if w):
            return True, "only_emoji_labels"
        
        # Terlalu banyak emoji labels (>50% dari dokumen)
        emoji_count = sum(1 for w in words if w.startswith('[') and w.endswith(']'))
        if emoji_count / len(words) > 0.5:
            return True, f"mostly_emoji ({emoji_count}/{len(words)})"
        
        return False, "good"
    
    def process(self, 
                text_original: str, 
                remove_stopwords: bool = False,
                all_stopwords: Optional[set] = None,
                preserve_original_length: bool = True) -> Dict[str, any]:
        """
        Full preprocessing pipeline
        
        Args:
            text_original: Original text
            remove_stopwords: Whether to remove non-critical stopwords
            all_stopwords: Set of stopwords to use
            preserve_original_length: Keep original if final too short
            
        Returns:
            Dictionary dengan processed text dan metadata
        """
        
        original_length = len(text_original.split())
        text = text_original
        
        # 1. Fix slang & typo
        text = self.fix_slang(text)
        
        # 2. Handle emoji
        text = self.fix_emoji(text)
        
        # 3. Lowercase (but keep labels in brackets)
        # Preserve: [LABEL] case
        text = re.sub(r'([a-zA-Z])', lambda m: m.group(1).lower(), text)
        
        # 4. Remove unnecessary special characters
        text = self.cleanup_special_chars(text)
        
        # 5. Optional: selective stopword removal
        if remove_stopwords and all_stopwords:
            text = self.selective_stopword_removal(text, all_stopwords)
        
        # 6. Clean whitespace
        text = self.cleanup_whitespace(text)
        
        # 7. Quality check
        is_low, reason = self.is_low_quality(text)
        
        # 8. If too short, optionally use original
        if preserve_original_length and is_low and reason.startswith('too_short'):
            text = text_original.lower()
            is_low = False
            reason = "used_original_due_to_short_final"
        
        # 9. Detect language mix
        english_ratio, indonesian_ratio = self.detect_language_mix(text)
        
        # Calculate compression ratio
        final_length = len(text.split())
        compression = ((original_length - final_length) / original_length * 100) if original_length > 0 else 0
        
        return {
            'text_original': text_original,
            'text_processed': text,
            'original_length': original_length,
            'final_length': final_length,
            'compression_ratio': compression,
            'quality': 'low' if is_low else 'good',
            'quality_reason': reason,
            'english_ratio': english_ratio,
            'indonesian_ratio': indonesian_ratio,
        }


def process_dataset(input_file: str, 
                    output_file: str,
                    remove_stopwords: bool = False,
                    all_stopwords: Optional[set] = None,
                    sample_size: Optional[int] = None,
                    verbose: bool = True) -> Dict[str, any]:
    """
    Process entire dataset
    
    Args:
        input_file: Path ke JSON input
        output_file: Path untuk JSON output
        remove_stopwords: Whether to apply stopword removal
        all_stopwords: Set of stopwords
        sample_size: Process hanya N dokumen (for testing)
        verbose: Print progress
        
    Returns:
        Statistics tentang processing
    """
    
    preprocessor = ImprovedSentimentPreprocessor()
    
    # Load data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if sample_size:
        data = data[:sample_size]
    
    # Process
    processed_data = []
    stats = {
        'total': len(data),
        'good_quality': 0,
        'low_quality': 0,
        'too_short': 0,
        'mostly_emoji': 0,
        'avg_compression': 0,
        'avg_english_ratio': 0,
    }
    
    for idx, doc in enumerate(data):
        if verbose and idx % 1000 == 0:
            print(f"Processing {idx}/{len(data)}...")
        
        result = preprocessor.process(
            doc['text_original'],
            remove_stopwords=remove_stopwords,
            all_stopwords=all_stopwords
        )
        
        # Add original fields
        processed_doc = {
            '_id': doc.get('_id'),
            'comment_id': doc.get('comment_id'),
            'video_id': doc.get('video_id'),
            'text_original': doc['text_original'],
            'text_final_original': doc.get('text_final'),
            'text_final_improved': result['text_processed'],
            'metadata': {
                'original_length': result['original_length'],
                'final_length': result['final_length'],
                'compression_ratio': result['compression_ratio'],
                'quality': result['quality'],
                'quality_reason': result['quality_reason'],
                'english_ratio': result['english_ratio'],
            }
        }
        
        processed_data.append(processed_doc)
        
        # Update stats
        if result['quality'] == 'good':
            stats['good_quality'] += 1
        else:
            stats['low_quality'] += 1
            if 'too_short' in result['quality_reason']:
                stats['too_short'] += 1
            if 'mostly_emoji' in result['quality_reason']:
                stats['mostly_emoji'] += 1
        
        stats['avg_compression'] += result['compression_ratio']
        stats['avg_english_ratio'] += result['english_ratio']
    
    # Calculate averages
    stats['avg_compression'] /= len(data)
    stats['avg_english_ratio'] /= len(data)
    
    # Save output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Processing Complete!")
        print(f"{'='*60}")
        print(f"Total documents: {stats['total']}")
        print(f"Good quality: {stats['good_quality']} ({stats['good_quality']/stats['total']*100:.1f}%)")
        print(f"Low quality: {stats['low_quality']} ({stats['low_quality']/stats['total']*100:.1f}%)")
        print(f"  - Too short: {stats['too_short']}")
        print(f"  - Mostly emoji: {stats['mostly_emoji']}")
        print(f"Average compression: {stats['avg_compression']:.1f}%")
        print(f"Average English ratio: {stats['avg_english_ratio']:.1f}%")
        print(f"\nOutput saved to: {output_file}")
    
    return stats


if __name__ == '__main__':
    # Example usage
    input_file = '/mnt/user-data/uploads/analisis_sentimen_comments_preprocessed.json'
    output_file = '/mnt/user-data/outputs/analisis_sentimen_comments_improved.json'
    
    # Process
    stats = process_dataset(
        input_file=input_file,
        output_file=output_file,
        remove_stopwords=False,  # Can enable if needed
        verbose=True
    )
