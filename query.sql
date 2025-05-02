SELECT
  DATABASE()                                                       AS DatabaseName,
  (
    SELECT ROUND(SUM(data_length + index_length) / POWER(1024, 3), 2)
    FROM   information_schema.TABLES
    WHERE  table_schema = DATABASE()
  )                                                                 AS DatabaseSizeGB,
  inst.Name                                                        AS InstitutionName,
  d.Name                                                           AS DisciplineName,
#   COALESCE(tt.Trees, '')                                           AS TaxonTrees,
  c.CollectionName,
  COALESCE(co_stats.NumObjects, 0)                                 AS NumCollectionObjects,
  co_stats.LatestCreated                                           AS LatestCollectionObjectCreated,
  CONCAT_WS(' ', cat_ag.FirstName, cat_ag.LastName)                AS MostCommonCataloger
FROM
  collection  AS c
  JOIN discipline    AS d
    ON c.DisciplineID = d.UserGroupScopeId
  LEFT JOIN (
    SELECT
      DisciplineID,
      GROUP_CONCAT(Name ORDER BY Name SEPARATOR ', ')               AS Trees
    FROM
      taxontreedef
    GROUP BY
      DisciplineID
  ) AS tt
    ON d.UserGroupScopeId = tt.DisciplineID
  LEFT JOIN (
    SELECT
      CollectionID,
      COUNT(*)             AS NumObjects,
      MAX(TimestampCreated) AS LatestCreated
    FROM
      collectionobject
    GROUP BY
      CollectionID
  ) AS co_stats
    ON c.UserGroupScopeId = co_stats.CollectionID
  LEFT JOIN (
    SELECT CollectionID, CatalogerID
    FROM  (
      SELECT
        CollectionID,
        CatalogerID,
        ROW_NUMBER() OVER (
          PARTITION BY CollectionID
          ORDER BY COUNT(*) DESC
        ) AS rn
      FROM
        collectionobject
      WHERE
        CatalogerID IS NOT NULL
      GROUP BY
        CollectionID, CatalogerID
    ) AS ranked
    WHERE rn = 1
  ) AS mostcat
    ON c.UserGroupScopeId = mostcat.CollectionID
  LEFT JOIN agent AS cat_ag
    ON mostcat.CatalogerID = cat_ag.AgentID
  JOIN division   AS dv
    ON d.DivisionID = dv.UserGroupScopeId
  JOIN institution AS inst
    ON dv.InstitutionID = inst.UserGroupScopeId
ORDER BY
  inst.Name,
  d.Name,
  c.CollectionName;
