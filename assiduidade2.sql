-- ============================================================
-- BASE DE DADOS: ASSIDUIDADE
-- Sistema de controlo de picagens, horários, atrasos e faltas
-- ============================================================
CREATE DATABASE IF NOT EXISTS ASSIDUIDADE2
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE ASSIDUIDADE2;

-- ============================================================
-- HORARIO
-- Guarda todas as definições possíveis de tempo de trabalho:
-- horário fixo, turnos, horário livre (janela + horas exigidas)
-- e folga. Cada tipo usa só o subconjunto de colunas que lhe é
-- relevante, deixando as restantes a NULL.
--
-- Tem de ser criada ANTES de FUNCIONARIOS, porque FUNCIONARIOS
-- tem uma chave estrangeira para esta tabela.
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

INSERT INTO horario (nome, tipo, janela_inicio, janela_fim, horas_diarias_exigidas) VALUES
('LIVRE PADRÃO', 'LIVRE', '09:00:00', '20:00:00', 8.0);

INSERT INTO horario (nome, tipo, entrada, saida, tolerancia) VALUES
('MEIO DIA TARDE', 'TURNO', '13:30:00', '17:30:00', 5),
('MEIO DIA MANHÃ', 'TURNO', '08:30:00', '12:30:00', 5);

INSERT INTO horario (nome, tipo) VALUES ('FOLGA', 'FOLGA');

-- ============================================================
-- FUNCIONARIOS
-- Identidade de cada pessoa, com o horário que lhe está atribuído
-- (coluna "horario", NULL = sem horário atribuído) e a data a
-- partir da qual passa a contar para faltas/atrasos (data_adesao).
--
-- Fase atual: todos os funcionários (ADMIN e COLABORADOR) têm
-- senha, usada para picagem na própria aplicação. Quando o
-- dispositivo remoto de picagem for implementado, os colaboradores
-- passarão a usar um PIN próprio nesse dispositivo.
-- ============================================================
CREATE TABLE FUNCIONARIOS (
    id_funcionario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    tipo ENUM('ADMIN', 'COLABORADOR') NOT NULL,
    senha VARCHAR(255) NULL,
    estado ENUM('ATIVO', 'INATIVO') NOT NULL DEFAULT 'ATIVO',
    data_adesao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    horario INT NULL,

    FOREIGN KEY (horario) REFERENCES HORARIO(id_horario)
);

INSERT INTO funcionarios (nome, tipo, senha) VALUES ('admin', 'ADMIN', '$2b$12$yOTfQ.4LWKNG6A4VrL6ob.SRZYTlsOWnVWIXMiI6fc13WTeYjrhJm');

-- ============================================================
-- PICAGEM
-- Registo efetivo de cada entrada/saída. Só há dois tipos
-- (ENTRADA / SAIDA) — pausas, atrasos e faltas são resolvidos
-- depois, no processamento mensal, a partir destes registos.
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
    tipo ENUM('ENTRADA', 'SAIDA') NOT NULL,

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

-- =============================================================
-- AUSENCIAS
-- Férias, baixas médicas, faltas justificadas, etc. Consultada
-- no cálculo de faltas para não marcar como "falta" quem estava
-- ausente por um motivo aprovado.
-- =============================================================
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
-- (Nota: RESULTADOS.horas_extra_minutos passou a substituir
-- esta tabela — ver decisão anterior. Mantida por agora.)
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

-- ============================================================
-- RESULTADOS
-- Resultado do processamento de cada dia (atraso, horas extra,
-- total trabalhado), para os relatórios lerem diretamente daqui.
-- ============================================================
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
-- Aceleram as consultas mais frequentes do dia a dia da aplicação.
-- ============================================================
CREATE INDEX idx_picagem_funcionario_data ON PICAGEM (id_funcionario, data);
CREATE INDEX idx_ausencias_funcionario_periodo ON AUSENCIAS (id_funcionario, data_inicio, data_fim);