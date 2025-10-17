import language_tool_python
from typing import List, Dict, Optional
from app.core.config import settings
import re


class SpellCheckerService:
    """Service for checking spelling and grammar in Ukrainian text."""
    
    def __init__(self):
        self.tool = None
        self.enabled = settings.LANGUAGETOOL_ENABLED
        
    def __enter__(self):
        if self.enabled:
            try:
                # Initialize LanguageTool for Ukrainian
                self.tool = language_tool_python.LanguageTool('uk-UA')
                print("✅ LanguageTool initialized successfully")
            except Exception as e:
                print(f"⚠️ LanguageTool initialization failed: {e}")
                print("   Continuing without spell checking...")
                self.enabled = False
                self.tool = None
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.tool:
            self.tool.close()
    
    def clean_text(self, text: str) -> str:
        """Clean text from HTML entities and extra whitespace."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def check_text(self, text: str, whitelist_words: Optional[List[str]] = None) -> List[Dict]:
        """
        Check text for spelling and grammar errors.
        
        Args:
            text: Text to check
            whitelist_words: List of words to ignore
            
        Returns:
            List of error dictionaries
        """
        if not self.enabled or not self.tool:
            return []
        
        # Clean text
        text = self.clean_text(text)
        
        if not text or len(text) < 3:
            return []
        
        # Split into chunks if text is too long (LanguageTool has limits)
        max_length = 20000
        if len(text) > max_length:
            chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        else:
            chunks = [text]
        
        errors = []
        offset = 0
        
        whitelist_words = whitelist_words or []
        whitelist_lower = [w.lower() for w in whitelist_words]
        
        for chunk in chunks:
            try:
                matches = self.tool.check(chunk)
                
                for match in matches:
                    # Skip if word is in whitelist
                    if match.context.lower() in whitelist_lower:
                        continue
                    
                    # Get context (50 chars before and after)
                    start = max(0, match.offset - 50)
                    end = min(len(chunk), match.offset + match.errorLength + 50)
                    context = chunk[start:end]
                    
                    error = {
                        'message': match.message,
                        'context': context,
                        'suggestion': ', '.join(match.replacements[:3]) if match.replacements else None,
                        'offset': offset + match.offset,
                        'length': match.errorLength,
                        'rule_id': match.ruleId,
                        'category': match.category,
                    }
                    errors.append(error)
                    
            except Exception as e:
                print(f"Error checking chunk: {e}")
                continue
            
            offset += len(chunk)
        
        return errors
    
    def check_page(self, text_content: str, whitelist_words: Optional[List[str]] = None) -> List[Dict]:
        """
        Check a page's text content for errors.
        
        Args:
            text_content: Extracted text from HTML page
            whitelist_words: Words to ignore (e.g., brand names, technical terms)
            
        Returns:
            List of spelling/grammar errors
        """
        return self.check_text(text_content, whitelist_words)

