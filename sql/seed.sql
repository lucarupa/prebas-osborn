CREATE USER defaultuser WITH PASSWORD 'defaultuser123';

CREATE DATABASE asset_db
    WITH
    OWNER = defaultuser;

CREATE TABLE agencies (
    id          VARCHAR(36)  PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    agency_type VARCHAR(50)  DEFAULT 'agency',
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE projects (
    id          VARCHAR(36)  PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    agency_id   VARCHAR(36)  NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    status      VARCHAR(50)  DEFAULT 'active',
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id         VARCHAR(36)  PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    email      VARCHAR(255) NOT NULL UNIQUE,
    role       VARCHAR(50)  NOT NULL,
    agency_id  VARCHAR(36)  REFERENCES agencies(id) ON DELETE SET NULL,
    created_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE assets (
    id              VARCHAR(36)  PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    asset_type      VARCHAR(50)  NOT NULL,
    project_id      VARCHAR(36)  NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agency_id       VARCHAR(36)  NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    created_by      VARCHAR(36)  NOT NULL REFERENCES users(id),
    status          VARCHAR(50)  DEFAULT 'pending_review',
    current_version INTEGER      DEFAULT 1,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_assets_project_id ON assets(project_id);
CREATE INDEX idx_assets_agency_id  ON assets(agency_id);

CREATE TABLE asset_versions (
    id              VARCHAR(36)  PRIMARY KEY,
    asset_id        VARCHAR(36)  NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    version_number  INTEGER      NOT NULL,
    file_url        VARCHAR(500) NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_size_bytes INTEGER,
    notes           TEXT,
    created_by      VARCHAR(36)  NOT NULL REFERENCES users(id),
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_asset_version UNIQUE (asset_id, version_number)
);

CREATE INDEX idx_asset_versions_asset_id ON asset_versions(asset_id);

CREATE TABLE approvals (
    id               VARCHAR(36) PRIMARY KEY,
    asset_version_id VARCHAR(36) NOT NULL REFERENCES asset_versions(id) ON DELETE CASCADE,
    reviewed_by      VARCHAR(36) NOT NULL REFERENCES users(id),
    decision         VARCHAR(50) NOT NULL,
    comment          TEXT,
    created_at       TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_approvals_asset_version_id ON approvals(asset_version_id);
CREATE INDEX idx_approvals_reviewed_by      ON approvals(reviewed_by);

CREATE TABLE comments (
    id               VARCHAR(36) PRIMARY KEY,
    asset_version_id VARCHAR(36) NOT NULL REFERENCES asset_versions(id) ON DELETE CASCADE,
    author_id        VARCHAR(36) NOT NULL REFERENCES users(id),
    body             TEXT        NOT NULL,
    created_at       TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comments_asset_version_id ON comments(asset_version_id);
CREATE INDEX idx_comments_author_id        ON comments(author_id);

-- =====================
-- AGENCIES
-- =====================
INSERT INTO agencies (id, name, agency_type)
VALUES
    ('a1000000-0000-0000-0000-000000000001', 'Creativa Studio', 'agency'),
    ('a2000000-0000-0000-0000-000000000002', 'Freelancer Pro',  'freelancer')
ON CONFLICT (id) DO NOTHING;

-- =====================
-- PROJECTS
-- =====================
INSERT INTO projects (id, name, description, agency_id, status)
VALUES
    (
        'b1000000-0000-0000-0000-000000000001',
        'Campaña Verano 2025',
        'Campaña completa de verano para redes sociales',
        'a1000000-0000-0000-0000-000000000001',
        'active'
    ),
    (
        'b2000000-0000-0000-0000-000000000002',
        'Rebranding Corporativo',
        'Nuevo manual de identidad y piezas institucionales',
        'a2000000-0000-0000-0000-000000000002',
        'active'
    )
ON CONFLICT (id) DO NOTHING;

-- =====================
-- USERS
-- =====================
INSERT INTO users (id, name, email, role, agency_id)
VALUES
    (
        'c1000000-0000-0000-0000-000000000001',
        'Ana Diseñadora',
        'ana@creativastudio.com',
        'designer',
        'a1000000-0000-0000-0000-000000000001'
    ),
    (
        'c2000000-0000-0000-0000-000000000002',
        'Luis Revisor',
        'luis@creativastudio.com',
        'reviewer',
        'a1000000-0000-0000-0000-000000000001'
    ),
    (
        'c3000000-0000-0000-0000-000000000003',
        'Carlos Cliente',
        'carlos@empresa.com',
        'client',
        NULL
    )
ON CONFLICT (id) DO NOTHING;

-- =====================
-- ASSETS
-- =====================
INSERT INTO assets (id, title, description, asset_type, project_id, agency_id, created_by, status, current_version)
VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'Banner Principal Verano',
        'Banner hero para Instagram y Facebook',
        'image',
        'b1000000-0000-0000-0000-000000000001',
        'a1000000-0000-0000-0000-000000000001',
        'c1000000-0000-0000-0000-000000000001',
        'pending_review',
        1
    ),
    (
        'd2000000-0000-0000-0000-000000000002',
        'Video Corporativo',
        'Video de presentación institucional 60 segundos',
        'video',
        'b2000000-0000-0000-0000-000000000002',
        'a2000000-0000-0000-0000-000000000002',
        'c1000000-0000-0000-0000-000000000001',
        'pending_review',
        1
    )
ON CONFLICT (id) DO NOTHING;

-- =====================
-- ASSET VERSIONS
-- =====================
INSERT INTO asset_versions (id, asset_id, version_number, file_url, file_name, file_size_bytes, notes, created_by)
VALUES
    (
        'e1000000-0000-0000-0000-000000000001',
        'd1000000-0000-0000-0000-000000000001',
        1,
        'https://storage.ejemplo.com/assets/banner-verano-v1.jpg',
        'banner-verano-v1.jpg',
        2048000,
        'Primera versión del banner',
        'c1000000-0000-0000-0000-000000000001'
    ),
    (
        'e2000000-0000-0000-0000-000000000002',
        'd2000000-0000-0000-0000-000000000002',
        1,
        'https://storage.ejemplo.com/assets/video-corporativo-v1.mp4',
        'video-corporativo-v1.mp4',
        15360000,
        'Primera versión del video',
        'c1000000-0000-0000-0000-000000000001'
    )
ON CONFLICT (id) DO NOTHING;

-- =====================
-- APPROVALS
-- =====================
INSERT INTO approvals (id, asset_version_id, reviewed_by, decision, comment)
VALUES
    (
        'f1000000-0000-0000-0000-000000000001',
        'e1000000-0000-0000-0000-000000000001',
        'c2000000-0000-0000-0000-000000000002',
        'approved',
        'Se ve muy bien, aprobado para publicar'
    )
ON CONFLICT (id) DO NOTHING;

-- =====================
-- COMMENTS
-- =====================
INSERT INTO comments (id, asset_version_id, author_id, body)
VALUES
    (
        'g1000000-0000-0000-0000-000000000001',
        'e1000000-0000-0000-0000-000000000001',
        'c3000000-0000-0000-0000-000000000003',
        'Me gusta la paleta de colores, pero ajustar el tamaño del texto'
    ),
    (
        'g2000000-0000-0000-0000-000000000002',
        'e2000000-0000-0000-0000-000000000002',
        'c2000000-0000-0000-0000-000000000002',
        'El ritmo del video está bien, revisar el audio al final'
    )
ON CONFLICT (id) DO NOTHING;