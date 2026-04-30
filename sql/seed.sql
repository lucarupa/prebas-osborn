-- =====================
-- AGENCIES
-- =====================
INSERT INTO agencies (id, name, type)
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