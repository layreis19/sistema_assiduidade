-- ============================================================
-- BASE DE DADOS: ASSIDUIDADE
-- Sistema de controlo de picagens, horários, atrasos e faltas
-- ============================================================

CREATE DATABASE IF NOT EXISTS ASSIDUIDADE2;
USE ASSIDUIDADE2;

-- ============================================================
-- FUNCIONARIOS
-- Identidade de cada pessoa. Fase atual: todos os funcionários
-- (ADMIN e COLABORADOR) têm senha, usada para picagem na própria
-- aplicação. Quando o dispositivo remoto de picagem for
-- implementado, os colaboradores passarão a usar um PIN próprio
-- nesse dispositivo, deixando "senha" relevante só para ADMIN
-- (login na aplicação) — não é preciso alterar o esquema para
-- essa transição, só a forma como o campo é usado no código.
-- ============================================================
CREATE TABLE FUNCIONARIOS (
    id_funcionario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo ENUM('ADMIN', 'COLABORADOR') NOT NULL,
    senha VARCHAR(255) NULL,
    estado ENUM('ATIVO', 'INATIVO') NOT NULL DEFAULT 'ATIVO'
);

INSERT INTO funcionarios (nome, tipo, senha) VALUES ('admin', 'ADMIN', '$2b$12$yOTfQ.4LWKNG6A4VrL6ob.SRZYTlsOWnVWIXMiI6fc13WTeYjrhJm');

-- ============================================================
-- HORARIO
-- Guarda todas as definições possíveis de tempo de trabalho:
-- horário fixo, turnos (usados em regime rotativo), horário
-- livre (janela + horas exigidas) e folga. Cada tipo usa só o
-- subconjunto de colunas que lhe é relevante, deixando as
-- restantes a NULL.
-- ============================================================
CREATE TABLE HORARIO (
    id_horario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    tipo ENUM('FIXO', 'TURNO', 'LIVRE', 'FOLGA') NOT NULL,

    -- relevante para FIXO e TURNO
    entrada TIME NULL,
    saida TIME NULL,
    inicio_almoco TIME NULL,
    fim_almoco TIME NULL,
    tolerancia INT DEFAULT 0,          -- minutos de tolerância antes de contar atraso

    -- relevante para LIVRE
    janela_inicio TIME NULL,
    janela_fim TIME NULL,
    horas_diarias_exigidas DECIMAL(4,2) NULL
);

INSERT INTO horario (nome, tipo, entrada, saida, inicio_almoco, fim_almoco, tolerancia) VALUES 
('FIXO PADRÃO', 'FIXO', '08:30:00', '17:30:00', '12:30:00', '13:30:00', 5),
('TURNO MANHÃ', 'TURNO', '06:00:00', '15:00:00', '10:00:00', '11:00:00', 5),
('TURNO TARDE', 'TURNO', '14:00:00', '23:00:00', '18:00:00', '19:00:00', 5),
('TURNO NOITE', 'TURNO', '22:00:00', '07:00:00', '02:00:00', '03:00:00', 5);

INSERT INTO horario (nome, tipo, janela_inicio, jaNela_fim, horas_diarias_exigidas) VALUES
('LIVRE PADRÃO', 'LIVRE', '09:00:00', '20:00:00', 8.0);

INSERT INTO horario (nome, tipo, entrada, saida, tolerancia) VALUES
('MEIO DIA TARDE', 'TURNO', '13:30:00', '17:30:00', 5),
('MEIO DIA MANHÃ', 'TURNO', '08:30:00', '12:30:00', 5);

INSERT INTO horario (nome, tipo) VALUES ('FOLGA', 'FOLGA');
-- ============================================================
-- FUNCIONARIO_HORARIO
-- Liga cada funcionário ao horário que lhe é aplicável num dia
-- específico. Uma linha = um dia. A constraint UNIQUE garante,
-- ao nível da própria base de dados, que nunca existem dois
-- horários diferentes atribuídos ao mesmo funcionário no mesmo
-- dia (elimina qualquer ambiguidade ou sobreposição).
--
-- Para horário fixo/livre, o mesmo id_horario repete-se em
-- várias linhas consecutivas. Para regime rotativo, dias
-- diferentes apontam para HORARIOs do tipo TURNO diferentes.
-- A atribuição em lote (semana, período, padrão repetido) é
-- feita pela aplicação, não pela base de dados.
-- ============================================================
CREATE TABLE FUNCIONARIO_HORARIO (
    id_funcionario_horario INT AUTO_INCREMENT PRIMARY KEY,
    id_funcionario INT NOT NULL,
    id_horario INT NOT NULL,
    data DATE NOT NULL,

    FOREIGN KEY (id_funcionario)
        REFERENCES FUNCIONARIOS(id_funcionario)
        ON DELETE CASCADE,
    FOREIGN KEY (id_horario)
        REFERENCES HORARIO(id_horario),

    UNIQUE (id_funcionario, data)
);

