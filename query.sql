SELECT
  -- total database size in GB
  (
    SELECT ROUND(SUM(data_length + index_length) / POWER(1024, 3), 2)
      FROM information_schema.TABLES
     WHERE table_schema = DATABASE()
  )                                                          AS DatabaseSizeGB,

  -- overall object count & latest created date
  co_stats.NumObjects,
  co_stats.LatestCreated                                  AS LatestCollectionObjectCreated,

  -- most common cataloger across all objects
  CONCAT_WS(' ', mostcat_ag.FirstName, mostcat_ag.LastName) AS MostCommonCataloger

FROM
  -- aggregate total count & latest create timestamp
  (
    SELECT
      COUNT(*)             AS NumObjects,
      MAX(TimestampCreated) AS LatestCreated
      FROM collectionobject
  ) AS co_stats

  -- find the single CatalogerID with highest object count
  CROSS JOIN (
    SELECT CatalogerID
      FROM collectionobject
     WHERE CatalogerID IS NOT NULL
     GROUP BY CatalogerID
     ORDER BY COUNT(*) DESC
     LIMIT 1
  ) AS mostcat

  -- join back to agent to get the name
  LEFT JOIN agent AS mostcat_ag
    ON mostcat.CatalogerID = mostcat_ag.AgentID;
