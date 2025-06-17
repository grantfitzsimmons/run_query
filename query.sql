SELECT
  -- current database name
  DATABASE()                                                           AS DatabaseName,

  -- total database size in GB
  (
    SELECT ROUND(SUM(data_length + index_length) / POWER(1024, 3), 2)
      FROM information_schema.TABLES
     WHERE table_schema = DATABASE()
  )                                                                    AS DatabaseSizeGB,

  inst.Name                                                            AS InstitutionName,
  d.Name                                                               AS DisciplineName,

  -- comma-separated list of collections with their object counts
  GROUP_CONCAT(
    CONCAT(
      c.CollectionName,
      ' (',
      COALESCE(co_stats.NumObjects, 0),
      ')'
    )
    ORDER BY c.CollectionName
    SEPARATOR ', '
  )                                                                    AS Collections

FROM
  collection   AS c
  JOIN discipline AS d
    ON c.DisciplineID = d.UserGroupScopeId

  -- link discipline → division → institution
  JOIN division    AS dv
    ON d.DivisionID = dv.UserGroupScopeId
  JOIN institution AS inst
    ON dv.InstitutionID = inst.UserGroupScopeId

  -- per-collection object counts
  LEFT JOIN (
    SELECT
      CollectionID,
      COUNT(*) AS NumObjects
    FROM
      collectionobject
    GROUP BY
      CollectionID
  ) AS co_stats
    ON c.UserGroupScopeId = co_stats.CollectionID

GROUP BY
  inst.Name,
  d.Name

ORDER BY
  inst.Name,
  d.Name;
