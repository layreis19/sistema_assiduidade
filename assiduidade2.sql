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

-- ============================================================
-- ÍNDICES ADICIONAIS ÚTEIS
-- (id_funcionario, data) em FUNCIONARIO_HORARIO já fica coberto
-- pela UNIQUE acima. Os seguintes aceleram as consultas mais
-- frequentes do dia a dia da aplicação.
-- ============================================================
CREATE INDEX idx_picagem_funcionario_data ON PICAGEM (id_funcionario, data);
CREATE INDEX idx_ausencias_funcionario_periodo ON AUSENCIAS (id_funcionario, data_inicio, data_fim);

-- ============================================================
-- DADOS DE EXEMPLO (opcional — remover em produção)
-- ============================================================
-- INSERT INTO HORARIO (nome, tipo, entrada, saida, inicio_almoco, fim_almoco, tolerancia) VALUES
--     ('Fixo Padrão', 'FIXO', '09:00', '18:00', '13:00', '14:00', 15);
--
-- INSERT INTO HORARIO (nome, tipo, entrada, saida, tolerancia) VALUES
--     ('Turno Manhã', 'TURNO', '08:00', '13:00', 10),
--     ('Turno Tarde',  'TURNO', '13:00', '18:00', 10),
--     ('Turno Noite',  'TURNO', '22:00', '06:00', 10);
--
-- INSERT INTO HORARIO (nome, tipo, janela_inicio, janela_fim, horas_diarias_exigidas) VALUES
--     ('Livre 9-20', 'LIVRE', '09:00', '20:00', 8.00);
--
-- INSERT INTO HORARIO (nome, tipo) VALUES
--     ('Folga', 'FOLGA');