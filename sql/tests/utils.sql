CREATE OR REPLACE FUNCTION create_test_user() RETURNS "user" AS $$
DECLARE
    _user "user";
BEGIN
    INSERT INTO "user" (username, email, name)
    VALUES ('blabla', 'blabla@test.com', 'blabla')
    RETURNING * INTO _user;

    PERFORM set_config('app.current_user_id', _user.id::TEXT, true);

    RETURN _user;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_test_person() RETURNS person AS $$
DECLARE
    _person person;
BEGIN
    INSERT INTO person (type) values ('natural') RETURNING * INTO _person;

    INSERT INTO natural_person_details (person_id, curp, rfc, name, first_last_name, second_last_name, date_of_birth)
    VALUES (_person.id, 'VARD123456AAAAAA12', 'AAAA123456AAA', 'John', 'Doe', 'Smith', '1990-01-01');

    RETURN _person;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_test_blacklist() RETURNS blacklist AS $$
DECLARE
    _blacklist blacklist;
BEGIN
    INSERT INTO blacklist (short_name) VALUES ('test') RETURNING * INTO _blacklist;

    RETURN _blacklist;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION create_test_blacklist_person(_blacklist_id INTEGER) RETURNS blacklist_person AS $$
DECLARE
    blp blacklist_person;
BEGIN
    INSERT INTO blacklist_person (blacklist_id, type, official_registration_number)
    values (_blacklist_id, 'natural', '1234567890')
    RETURNING * INTO blp;

    INSERT INTO blacklist_natural_person_details (id, curp, rfc, name, first_last_name, second_last_name, date_of_birth)
    VALUES (blp.id, 'VARD123456AAAAAA12', 'AAAA123456AAA', 'John', 'Doe', 'Smith', '1990-01-01');

    RETURN blp;
END;
$$ LANGUAGE plpgsql;