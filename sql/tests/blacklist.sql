BEGIN;
DO $$
    DECLARE
        _blacklist_person_id INTEGER;
        _blacklist_id INTEGER;
        _user_id INTEGER;
        _person_id INTEGER;
BEGIN
    SELECT id INTO _user_id FROM create_test_user();
    SELECT id INTO _person_id FROM create_test_person();
    SELECT id INTO _blacklist_id FROM create_test_blacklist();
    select id INTO _blacklist_person_id FROM create_test_blacklist_person(_blacklist_id);

    if not exists (select * from blacklist_search where person_id = _person_id and _blacklist_person_id = _blacklist_person_id and match and match_score = 1) then
        raise exception 'Registro en blacklist_search no encontrado';
    end if;
END;
$$;
ROLLBACK;

