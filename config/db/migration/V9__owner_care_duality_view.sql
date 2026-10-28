CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW OWNER_CARE_DV AS
SELECT JSON {
    '_id': o.ID,
    'firstName': o.FIRST_NAME,
    'lastName': o.LAST_NAME,
    'address': o.ADDRESS,
    'city': o.CITY,
    'telephone': o.TELEPHONE,
    'pets': [
        SELECT JSON {
            'id': p.ID,
            'name': p.NAME,
            'birthDate': p.BIRTH_DATE,
            'visits': [
                SELECT JSON {
                    'id': v.ID,
                    'date': v.VISIT_DATE,
                    'description': v.DESCRIPTION
                }
                FROM VISITS v WITH UPDATE
                WHERE p.ID = v.PET_ID
            ]
        }
        FROM PETS p WITH UPDATE
        WHERE o.ID = p.OWNER_ID
    ]
}
FROM OWNERS o WITH UPDATE;
