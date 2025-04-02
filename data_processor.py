import pandas as pd
import re
from typing import List, Dict, Any

class DataProcessor:
    """Class for processing CSV data and extracting keywords"""
    
    def extract_keywords(self, 
                         df: pd.DataFrame, 
                         name_col: str, 
                         owner_col: str,
                         min_keyword_length: int = 3) -> List[str]:
        """
        Extract keywords from the specified columns in the dataframe
        
        Args:
            df: The pandas DataFrame containing the data
            name_col: Column name for names (plant or vessel names)
            owner_col: Column name for owners
            min_keyword_length: Minimum length for a keyword to be included
            
        Returns:
            List of unique keywords for searching
        """
        keywords = set()
        
        # Process name column
        if name_col in df.columns:
            name_values = df[name_col].dropna().astype(str).tolist()
            for name in name_values:
                # Clean and process the name
                processed_name = self._clean_text(name)
                if processed_name and len(processed_name) >= min_keyword_length:
                    keywords.add(processed_name)
                
                # Also add parts of compound names (e.g., "Pacific Harvester" -> "Pacific", "Harvester")
                parts = processed_name.split()
                for part in parts:
                    if len(part) >= min_keyword_length and self._is_valid_keyword(part):
                        keywords.add(part)
        
        # Process owner column
        if owner_col in df.columns:
            owner_values = df[owner_col].dropna().astype(str).tolist()
            for owner in owner_values:
                # Clean and process the owner name
                processed_owner = self._clean_text(owner)
                if processed_owner and len(processed_owner) >= min_keyword_length:
                    keywords.add(processed_owner)
                
                # Add parts of compound owner names
                parts = processed_owner.split()
                for part in parts:
                    if len(part) >= min_keyword_length and self._is_valid_keyword(part):
                        keywords.add(part)
        
        # Convert set to list and sort
        keyword_list = sorted(list(keywords))
        
        # Remove very common words that might create false positives
        filtered_keywords = [k for k in keyword_list if not self._is_common_word(k)]
        
        return filtered_keywords
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing special characters and normalizing"""
        if not isinstance(text, str):
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)  # Replace special chars with space
        text = re.sub(r'\s+', ' ', text)      # Replace multiple spaces with single space
        
        return text.strip()
    
    def _is_valid_keyword(self, keyword: str) -> bool:
        """
        Check if keyword is valid for searching
        Excludes numbers-only and single-letter keywords
        """
        # Skip if it's just numbers
        if keyword.isdigit():
            return False
        
        # Skip if it's just a single letter
        if len(keyword) <= 1:
            return False
            
        return True
    
    def _is_common_word(self, word: str) -> bool:
        """Check if word is a common word that would create too many false positives"""
        common_words = {
            "the", "and", "fishing", "fish", "inc", "incorporated", "llc", 
            "company", "corp", "corporation", "industries", "seafood", "vessel",
            "boat", "ship", "processing", "plant", "factory", "international",
            "pacific", "atlantic", "north", "south", "east", "west", "marine",
            "sea", "ocean", "gulf", "bay", "harbor", "port", "enterprises", 
            "limited", "ltd", "holdings", "group"
        }
        
        return word.lower() in common_words
