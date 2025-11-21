import streamlit as st
from functools import wraps as _wraps


def _track_forbidden_keys(element):
    if "__track_forbidden_keys__" not in element.__dict__:
        element.__dict__["__track_forbidden_keys__"] = True

        @_wraps(element)
        def wrapper_element(*args, **kwargs):
            if "key" in kwargs:
                # Initialize _forbidden_keys if it doesn't exist
                if "_forbidden_keys" not in st.session_state:
                    st.session_state._forbidden_keys = set()
                st.session_state._forbidden_keys.add(kwargs["key"])
            return element(*args, **kwargs)

        return wrapper_element

    return element


def legacy_session_state():
    # Initialize forbidden keys set.
    if "_forbidden_keys" not in st.session_state:
        st.session_state._forbidden_keys = set()
    
    # Add navigation-related keys to forbidden set (created by st.navigation/widgets)
    # These are widget-bound and cannot be modified directly
    navigation_keys = {'init', 'current_page', '_page_id'}
    st.session_state._forbidden_keys.update(navigation_keys)

    # Self-assign session state items that are not in our forbidden set.
    # This actually translates widget state items to user-defined session
    # state items internally, which makes widget states persistent.
    # Skip widget-bound keys to avoid StreamlitAPIException
    for key, value in list(st.session_state.items()):
        # Skip forbidden keys (including navigation keys) and internal keys
        if key in st.session_state._forbidden_keys:
            continue
        if key.startswith('_'):
            continue
        
        # Try to assign - if it fails, the key is widget-bound
        try:
            # This assignment will fail if the key is widget-bound
            st.session_state[key] = value
        except Exception:
            # Key is widget-bound - add to forbidden set and skip
            st.session_state._forbidden_keys.add(key)
            continue

    # We don't want to self-assign keys from the following widgets
    # to avoid a Streamlit API exception.
    # So we wrap them and save any used key in our _forbidden_keys set.
    st.button = _track_forbidden_keys(st.button)
    st.download_button = _track_forbidden_keys(st.download_button)
    st.file_uploader = _track_forbidden_keys(st.file_uploader)
    st.form = _track_forbidden_keys(st.form)

    # Don't clear navigation keys - they should always be forbidden
    # Only clear widget keys that are no longer in use (not navigation keys)
    navigation_keys_to_keep = {'init', 'current_page', '_page_id'}
    current_forbidden = st.session_state._forbidden_keys.copy()
    st.session_state._forbidden_keys.clear()
    # Restore navigation keys
    st.session_state._forbidden_keys.update(navigation_keys_to_keep)
    # Keep any other keys that were marked as forbidden (widget keys)
    for key in current_forbidden:
        if key not in navigation_keys_to_keep:
            # Only keep if it's still a widget key (starts with known patterns)
            if not key.startswith('_') or key == '_forbidden_keys':
                continue
            # Keep widget-bound keys that were detected
            st.session_state._forbidden_keys.add(key)