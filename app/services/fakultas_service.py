from app.repositories.fakultas_repository import FakultasRepository

class FakultasService:
    def __init__(self):
        self.repo = FakultasRepository()

    def get_program_studi_by_fakultas(self, fakultas_id: int):
        fakultas = self.repo.get_with_program_studi(fakultas_id)
        if fakultas:
            return fakultas.to_dict()   # ✅ aman di jsonify
        return {}

    def get_all_program_studi(self):
        fakultas_list = self.repo.get_all_with_program_studi()
        return [f.to_dict() for f in fakultas_list]   # ✅ list of dict
