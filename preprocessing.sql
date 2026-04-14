DROP SCHEMA IF EXISTS cyberbullying_motifs CASCADE;
CREATE SCHEMA IF NOT EXISTS cyberbullying_motifs;

CREATE TEMP TABLE majority_calculation AS
WITH remap_severity_and_role AS (
    SELECT
        comments.unit_id,
        anons.*,
        CASE
            WHEN anons.bullying_severity = 'mild'
                THEN 1.0
            WHEN anons.bullying_severity = 'moderate'
                THEN 2.0
            WHEN anons.bullying_severity = 'severe'
                THEN 3.0
            ELSE 1.0
        END AS severity,
        CASE
            WHEN anons.bullying_role = 'non_aggressive_defender'
                THEN anons.bullying_role || ':' || anons.defense_type
            ELSE anons.bullying_role
        END AS role,
        sum(anons.is_cyberbullying::INTEGER)
            OVER (PARTITION BY anons.comment_id)
            AS bullying_votes,
        count(*) OVER (PARTITION BY anons.comment_id) AS number_annotators
    FROM ctsr.mturk.comment_annotations AS anons
    INNER JOIN ctsr.instagram.comments
        ON anons.comment_id = comments.comment_id
    WHERE comments.comment_content <> ''
),

assign_ranks_roles AS (
    SELECT
        *,
        CASE
            WHEN role = 'aggressive_defender'
                THEN 1
            WHEN role = 'non_aggressive_defender:support_of_the_victim'
                THEN 2
            WHEN role = 'non_aggressive_defender:direct_to_the_bully'
                THEN 3
            WHEN role = 'aggressive_victim'
                THEN 4
            WHEN role = 'non_aggressive_victim'
                THEN 5
            WHEN role = 'bully_assistant'
                THEN 6
            WHEN role = 'bully'
                THEN 7
            ELSE 8
        END AS role_over_rule,
        ceil(number_annotators / 2.0) AS majority_vote_required,
        (bullying_votes >= ceil(number_annotators / 2.0)::INTEGER)
            AS is_majority_cyberbullying
    FROM remap_severity_and_role
)

SELECT *
FROM assign_ranks_roles
WHERE is_cyberbullying = is_majority_cyberbullying;


CREATE TEMP TABLE roles_majority AS
WITH count_role_votes AS (
    SELECT
        comment_id,
        is_cyberbullying,
        role,
        role_over_rule,
        count(*) AS role_votes
    FROM majority_calculation
    GROUP BY comment_id, is_cyberbullying, role, role_over_rule
),

dense_rank_role_votes AS (
    SELECT
        *,
        dense_rank()
            OVER (
                PARTITION BY comment_id ORDER BY role_votes DESC, role_over_rule
            )
            AS roles_preferenced
    FROM count_role_votes
)

SELECT *
FROM dense_rank_role_votes
WHERE roles_preferenced = 1;

-- If this query returns any records, there is an issue with 
-- the majority_calculation query.
SELECT comment_id, assignment_id, count(*) AS comment_annotation_count
FROM majority_calculation
GROUP BY comment_id, assignment_id
HAVING count(*) > 1;

-- If this query returns any records, there is an issue with 
-- the roles_majority query.
SELECT comment_id, count(*) AS comment_count
FROM roles_majority
GROUP BY comment_id
HAVING count(*) > 1;

CREATE TEMP TABLE majority_avg_severity AS
SELECT comment_id, avg(severity) AS severity
FROM majority_calculation
GROUP BY comment_id;

DROP TABLE IF EXISTS cyberbullying_motifs.comments;
CREATE TABLE IF NOT EXISTS cyberbullying_motifs.comments AS
SELECT
    comments.*,
    roles_majority.is_cyberbullying,
    roles_majority.role,
    majority_avg_severity.severity
FROM ctsr.instagram.comments
INNER JOIN ctsr.instagram.sessions
    ON comments.unit_id = sessions.unit_id
INNER JOIN roles_majority
    ON comments.comment_id = roles_majority.comment_id
INNER JOIN majority_avg_severity
    ON comments.comment_id = majority_avg_severity.comment_id
WHERE
    comments.comment_content <> ''
    AND sessions.number_of_bully_annotations >= 3;

CREATE TEMP TABLE main_victim_majority AS
WITH merging_main_victim_labels AS (
    SELECT
        unit_id,
        CASE
            WHEN session_main_victim IN ('people_in_picture', 'user')
                THEN 'OP'
            WHEN session_main_victim = 'participants'
                THEN 'Participants'
            ELSE 'NA'
        END AS main_victim
    FROM ctsr.mturk.assignments
),

