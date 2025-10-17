import re
from typing import List, Dict, Optional


class AddressValidatorService:
    """Service for validating Ukrainian address formats."""
    
    # Correct address patterns
    CORRECT_PATTERNS = [
        # м. [місто], вул. [вулиця], [номер]
        r'м\.\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-]+,\s+вул\.\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-\s]+,\s+\d+',
        # м. [місто], пров. [провулок], [номер]
        r'м\.\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-]+,\s+пров\.\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-\s]+,\s+\d+',
        # м. [місто], проспект [назва], [номер]
        r'м\.\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-]+,\s+проспект\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-\s]+,\s+\d+',
        # м. [місто], бульвар [назва], [номер]
        r'м\.\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-]+,\s+бульвар\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-\s]+,\s+\d+',
        # With building/apartment: м. [місто], вул. [вулиця], [номер], кв. [номер]
        r'м\.\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-]+,\s+вул\.\s+[А-ЯІЇЄҐ][а-яіїєґ\'\-\s]+,\s+\d+,\s+кв\.\s+\d+',
    ]
    
    # Patterns to detect potential addresses (even incorrectly formatted)
    DETECTION_PATTERNS = [
        # Any text that looks like it might be an address
        r'[мМ]\.?\s*[А-ЯІЇЄҐ][а-яіїєґ\'\-]+[\s,]+(?:вул|пров|проспект|бульвар)\.?\s*[А-ЯІЇЄҐ][а-яіїєґ\'\-\s]+[\s,]+\d+',
        r'(?:місто|м)[\s\.]*[А-ЯІЇЄҐ][а-яіїєґ\'\-]+',
        r'(?:вулиця|вул)[\s\.]*[А-ЯІЇЄҐ][а-яіїєґ\'\-\s]+[\s,]+\d+',
    ]
    
    def __init__(self):
        self.correct_compiled = [re.compile(p, re.UNICODE) for p in self.CORRECT_PATTERNS]
        self.detection_compiled = [re.compile(p, re.UNICODE) for p in self.DETECTION_PATTERNS]
    
    def is_correct_format(self, address: str) -> bool:
        """Check if address matches correct format."""
        address = address.strip()
        return any(pattern.fullmatch(address) for pattern in self.correct_compiled)
    
    def find_addresses(self, text: str) -> List[Dict]:
        """Find all potential addresses in text."""
        found_addresses = []
        
        for pattern in self.detection_compiled:
            matches = pattern.finditer(text)
            for match in matches:
                address_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
                # Get context (100 chars before and after)
                context_start = max(0, start_pos - 100)
                context_end = min(len(text), end_pos + 100)
                context = text[context_start:context_end]
                
                found_addresses.append({
                    'address': address_text,
                    'context': context,
                    'position': start_pos,
                })
        
        return found_addresses
    
    def validate_text(self, text: str) -> List[Dict]:
        """
        Find and validate addresses in text.
        
        Returns list of errors for incorrectly formatted addresses.
        """
        errors = []
        addresses = self.find_addresses(text)
        
        for addr_data in addresses:
            address = addr_data['address']
            
            if not self.is_correct_format(address):
                # Determine what's wrong
                issues = []
                
                # Check for missing "м."
                if re.search(r'(?:^|[^м])(?:місто|М[А-ЯІЇЄҐ])', address):
                    issues.append('Відсутнє скорочення "м." перед назвою міста')
                
                # Check for missing "вул.", "пров." etc.
                if re.search(r'(?:вулиця|провулок)\s+[А-ЯІЇЄҐ]', address):
                    issues.append('Використовуйте скорочення "вул." або "пров." замість повної назви')
                
                # Check for missing comma
                if ',' not in address:
                    issues.append('Відсутні коми між частинами адреси')
                
                # Check for missing spaces after abbreviations
                if re.search(r'[мвп]\.[А-ЯІЇЄҐ]', address):
                    issues.append('Відсутній пробіл після скорочення')
                
                suggestion = self.suggest_correction(address)
                
                error = {
                    'address': address,
                    'context': addr_data['context'],
                    'issues': issues,
                    'suggestion': suggestion,
                    'message': f"Неправильний формат адреси. {' '.join(issues) if issues else 'Використовуйте формат: м. Місто, вул. Назва, 123'}",
                }
                errors.append(error)
        
        return errors
    
    def suggest_correction(self, address: str) -> Optional[str]:
        """Suggest a correction for incorrectly formatted address."""
        # Try to auto-fix common issues
        corrected = address
        
        # Add "м." if missing
        corrected = re.sub(r'^([А-ЯІЇЄҐ][а-яіїєґ\'\-]+)[\s,]+', r'м. \1, ', corrected)
        corrected = re.sub(r'місто\s+', 'м. ', corrected, flags=re.IGNORECASE)
        
        # Replace full words with abbreviations
        corrected = re.sub(r'вулиця\s+', 'вул. ', corrected, flags=re.IGNORECASE)
        corrected = re.sub(r'провулок\s+', 'пров. ', corrected, flags=re.IGNORECASE)
        
        # Fix spacing after abbreviations
        corrected = re.sub(r'([мвп])\.([А-ЯІЇЄҐ])', r'\1. \2', corrected)
        
        # Ensure commas between parts
        corrected = re.sub(r'([а-яіїєґ])\s+(вул|пров)', r'\1, \2', corrected)
        corrected = re.sub(r'([а-яіїєґ\.])\s+(\d)', r'\1, \2', corrected)
        
        return corrected if corrected != address else None

