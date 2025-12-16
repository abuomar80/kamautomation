"""
Translation Helper Module for FOLIO Location System

This module provides reusable functions to create translations for FOLIO entities
(locations, libraries, institutions, campuses) via the FOLIO translation API.

Extracted from complete_translation_system to provide a clean interface for 
the location creation workflow.
"""

import requests
import uuid
import json
from typing import Tuple, Optional


def create_translation_for_entity(
    entity_id: str,
    english_name: str,
    arabic_name: str,
    entity_type: str,  # 'CAMPUS', 'INSTITUTION', 'LIBRARY', 'LOCATION'
    okapi: str,
    tenant: str,
    token: str
) -> Tuple[bool, Optional[str]]:
    """
    Create a translation for a FOLIO entity with English and Arabic values.
    
    Args:
        entity_id: UUID of the entity to create translation for
        english_name: English name of the entity
        arabic_name: Arabic translation of the entity name
        entity_type: Type of entity - 'CAMPUS', 'INSTITUTION', 'LIBRARY', or 'LOCATION'
        okapi: OKAPI base URL (e.g., 'https://api02-v1.ils.medad.com')
        tenant: Tenant ID
        token: Authentication token
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
        - (True, None) if translation created successfully
        - (True, None) if translation already exists (422 status)
        - (False, error_message) if creation failed
    
    Example:
        success, error = create_translation_for_entity(
            entity_id="123e4567-e89b-12d3-a456-426614174000",
            english_name="Main Library",
            arabic_name="المكتبة الرئيسية",
            entity_type="LIBRARY",
            okapi="https://api02-v1.ils.medad.com",
            tenant="mytenant",
            token="eyJhbGc..."
        )
    """
    # Validate entity type
    valid_types = ['CAMPUS', 'INSTITUTION', 'LIBRARY', 'LOCATION']
    if entity_type not in valid_types:
        return False, f"Invalid entity type '{entity_type}'. Must be one of: {', '.join(valid_types)}"
    
    # Validate required fields
    if not entity_id or not english_name or not arabic_name:
        return False, "entity_id, english_name, and arabic_name are required"
    
    # Generate unique translation ID
    translation_id = str(uuid.uuid4())
    
    # Create translation payload
    translation_data = {
        "id": translation_id,
        "entityId": entity_id,
        "type": entity_type,
        "translatedFields": [
            {
                "field": "name",
                "translations": [
                    {
                        "lang": "en",
                        "value": english_name
                    },
                    {
                        "lang": "ar",
                        "value": arabic_name
                    }
                ]
            }
        ]
    }
    
    # Set up request headers
    headers = {
        "x-okapi-tenant": tenant,
        "x-okapi-token": token,
        "Content-Type": "application/json"
    }
    
    url = f"{okapi}/inventory-storage/translations"
    
    try:
        response = requests.post(url, json=translation_data, headers=headers)
        
        # 201 = Created successfully
        if response.status_code == 201:
            return True, None
        
        # 422 = Already exists (which is OK, we consider this success)
        elif response.status_code == 422:
            return True, None
        
        # Other error status codes
        else:
            try:
                error_data = response.json()
                if 'errors' in error_data and len(error_data['errors']) > 0:
                    error_msg = error_data['errors'][0].get('message', 'Unknown error')
                    return False, f"Translation API error: {error_msg}"
            except:
                pass
            return False, f"Failed to create translation (HTTP {response.status_code})"
            
    except requests.exceptions.RequestException as e:
        return False, f"Network error creating translation: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error creating translation: {str(e)}"


def check_translation_exists(
    entity_id: str,
    okapi: str,
    tenant: str,
    token: str
) -> Tuple[bool, Optional[dict]]:
    """
    Check if a translation already exists for an entity.
    
    Args:
        entity_id: UUID of the entity
        okapi: OKAPI base URL
        tenant: Tenant ID
        token: Authentication token
        
    Returns:
        Tuple of (exists: bool, translation_data: Optional[dict])
    """
    headers = {
        "x-okapi-tenant": tenant,
        "x-okapi-token": token
    }
    
    url = f"{okapi}/inventory-storage/translations"
    params = {'query': f'entityId=={entity_id}', 'limit': 1}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            translations = data.get('entityTranslations', [])
            if translations:
                return True, translations[0]
        
        return False, None
        
    except Exception:
        return False, None
