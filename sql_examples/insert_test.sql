USE mycluster;

SELECT * FROM actor ORDER BY actor_id DESC LIMIT 10;

INSERT INTO actor(first_name, last_name) VALUES ("EMMA", "WATSON"), ("SCARLETT", "JOHANSSON");

SELECT * FROM actor ORDER BY actor_id DESC LIMIT 10;
