SELECT
  -- current database name
  DATABASE()                                                         AS DatabaseName,

  -- total database size in GB
  (
    SELECT ROUND(SUM(data_length + index_length) / POWER(1024,3), 2)
      FROM information_schema.TABLES
     WHERE table_schema = DATABASE()
  )                                                                   AS DatabaseSizeGB,

  inst.Name                                                           AS InstitutionName,

  -- comma‐separated list of all disciplines for this institution
  GROUP_CONCAT(
    DISTINCT d.Name
    ORDER BY d.Name
    SEPARATOR ', '
  )                                                                   AS Disciplines,

  -- comma‐separated list of all collections (with counts) for this institution
  GROUP_CONCAT(
    DISTINCT CONCAT(
      c.CollectionName,
      ' (',
      COALESCE(cs.NumObjects, 0),
      ')'
    )
    ORDER BY c.CollectionName
    SEPARATOR ', '
  )                                                                   AS Collections

FROM
  institution AS inst

  -- institution → division → discipline → collection
  JOIN division    AS dv
    ON dv.InstitutionID = inst.UserGroupScopeId
  JOIN discipline  AS d
    ON d.DivisionID = dv.UserGroupScopeId
  LEFT JOIN collection AS c
    ON c.DisciplineID = d.UserGroupScopeId

  -- per‐collection object counts
  LEFT JOIN (
    SELECT
      CollectionID,
      COUNT(*) AS NumObjects
    FROM collectionobject
    GROUP BY CollectionID
  ) AS cs
    ON cs.CollectionID = c.UserGroupScopeId

GROUP BY
  inst.Name

ORDER BY
  inst.Name;
