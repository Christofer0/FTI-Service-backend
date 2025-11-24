# controllers/fakultas_controller.py (Additional controller for master data)
from flask import Blueprint,jsonify
from app.services.fakultas_service import FakultasService
from schemas.fakultas_schema import FakultasSchema, ProgramStudiSchema
from utils.jwt_utils import role_required,jwt_required
from utils.response_utils import success_response, error_response

fakultas_bp = Blueprint('fakultas', __name__)
fakultas_service = FakultasService()
program_studi_schema = ProgramStudiSchema(many=True)


@fakultas_bp.route('/', methods=['GET'])
# @jwt_required()
def get_fakultas_list():
    """Get list of fakultas"""
    try:
        program_studi_list = fakultas_service.get_all_program_studi()
        print(program_studi_list)
        return success_response("Fakultas list retrieved", program_studi_list)
    except Exception as e:
        return error_response("Failed to get fakultas list", str(e), 500)
