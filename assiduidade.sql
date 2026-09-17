CREATE DATABASE ASSIDUIDADE;

USE ASSIDUIDADE;

CREATE TABLE FUNCIONARIOS (

    id_funcionario INT AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(100) NOT NULL,

    tipo ENUM("ADMIN", "COLABORADOR") NOT NULL,

    senha VARCHAR(255),

    estado ENUM("ATIVO", "INATIVO") NOT NULL DEFAULT "ATIVO"

);


CREATE TABLE PICAGEM (

    id_picagem INT AUTO_INCREMENT PRIMARY KEY,

    id_funcionario INT,

    data DATETIME NOT NULL,

    tipo ENUM("ENTRADA", "SAIDA") NOT NULL,

    FOREIGN KEY(id_funcionario)
        REFERENCES FUNCIONARIOS(id_funcionario)
        ON DELETE CASCADE

);


CREATE TABLE HORAS_EXTRA (

    id INT AUTO_INCREMENT PRIMARY KEY,

    id_funcionario INT,

    min_extra INT,

    FOREIGN KEY(id_funcionario)
        REFERENCES FUNCIONARIOS(id_funcionario)
        ON DELETE CASCADE

);


CREATE TABLE TURNO (

    id_turno INT AUTO_INCREMENT PRIMARY KEY,

    entrada TIME,

    saida TIME,

    tolerancia INT,

    pausa INT

);


CREATE TABLE AUSENCIAS (

    id INT AUTO_INCREMENT PRIMARY KEY,

    id_funcionario INT,

    data_inicio DATE,

    data_fim DATE,

    aprovado_por VARCHAR(100),

    FOREIGN KEY(id_funcionario)
        REFERENCES FUNCIONARIOS(id_funcionario)
        ON DELETE CASCADE

);