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


CREATE OR REPLACE FUNCTION create_test_person(_curp TEXT default 'VARD123456AAAAAA12', _rfc TEXT default 'AAAA123456AAA', _name TEXT default 'John', _first_last_name TEXT default 'Doe', _second_last_name TEXT default 'Smith', _date_of_birth DATE default '1990-01-01'::DATE) RETURNS person AS $$
DECLARE
    _person person;
BEGIN
    INSERT INTO person (type) values ('natural') RETURNING * INTO _person;

    INSERT INTO natural_person_details (person_id, curp, rfc, name, first_last_name, second_last_name, date_of_birth)
    VALUES (_person.id, _curp, _rfc, _name, _first_last_name, _second_last_name, _date_of_birth);

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


CREATE OR REPLACE FUNCTION create_test_blacklist_person(_blacklist_id INTEGER, _curp TEXT default 'VARD123456AAAAAA12', _rfc TEXT default 'AAAA123456AAA', _name TEXT default 'John', _first_last_name TEXT default 'Doe', _second_last_name TEXT default 'Smith', _date_of_birth DATE default '1990-01-01'::DATE) RETURNS blacklist_person AS $$
DECLARE
    blp blacklist_person;
BEGIN
    INSERT INTO blacklist_person (blacklist_id, type, official_registration_number)
    values (_blacklist_id, 'natural', '1234567890')
    RETURNING * INTO blp;

    INSERT INTO blacklist_natural_person_details (id, curp, rfc, name, first_last_name, second_last_name, date_of_birth)
    VALUES (blp.id, _curp, _rfc, _name, _first_last_name, _second_last_name, _date_of_birth);

    RETURN blp;
END;
$$ LANGUAGE plpgsql;
