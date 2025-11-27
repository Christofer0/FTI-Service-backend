from extensions import db
from app.models.user_model import User
from app.models.mahasiswa_model import Mahasiswa
from app.models.fakultas_model import Fakultas, ProgramStudi
from app.models.dosen_model import Dosen


class ViewRepositoryDosen:
    def get_all_dosen(self):
        data = (
            db.session.query(
                User.id.label("user_id"),
                User.nomor_induk,
                User.nama,
                User.email,
                User.no_hp,
                User.is_active,
                Dosen.gelar_depan,
                Dosen.gelar_belakang,
                db.func.concat(
                    db.func.coalesce(Dosen.gelar_depan + " ", ""),
                    User.nama,
                    db.func.coalesce(" " + Dosen.gelar_belakang, "")
                ).label("nama_lengkap"),
                Dosen.jabatan,
                Fakultas.id.label("fakultas_id"),
                Fakultas.nama_fakultas,
                Dosen.ttd_path,
                Dosen.signature_upload_at,
                User.created_at,
                User.last_login,
            )
            .join(Dosen, User.id == Dosen.user_id)
            .outerjoin(Fakultas, Dosen.fakultas_id == Fakultas.id)
            .filter(User.role == "dosen")
            .all()
        )

        return [row._asdict() for row in data]


class ViewRepositoryMahasiswa:
    def get_all_mahasiswa(self):
        data = (
            db.session.query(
                User.id.label("user_id"),
                User.nomor_induk,
                User.nama,
                User.email,
                User.no_hp,
                User.is_active,
                Mahasiswa.semester,
                Fakultas.id.label("fakultas_id"),
                Fakultas.nama_fakultas,
                ProgramStudi.id.label("program_studi_id"),
                ProgramStudi.nama_prodi,
                User.created_at,
                User.last_login,
            )
            .join(Mahasiswa, User.id == Mahasiswa.user_id)
            .join(Fakultas, Mahasiswa.fakultas_id == Fakultas.id)
            .join(ProgramStudi, Mahasiswa.program_studi_id == ProgramStudi.id)
            .filter(User.role == "mahasiswa")
            .all()
        )

        return [row._asdict() for row in data]
