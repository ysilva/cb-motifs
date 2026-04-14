DROP VIEW IF EXISTS cyberbullying_motifs.session_digraphs_complete;
CREATE VIEW cyberbullying_motifs.session_digraphs_complete AS
SELECT
  graphs.*,
  sessions.session_posted_at,
  cmnts.is_cyberbullying,
  cmnts.severity,
  cmnts.role,
  coalesce(cmnts.comment_created_at, sessions.session_posted_at) AS created_at,
  (row_number() OVER (PARTITION BY graphs.unit_id ORDER BY coalesce(cmnts.comment_created_at, sessions.session_posted_at) DESC NULLS LAST) = 1) AS is_complete_graph
FROM cyberbullying_motifs.session_digraphs AS graphs
LEFT JOIN cyberbullying_motifs.comments AS cmnts
 ON cmnts.comment_id = graphs.comment_id
LEFT JOIN cyberbullying_motifs.sessions AS sessions
 ON sessions.unit_id = graphs.unit_id;

