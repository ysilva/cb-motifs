SELECT unit_id, array_agg(session_main_victim) AS main_victim
FROM mturk.assignments
GROUP BY unit_id;

SELECT 
  cmnts.unit_id,
  cmnts.comment_id,
  array_agg(anons.main_victim) AS is_cyberbullying,
  array_agg(anons.is_cyberbullying) AS is_cyberbullying,
  array_agg(anons.bullying_role) AS bullying_role,
  array_agg(anons.bullying_severity) AS bullying_severity
FROM mturk.comment_annotations AS anons
INNER JOIN instagram.comments AS cmnts
  ON anons.comment_id = cmnts.comment_id
GROUP BY cmnts.unit_id, cmnts.comment_id;
