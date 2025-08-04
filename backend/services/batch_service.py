from datetime import datetime, date
from typing import Dict, List, Optional, Any
import re

class BatchService:
    """
    Batch Service - Assists with metadata validation and status updates
    """
    
    # Valid batch statuses
    VALID_STATUSES = ['pending', 'inspected', 'approved', 'rejected']
    
    # Status transition rules
    STATUS_TRANSITIONS = {
        'pending': ['inspected'],
        'inspected': ['approved', 'rejected'],
        'approved': [],  # Final status
        'rejected': []   # Final status
    }
    
    # Required fields
    REQUIRED_FIELDS = ['productName', 'origin', 'quantity', 'unit']
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Metadata validation
        
        Args:
            metadata: Batch metadata
            
        Returns:
            Dict: Validation result {'valid': bool, 'errors': List[str], 'warnings': List[str]}
        """
        errors = []
        warnings = []
        
        # 1. Check required fields
        missing_fields = BatchService._check_required_fields(metadata)
        if missing_fields:
            errors.extend([f"Missing required field: {field}" for field in missing_fields])
        
        # 2. Check field formats
        format_errors = BatchService._validate_field_formats(metadata)
        errors.extend(format_errors)
        
        # 3. Check business rules
        business_warnings = BatchService._validate_business_rules(metadata)
        warnings.extend(business_warnings)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def _check_required_fields(metadata: Dict[str, Any]) -> List[str]:
        """Check required fields"""
        missing_fields = []
        
        for field in BatchService.REQUIRED_FIELDS:
            if not metadata.get(field) or str(metadata.get(field)).strip() == '':
                missing_fields.append(field)
        
        return missing_fields
    
    @staticmethod
    def _validate_field_formats(metadata: Dict[str, Any]) -> List[str]:
        """Validate field formats"""
        errors = []
        
        # Validate product name
        product_name = metadata.get('productName', '')
        if product_name and len(product_name) > 100:
            errors.append("productName too long (max 100 characters)")
        
        # Validate origin
        origin = metadata.get('origin', '')
        if origin and len(origin) > 100:
            errors.append("origin too long (max 100 characters)")
        
        # Validate quantity
        quantity = metadata.get('quantity')
        if quantity and not isinstance(quantity, str):
            errors.append("quantity must be string")
        
        # Validate unit
        unit = metadata.get('unit', '')
        if unit and len(unit) > 20:
            errors.append("unit too long (max 20 characters)")
        
        # Validate total weight
        total_weight = metadata.get('totalWeightKg')
        if total_weight is not None:
            try:
                weight = int(total_weight)
                if weight < 0:
                    errors.append("totalWeightKg must be positive")
                elif weight > 1000000:  # 1000 ton limit
                    errors.append("totalWeightKg too large (max 1,000,000 kg)")
            except (ValueError, TypeError):
                errors.append("totalWeightKg must be integer")
        
        # Validate date format
        errors.extend(BatchService._validate_dates(metadata))
        
        # Validate boolean values
        errors.extend(BatchService._validate_booleans(metadata))
        
        return errors
    
    @staticmethod
    def _validate_dates(metadata: Dict[str, Any]) -> List[str]:
        """Validate date fields"""
        errors = []
        date_fields = ['harvestDate', 'expiryDate']
        
        for field in date_fields:
            date_str = metadata.get(field)
            if date_str:
                try:
                    # Validate date format YYYY-MM-DD
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                        errors.append(f"{field} must be in YYYY-MM-DD format")
                        continue
                    
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Validate date reasonableness
                    if field == 'harvestDate':
                        # Harvest date cannot be in the future
                        if parsed_date > date.today():
                            errors.append("harvestDate cannot be in the future")
                        # Harvest date cannot be too old
                        elif parsed_date < date(2000, 1, 1):
                            errors.append("harvestDate too old (before 2000)")
                    
                    elif field == 'expiryDate':
                        # Expiry date must be in the future
                        if parsed_date <= date.today():
                            errors.append("expiryDate must be in the future")
                
                except ValueError:
                    errors.append(f"Invalid date format for {field}")
        
        # Validate date logical relationships
        harvest_date = metadata.get('harvestDate')
        expiry_date = metadata.get('expiryDate')
        if harvest_date and expiry_date:
            try:
                harvest = datetime.strptime(harvest_date, '%Y-%m-%d').date()
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                if expiry <= harvest:
                    errors.append("expiryDate must be after harvestDate")
            except ValueError:
                pass  # Format errors already checked above
        
        return errors
    
    @staticmethod
    def _validate_booleans(metadata: Dict[str, Any]) -> List[str]:
        """Validate boolean fields"""
        errors = []
        boolean_fields = ['organic', 'import']
        
        for field in boolean_fields:
            value = metadata.get(field)
            if value is not None and not isinstance(value, bool):
                errors.append(f"{field} must be boolean (true/false)")
        
        return errors
    
    @staticmethod
    def _validate_business_rules(metadata: Dict[str, Any]) -> List[str]:
        """Validate business rules (returns warnings)"""
        warnings = []
        
        # Check shelf life reasonableness
        harvest_date = metadata.get('harvestDate')
        expiry_date = metadata.get('expiryDate')
        if harvest_date and expiry_date:
            try:
                harvest = datetime.strptime(harvest_date, '%Y-%m-%d').date()
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                shelf_life = (expiry - harvest).days
                
                if shelf_life > 365:
                    warnings.append("Shelf life over 1 year, please verify")
                elif shelf_life < 1:
                    warnings.append("Very short shelf life, please verify")
            except ValueError:
                pass
        
        # Check consistency between weight and quantity
        quantity = metadata.get('quantity')
        total_weight = metadata.get('totalWeightKg')
        unit = metadata.get('unit', '').lower()
        
        if quantity and total_weight and unit == 'kg':
            try:
                qty_num = float(quantity)
                if abs(qty_num - total_weight) > total_weight * 0.1:  # 10% tolerance
                    warnings.append("Quantity and totalWeightKg seem inconsistent")
            except ValueError:
                pass
        
        return warnings
    
    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> Dict[str, Any]:
        """
        Validate if status transition is legal
        
        Args:
            current_status: Current status
            new_status: Target status
            
        Returns:
            Dict: {'valid': bool, 'error': str}
        """
        # Check if status is valid
        if new_status not in BatchService.VALID_STATUSES:
            return {
                'valid': False,
                'error': f"Invalid status: {new_status}. Valid statuses: {', '.join(BatchService.VALID_STATUSES)}"
            }
        
        # Check if transition is legal
        allowed_transitions = BatchService.STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_transitions:
            return {
                'valid': False,
                'error': f"Cannot transition from {current_status} to {new_status}. Allowed: {', '.join(allowed_transitions)}"
            }
        
        return {'valid': True, 'error': None}
    
    @staticmethod
    def get_next_batch_number() -> str:
        """
        Generate next batch number
        
        Returns:
            str: Batch number format: BATCH-YYYYMMDDHHMMSS
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"BATCH-{timestamp}"
    
    @staticmethod
    def calculate_batch_summary(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate batch summary information
        
        Args:
            metadata: Batch metadata
            
        Returns:
            Dict: Summary information
        """
        summary = {
            'product_name': metadata.get('productName', ''),
            'origin': metadata.get('origin', ''),
            'quantity_with_unit': f"{metadata.get('quantity', '')} {metadata.get('unit', '')}",
            'is_organic': metadata.get('organic', False),
            'is_import': metadata.get('import', False),
            'shelf_life_days': None
        }
        
        # Calculate shelf life in days
        harvest_date = metadata.get('harvestDate')
        expiry_date = metadata.get('expiryDate')
        if harvest_date and expiry_date:
            try:
                harvest = datetime.strptime(harvest_date, '%Y-%m-%d').date()
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                summary['shelf_life_days'] = (expiry - harvest).days
            except ValueError:
                pass
        
        return summary
    
    @staticmethod
    def get_status_display_info(status: str) -> Dict[str, str]:
        """
        Get status display information
        
        Args:
            status: Batch status
            
        Returns:
            Dict: Display information {'status': str, 'display': str, 'color': str}
        """
        status_info = {
            'pending': {'display': 'Pending Inspection', 'color': 'orange'},
            'inspected': {'display': 'Inspected', 'color': 'blue'},
            'approved': {'display': 'Approved', 'color': 'green'},
            'rejected': {'display': 'Rejected', 'color': 'red'}
        }
        
        info = status_info.get(status, {'display': status, 'color': 'gray'})
        return {
            'status': status,
            'display': info['display'],
            'color': info['color']
        }
