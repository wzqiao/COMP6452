from datetime import datetime, date
from typing import Dict, List, Optional, Any
import re

class BatchService:
    """
    批次服务 - 辅助元数据校验、状态更新
    """
    
    # 有效的批次状态
    VALID_STATUSES = ['pending', 'inspected', 'approved', 'rejected']
    
    # 状态转换规则
    STATUS_TRANSITIONS = {
        'pending': ['inspected'],
        'inspected': ['approved', 'rejected'],
        'approved': [],  # 最终状态
        'rejected': []   # 最终状态
    }
    
    # 必填字段
    REQUIRED_FIELDS = ['productName', 'origin', 'quantity', 'unit']
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        元数据校验
        
        Args:
            metadata: 批次元数据
            
        Returns:
            Dict: 校验结果 {'valid': bool, 'errors': List[str], 'warnings': List[str]}
        """
        errors = []
        warnings = []
        
        # 1. 检查必填字段
        missing_fields = BatchService._check_required_fields(metadata)
        if missing_fields:
            errors.extend([f"Missing required field: {field}" for field in missing_fields])
        
        # 2. 检查字段格式
        format_errors = BatchService._validate_field_formats(metadata)
        errors.extend(format_errors)
        
        # 3. 检查业务规则
        business_warnings = BatchService._validate_business_rules(metadata)
        warnings.extend(business_warnings)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def _check_required_fields(metadata: Dict[str, Any]) -> List[str]:
        """检查必填字段"""
        missing_fields = []
        
        for field in BatchService.REQUIRED_FIELDS:
            if not metadata.get(field) or str(metadata.get(field)).strip() == '':
                missing_fields.append(field)
        
        return missing_fields
    
    @staticmethod
    def _validate_field_formats(metadata: Dict[str, Any]) -> List[str]:
        """验证字段格式"""
        errors = []
        
        # 验证产品名称
        product_name = metadata.get('productName', '')
        if product_name and len(product_name) > 100:
            errors.append("productName too long (max 100 characters)")
        
        # 验证产地
        origin = metadata.get('origin', '')
        if origin and len(origin) > 100:
            errors.append("origin too long (max 100 characters)")
        
        # 验证数量
        quantity = metadata.get('quantity')
        if quantity and not isinstance(quantity, str):
            errors.append("quantity must be string")
        
        # 验证单位
        unit = metadata.get('unit', '')
        if unit and len(unit) > 20:
            errors.append("unit too long (max 20 characters)")
        
        # 验证总重量
        total_weight = metadata.get('totalWeightKg')
        if total_weight is not None:
            try:
                weight = int(total_weight)
                if weight < 0:
                    errors.append("totalWeightKg must be positive")
                elif weight > 1000000:  # 1000吨限制
                    errors.append("totalWeightKg too large (max 1,000,000 kg)")
            except (ValueError, TypeError):
                errors.append("totalWeightKg must be integer")
        
        # 验证日期格式
        errors.extend(BatchService._validate_dates(metadata))
        
        # 验证布尔值
        errors.extend(BatchService._validate_booleans(metadata))
        
        return errors
    
    @staticmethod
    def _validate_dates(metadata: Dict[str, Any]) -> List[str]:
        """验证日期字段"""
        errors = []
        date_fields = ['harvestDate', 'expiryDate']
        
        for field in date_fields:
            date_str = metadata.get(field)
            if date_str:
                try:
                    # 验证日期格式 YYYY-MM-DD
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                        errors.append(f"{field} must be in YYYY-MM-DD format")
                        continue
                    
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # 验证日期合理性
                    if field == 'harvestDate':
                        # 收获日期不能是未来
                        if parsed_date > date.today():
                            errors.append("harvestDate cannot be in the future")
                        # 收获日期不能太久远
                        elif parsed_date < date(2000, 1, 1):
                            errors.append("harvestDate too old (before 2000)")
                    
                    elif field == 'expiryDate':
                        # 过期日期必须在未来
                        if parsed_date <= date.today():
                            errors.append("expiryDate must be in the future")
                
                except ValueError:
                    errors.append(f"Invalid date format for {field}")
        
        # 验证日期逻辑关系
        harvest_date = metadata.get('harvestDate')
        expiry_date = metadata.get('expiryDate')
        if harvest_date and expiry_date:
            try:
                harvest = datetime.strptime(harvest_date, '%Y-%m-%d').date()
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                if expiry <= harvest:
                    errors.append("expiryDate must be after harvestDate")
            except ValueError:
                pass  # 已经在上面检查过格式错误
        
        return errors
    
    @staticmethod
    def _validate_booleans(metadata: Dict[str, Any]) -> List[str]:
        """验证布尔字段"""
        errors = []
        boolean_fields = ['organic', 'import']
        
        for field in boolean_fields:
            value = metadata.get(field)
            if value is not None and not isinstance(value, bool):
                errors.append(f"{field} must be boolean (true/false)")
        
        return errors
    
    @staticmethod
    def _validate_business_rules(metadata: Dict[str, Any]) -> List[str]:
        """验证业务规则（返回警告）"""
        warnings = []
        
        # 检查保质期合理性
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
        
        # 检查重量与数量的合理性
        quantity = metadata.get('quantity')
        total_weight = metadata.get('totalWeightKg')
        unit = metadata.get('unit', '').lower()
        
        if quantity and total_weight and unit == 'kg':
            try:
                qty_num = float(quantity)
                if abs(qty_num - total_weight) > total_weight * 0.1:  # 10%误差
                    warnings.append("Quantity and totalWeightKg seem inconsistent")
            except ValueError:
                pass
        
        return warnings
    
    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> Dict[str, Any]:
        """
        验证状态转换是否合法
        
        Args:
            current_status: 当前状态
            new_status: 目标状态
            
        Returns:
            Dict: {'valid': bool, 'error': str}
        """
        # 检查状态是否有效
        if new_status not in BatchService.VALID_STATUSES:
            return {
                'valid': False,
                'error': f"Invalid status: {new_status}. Valid statuses: {', '.join(BatchService.VALID_STATUSES)}"
            }
        
        # 检查转换是否合法
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
        生成下一个批次编号
        
        Returns:
            str: 批次编号 格式: BATCH-YYYYMMDDHHMMSS
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"BATCH-{timestamp}"
    
    @staticmethod
    def calculate_batch_summary(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算批次摘要信息
        
        Args:
            metadata: 批次元数据
            
        Returns:
            Dict: 摘要信息
        """
        summary = {
            'product_name': metadata.get('productName', ''),
            'origin': metadata.get('origin', ''),
            'quantity_with_unit': f"{metadata.get('quantity', '')} {metadata.get('unit', '')}",
            'is_organic': metadata.get('organic', False),
            'is_import': metadata.get('import', False),
            'shelf_life_days': None
        }
        
        # 计算保质期天数
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
        获取状态的显示信息
        
        Args:
            status: 批次状态
            
        Returns:
            Dict: 显示信息 {'status': str, 'display': str, 'color': str}
        """
        status_info = {
            'pending': {'display': '待检验', 'color': 'orange'},
            'inspected': {'display': '已检验', 'color': 'blue'},
            'approved': {'display': '已批准', 'color': 'green'},
            'rejected': {'display': '已拒绝', 'color': 'red'}
        }
        
        info = status_info.get(status, {'display': status, 'color': 'gray'})
        return {
            'status': status,
            'display': info['display'],
            'color': info['color']
        }
