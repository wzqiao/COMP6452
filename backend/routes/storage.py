from flask import Blueprint, request, jsonify
from services.s3_service import generate_presigned_url

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def get_upload_url():
    """Generate a pre-signed URL for S3 upload"""
    try:
        file_type = request.json.get('file_type')
        if not file_type:
            return jsonify({'error': 'file_type is required'}), 400
            
        # Generate pre-signed URL for upload
        presigned_url = generate_presigned_url(file_type)
        
        return jsonify({
            'upload_url': presigned_url,
            'message': 'Upload URL generated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
