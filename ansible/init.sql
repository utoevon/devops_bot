ALTER USER postgres WITH PASSWORD 'P@ssw0rd';
CREATE USER repl_user WITH REPLICATION PASSWORD 'P@ssw0rd';

DROP TABLE IF EXISTS email_addresses;
DROP TABLE IF EXISTS phones;

--email_addresses
CREATE TABLE email_addresses (
    id SERIAL PRIMARY KEY,
    address VARCHAR(100) NOT NULL
);

INSERT INTO email_addresses (address)
VALUES  ('xor_ijibiba5@gmail.com'),
        ('waze_nefiyo15@mail.ru'),
        ('mer_ifukiwu96@gmail.com'),
        ('banib_eseha54@bk.ru'),
        ('mitexaw_uma81@internet.ru'),
        ('mara_hehozu34@yandex.ru'),
        ('test@test.te'),
        ('task@test.local');
--phones

CREATE TABLE phones (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL
);

INSERT INTO phones (phone)
VALUES  ('8(800)5553535'),
        ('+7 (922) 777 66 55'),
        ('+7(234)343-34-34'),
        ('+7(234)353-35-35'),
        ('8(234)3533536'),
        ('8(800)1112233'),
        ('+7 999 888 77 66'),
        ('8(777)3332233'),
        ('+7 999 444 33 22');