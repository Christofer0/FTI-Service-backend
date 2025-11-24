## ⚙️ Setup & Installation

### 1. Clone Repository From GITHUB

### 2. HAPUS FOLDER backend/migrations

### 3. MASUK cmd backend =>

    # 1. Initialize the database (run once)
        # flask db init

        # 2. Create initial migration
        # flask db migrate -m "Initial migration"

        # 3. Apply migration to database
        # flask db upgrade

### 4. Insert First Data

        # 1. First insert database the database (run once)
        # flask db revision -m "Insert First Data"
        # setelah muncul file di migrations masukkan
                def upgrade():
                    op.execute("""
                        INSERT INTO fakultas (nama_fakultas, created_at, updated_at)
                        VALUES ('Fakultas Teknologi Informasi', NOW(), NOW())
                    """)

                    op.execute("""
                        INSERT INTO program_studi (id,nama_prodi, fakultas_id, created_at, updated_at)
                        VALUES (67,'Teknik Informatika',
                        (SELECT id FROM fakultas WHERE nama_fakultas = 'Fakultas Teknologi Informasi'),
                        NOW(), NOW())
                    """)

                    # Tambahkan jenis permohonan dengan route_path
                    op.execute("""
                        INSERT INTO jenis_permohonan
                        (id, nama_jenis_permohonan, deskripsi, route_path, is_active, created_at, updated_at)
                        VALUES
                        (
                            1,
                            'Surat Permohonan TTD',
                            'Permohonan TTD untuk perizinan mahasiswa mengambil TTU1, TTU2, KP',
                            '/PermohonanTTD',
                            True,
                            NOW(),
                            NOW()
                        );
                    """)

                def downgrade():
                    # Hapus Program Studi dulu (foreign key ke fakultas)
                    op.execute("DELETE FROM program_studi WHERE id = 67")

                    # Hapus Fakultas
                    op.execute("DELETE FROM fakultas WHERE nama_fakultas = 'Fakultas Teknologi Informasi'")

                    #Hapus Jenis Permohonan
                    op.execute("DELETE FROM jenis_permohonan WHERE id = 1")
        # flask db upgrade

### 5.

        1. pendaftar pertama akan menjadi role = admin (namun belom benar2 berjalan untuk dashboardnya)
        2. pendaftar ke 2 bisa dosen / mahasiswa. tergantung. jika menggunakan email student maka role = mahasiswa jika email biasa menjadi dosen()
        3. bisa dicoba aplikasinya.

### 6. Drop tabel v_mahasiswa & v_dosen

        # 1. create view to database (run once)
            # flask db revision -m "create triggers view for users"
            # setelah muncul file di migrations baru, masukkan:

        def upgrade():
            op.execute("""
                DROP TABLE IF EXISTS v_dosen;
                DROP VIEW IF EXISTS v_dosen;
                DROP TABLE IF EXISTS v_mahasiswa;
                DROP VIEW IF EXISTS v_mahasiswa;
            """)

        def downgrade():
            pass

        #jangan lupa "flask db upgrade"

### 7. Create View & Triggers

        # 1. create view to database (run once)
        # flask db revision -m "create triggers view for users"
        # setelah muncul file di migrations baru, masukkan:

        def upgrade():
            op.execute (
            """
                -- VIEW Mahasiswa
                CREATE VIEW v_mahasiswa AS
                SELECT
                    u.id as user_id,
                    u.nomor_induk,
                    u.nama,
                    u.email,
                    u.no_hp,
                    u.is_active,
                    m.semester,
                    f.id as fakultas_id,
                    f.nama_fakultas,
                    ps.id as program_studi_id,
                    ps.nama_prodi,
                    u.created_at,
                    u.last_login
                FROM users u
                JOIN mahasiswa m ON u.id = m.user_id
                JOIN fakultas f ON m.fakultas_id = f.id
                JOIN program_studi ps ON m.program_studi_id = ps.id
                WHERE u.role = 'mahasiswa';

                --VIEW Dosen
                CREATE VIEW v_dosen AS
                SELECT
                    u.id as user_id,
                    u.nomor_induk,
                    u.nama,
                    u.email,
                    u.no_hp,
                    u.is_active,
                    d.gelar_depan,
                    d.gelar_belakang,
                    CASE
                        WHEN d.gelar_depan IS NOT NULL AND d.gelar_belakang IS NOT NULL THEN
                            CONCAT(d.gelar_depan, ' ', u.nama, ' ', d.gelar_belakang)
                        WHEN d.gelar_depan IS NOT NULL THEN
                            CONCAT(d.gelar_depan, ' ', u.nama)
                        WHEN d.gelar_belakang IS NOT NULL THEN
                            CONCAT(u.nama, ' ', d.gelar_belakang)
                        ELSE u.nama
                    END as nama_lengkap,
                    d.jabatan,
                    f.id as fakultas_id,
                    f.nama_fakultas,
                    d.ttd_path,
                    d.signature_upload_at,
                    u.created_at,
                    u.last_login
                FROM users u
                JOIN dosen d ON u.id = d.user_id
                LEFT JOIN fakultas f ON d.fakultas_id = f.id
                WHERE u.role = 'dosen';

                -- =========================
                -- TRIGGERS untuk updated_at
                -- =========================
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER update_fakultas_updated_at BEFORE UPDATE ON fakultas
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

                CREATE TRIGGER update_program_studi_updated_at BEFORE UPDATE ON program_studi
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

                CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

                CREATE TRIGGER update_permohonan_updated_at BEFORE UPDATE ON permohonan
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

            """
            )

        def downgrade():
            op.execute("DROP VIEW IF EXISTS v_mahasiswa CASCADE;")
            op.execute("DROP VIEW IF EXISTS v_dosen CASCADE;")
            #op.execute("DROP VIEW IF EXISTS v_admin CASCADE;")

        kembali ke cmd lalu masukkan flask db upgrade
