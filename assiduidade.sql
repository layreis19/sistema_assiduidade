CREATE DATABASE ASSIDUIDADE;
USE ASSIDUIDADE;

CREATE TABLE FUNCIONARIOS (
id_funcionario INT auto_increment primary key,
nome VARCHAR(100) NOT NULL,
tipo ENUM("ADMIN", "COLABORADOR") NOT NULL
);

CREATE TABLE  PICAGEM(
id_picagem INT AUTO_INCREMENT primary KEY,
id_funcionario INT,
data datetime NOT NULL,
tipo ENUM("ENTRADA", "SAIDA") NOT NULL,
FOREIGN KEY(id_funcionario) REFERENCES funcionarios(id_funcionario)
);

CREATE TABLE HORAS_EXTRA (
id INT AUTO_INCREMENT primary key,
id_funcionario INT,
min_extra INT,
FOREIGN KEY(id_funcionario) REFERENCES funcionarios(id_funcionario)
);

CREATE TABLE TURNO (
id_turno INT auto_increment primary KEY,
entrada TIME,
saida time,
tolerancia int,
pausa int);

CREATE TABLE AUSENCIAS (
id INT auto_increment primary key,
id_funcionario int,
data_inicio date,
data_fim date,
aprovado_por VARCHAR(100),
foreign key(id_funcionario) references funcionarios(id_funcionario)
);

