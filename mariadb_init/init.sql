CREATE DATABASE IF NOT EXISTS movies_db;

USE movies_db;

CREATE TABLE IF NOT EXISTS directors(
    name varchar(20) PRIMARY KEY,
    age int NOT NULL CHECK (age > 0)
);


CREATE TABLE IF NOT EXISTS movies(
    id int AUTO_INCREMENT PRIMARY KEY,
    title varchar(50) NOT NULL,
    director varchar(20) NOT NULL,
    year int NOT NULL CHECK (year>1900),
    genre varchar(15) NOT NULL,
    FOREIGN KEY (director) REFERENCES directors(name)
);


CREATE TABLE IF NOT EXISTS platform_availability (
    movie_id int,
    platform varchar(20),
    PRIMARY KEY (movie_id, platform),
    FOREIGN KEY (movie_id) REFERENCES movies(id)
);




