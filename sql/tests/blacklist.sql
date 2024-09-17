BEGIN;
DO $$
    DECLARE
        _blacklist_person_id INTEGER;
        _blacklist_id INTEGER;
        _user_id INTEGER;
        _person_id INTEGER;
BEGIN
    INSERT INTO "user" (username, email, name)
    VALUES ('blabla', 'blabla@test.com', 'blabla')
    RETURNING id INTO _user_id;

PERFORM set_config('app.current_user_id', _user_id::TEXT, true);

INSERT INTO person (type) values ('natural') RETURNING id INTO _person_id;

INSERT INTO natural_person_details (person_id, curp, rfc, name, first_last_name, second_last_name, date_of_birth)
VALUES (_person_id, 'VARD123456AAAAAA12', 'AAAA123456AAA', 'John', 'Doe', 'Smith', '1990-01-01');

INSERT INTO blacklist (short_name) VALUES ('test') RETURNING id INTO _blacklist_id;

INSERT INTO blacklist_person (blacklist_id, type, official_registration_number)
values (_blacklist_id, 'natural', '1234567890')
RETURNING id INTO _blacklist_person_id;

INSERT INTO blacklist_natural_person_details (id, curp, rfc, name, first_last_name, second_last_name, date_of_birth)
VALUES (_blacklist_person_id, 'VARD123456AAAAAA12', 'AAAA123456AAA', 'John', 'Doe', 'Smith', '1990-01-01');

if not exists (select * from blacklist_search where person_id = _person_id and _blacklist_person_id = _blacklist_person_id and match and match_score = 1) then
    raise exception 'Registro en blacklist_search no encontrado';
end if;

END;
$$;
ROLLBACK;