-- ============================================================
-- PICAGEM
-- Registo efetivo de cada entrada/saída. O tipo é explícito
-- (ENTRADA / SAIDA_ALMOCO / VOLTA_ALMOCO / SAIDA) em vez de
-- genérico, para que o cálculo de atraso/falta não dependa de
-- adivinhar o significado pela posição cronológica da picagem.
--
-- Retificações do admin nunca sobrescrevem nem apagam a picagem
-- original: esta é marcada como anulada e uma nova picagem é
-- inserida, ligada à original por picagem_original_id. Isto dá
-- rastreabilidade total para auditoria.
-- ============================================================
CREATE TABLE PICAGEM (
    id_picagem INT AUTO_INCREMENT PRIMARY KEY,
    id_funcionario INT NOT NULL,
    data DATETIME NOT NULL,
    tipo ENUM('ENTRADA', 'SAIDA_ALMOCO', 'VOLTA_ALMOCO', 'SAIDA') NOT NULL,

    anulada BOOLEAN NOT NULL DEFAULT 0,
    picagem_original_id INT NULL,
    id_admin_retificacao INT NULL,
    motivo_retificacao VARCHAR(255) NULL,

    FOREIGN KEY (id_funcionario)
        REFERENCES FUNCIONARIOS(id_funcionario)
        ON DELETE CASCADE,
    FOREIGN KEY (picagem_original_id)
        REFERENCES PICAGEM(id_picagem),
    FOREIGN KEY (id_admin_retificacao)
        REFERENCES FUNCIONARIOS(id_funcionario)
);

-- ============================================================
-- AUSENCIAS
-- Férias, baixas médicas, faltas justificadas, etc. Consultada
-- no cálculo de faltas para não marcar como "falta" quem estava
-- ausente por um motivo aprovado.
-- ============================================================
CREATE TABLE AUSENCIAS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_funcionario INT NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    tipo ENUM('FERIAS', 'BAIXA_MEDICA', 'FALTA_JUSTIFICADA', 'OUTRO') NOT NULL,
    aprovado_por INT NULL,

    FOREIGN KEY (id_funcionario)
        REFERENCES FUNCIONARIOS(id_funcionario)
        ON DELETE CASCADE,
    FOREIGN KEY (aprovado_por)
        REFERENCES FUNCIONARIOS(id_funcionario)
);

-- ============================================================
-- FERIADOS
-- Dias em que a ausência de picagem não deve contar como falta.
-- ============================================================
CREATE TABLE FERIADOS (
    data DATE PRIMARY KEY,
    descricao VARCHAR(100)
);

-- ============================================================
-- HORAS_EXTRA
-- Minutos extra trabalhados por funcionário, por dia.
-- ============================================================
CREATE TABLE HORAS_EXTRA (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_funcionario INT NOT NULL,
    data DATE NOT NULL,
    min_extra INT,

    FOREIGN KEY (id_funcionario)
        REFERENCES FUNCIONARIOS(id_funcionario)
        ON DELETE CASCADE
);


CREATE TABLE RESULTADOS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_funcionario INT NOT NULL,
    data DATE NOT NULL,
    atraso_minutos INT NOT NULL DEFAULT 0,
    horas_extra_minutos INT NOT NULL DEFAULT 0,
    total_minutos_trabalhados INT NOT NULL DEFAULT 0,
    calculado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_funcionario)
        REFERENCES FUNCIONARIOS(id_funcionario)
        ON DELETE CASCADE,

    UNIQUE (id_funcionario, data)
);

-- ============================================================
-- ÍNDICES ADICIONAIS ÚTEIS
-- (id_funcionario, data) em FUNCIONARIO_HORARIO já fica coberto
-- pela UNIQUE acima. Os seguintes aceleram as consultas mais
-- frequentes do dia a dia da aplicação.
-- ============================================================
CREATE INDEX idx_picagem_funcionario_data ON PICAGEM (id_funcionario, data);
CREATE INDEX idx_ausencias_funcionario_periodo ON AUSENCIAS (id_funcionario, data_inicio, data_fim);

