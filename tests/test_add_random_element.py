"""Tests for add_random_element functionality"""
import pandas as pd
import pytest
from app.model.modular import Modular
from app.model.solution import Solution
from tests.test_modular import supply_df


def test_add_random_element_restores_deleted(supply_df):
    """add_random_element should restore a previously deleted element"""
    req = pd.DataFrame([
        {"code": "r", "800": "36", "400": "20", "200": "15"},
    ])
    modular = Modular(supply_df)
    s = Solution(modular, req)
    
    original_count = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    
    # Delete an element
    s.delete_random_element()
    after_delete = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    assert after_delete == original_count - 1
    
    # Add it back
    s.add_random_element()
    after_add = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    assert after_add == original_count


def test_add_random_element_raises_if_nothing_deleted(supply_df):
    """add_random_element should raise error if no linecards are deleted"""
    req = pd.DataFrame([
        {"code": "r", "800": "36", "400": "20", "200": "15"},
    ])
    modular = Modular(supply_df)
    s = Solution(modular, req)
    
    # Try to add without deleting anything
    with pytest.raises(ValueError, match="No deleted linecards to re-add"):
        s.add_random_element()


def test_original_steps_preserved(supply_df):
    """original_steps should remain unchanged after deletions and additions"""
    req = pd.DataFrame([
        {"code": "r", "800": "36", "400": "20", "200": "15"},
    ])
    modular = Modular(supply_df)
    s = Solution(modular, req)
    
    original_original = [sublist.copy() for sublist in s.original_steps]
    
    # Delete and add multiple times
    for _ in range(5):
        s.delete_random_element()
        s.add_random_element()
    
    # original_steps should still be the same
    assert len(s.original_steps) == len(original_original)
    for orig, current_orig in zip(original_original, s.original_steps):
        assert len(orig) == len(current_orig)


def test_delete_then_add_multiple_times(supply_df):
    """should be able to delete and add elements multiple times"""
    req = pd.DataFrame([
        {"code": "r", "800": "36", "400": "20", "200": "15"},
    ])
    modular = Modular(supply_df)
    s = Solution(modular, req)
    
    original_count = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    
    # Delete multiple elements
    for _ in range(3):
        s.delete_random_element()
    
    deleted_count = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    assert deleted_count == original_count - 3
    
    # Add them back one by one
    for _ in range(3):
        s.add_random_element()
    
    restored_count = sum(len(sublist) for sublist in s.steps if isinstance(sublist, list))
    assert restored_count == original_count


def test_add_restores_exact_element(supply_df):
    """add_random_element should restore an element that was actually deleted"""
    req = pd.DataFrame([
        {"code": "r", "800": "36", "400": "20", "200": "15"},
    ])
    modular = Modular(supply_df)
    s = Solution(modular, req)
    
    # Find what was deleted
    before_delete = [set(sublist) if isinstance(sublist, list) else sublist 
                     for sublist in s.steps]
    
    s.delete_random_element()
    
    after_delete = [set(sublist) if isinstance(sublist, list) else sublist 
                    for sublist in s.steps]
    
    # Find what was deleted
    deleted_items = []
    for i, (before, after) in enumerate(zip(before_delete, after_delete)):
        if isinstance(before, set) and isinstance(after, set):
            deleted = before - after
            if deleted:
                deleted_items.extend(deleted)
    
    assert len(deleted_items) == 1, "Should have deleted exactly one item"
    
    s.add_random_element()
    
    # Check that the deleted item is restored
    after_add = [set(sublist) if isinstance(sublist, list) else sublist 
                 for sublist in s.steps]
    
    restored_items = []
    for i, (after_del, after_ad) in enumerate(zip(after_delete, after_add)):
        if isinstance(after_del, set) and isinstance(after_ad, set):
            restored = after_ad - after_del
            if restored:
                restored_items.extend(restored)
    
    assert len(restored_items) == 1
    assert restored_items[0] in deleted_items