assign_ranks_to_main_victim AS (
    SELECT
        unit_id,
        main_victim,
        CASE
            WHEN main_victim = 'OP'
                THEN 1
            WHEN main_victim = 'Participants'
                THEN 2
            ELSE 3
        END AS victim_over_rule
    FROM merging_main_victim_labels
),

count_victim_labels AS (
    SELECT unit_id, main_victim, victim_over_rule, count(*) AS victim_count
    FROM assign_ranks_to_main_victim
    GROUP BY unit_id, main_victim, victim_over_rule
),

dense_rank_victims_votes AS (
    SELECT
        *,
        dense_rank()
            OVER (
                PARTITION BY unit_id
                ORDER BY victim_count DESC, victim_over_rule
            )
            AS victim_rank
    FROM count_victim_labels
)

SELECT *
FROM dense_rank_victims_votes
WHERE victim_rank = 1;

-- If this query returns any records, there is an issue with 
-- the main_victim_majority query.
SELECT unit_id, count(*) AS count_sessions
FROM main_victim_majority
GROUP BY unit_id
HAVING count(*) > 1;

DROP TABLE IF EXISTS cyberbullying_motifs.sessions;
CREATE TABLE cyberbullying_motifs.sessions AS
SELECT
    sessions.*,
    main_victim_majority.main_victim
FROM ctsr.instagram.sessions
INNER JOIN main_victim_majority
    ON sessions.unit_id = main_victim_majority.unit_id
WHERE sessions.number_of_bully_annotations >= 3;

DROP TABLE IF EXISTS cyberbullying_motifs.session_digraphs;
CREATE TABLE IF NOT EXISTS cyberbullying_motifs.session_digraphs (
  session_graph_id UUID DEFAULT (gen_random_uuid()),
  unit_id INTEGER NOT NULL,
  serialized_graph BYTEA NOT NULL,
  -- This field can be null because the first node is a
  -- placeholder for the main-vicitm/the initial creation of the post.
  comment_id UUID,
  num_nodes INTEGER NOT NULL DEFAULT 0,
  num_edges INTEGER NOT NULL DEFAULT 0,
  num_bullies INTEGER NOT NULL DEFAULT 0,

  num_victims INTEGER NOT NULL DEFAULT 0,
  num_non_agg_victims INTEGER NOT NULL DEFAULT 0,
  num_agg_victims INTEGER NOT NULL DEFAULT 0,

  num_defenders INTEGER NOT NULL DEFAULT 0,
  num_non_agg_defenders INTEGER NOT NULL DEFAULT 0,
  num_agg_defenders INTEGER NOT NULL DEFAULT 0,

  main_victim_in_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  main_victim_weighted_in_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,

  main_victim_out_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  main_victim_weighted_out_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,

  victim_avg_in_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  victim_avg_weighted_in_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,

  victim_avg_out_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  victim_avg_weighted_out_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,

  victim_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  victim_score_weighted DOUBLE PRECISION NOT NULL DEFAULT 0.0,

  bully_avg_in_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  bully_avg_weighted_in_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,

  bully_avg_out_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  bully_avg_weighted_out_deg DOUBLE PRECISION NOT NULL DEFAULT 0.0,

  bully_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  bully_score_weighted DOUBLE PRECISION NOT NULL DEFAULT 0.0,

  main_victim_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  main_victim_score_weighted DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

DROP TABLE IF EXISTS cyberbullying_motifs.plain_motifs ;
CREATE TABLE IF NOT EXISTS cyberbullying_motifs.plain_motifs (
  plain_motif_id UUID NOT NULL,
  unit_id BIGINT NOT NULL,
  size INTEGER NOT NULL,
  iso_class INTEGER NOT NULL,
  motif_hash TEXT NOT NULL,
  serialized_motif BYTEA NOT NULL
);

DROP TABLE IF EXISTS cyberbullying_motifs.flavored_motifs ;
CREATE TABLE IF NOT EXISTS cyberbullying_motifs.flavored_motifs (
  flavored_motif_id UUID NOT NULL,
  plain_motif_id UUID NOT NULL,
  node_flavor TEXT NOT NULL,
  edge_flavor TEXT NOT NULL,
  motif_hash TEXT NOT NULL,
  serialized_motif BYTEA NOT NULL
);
