# Verification Guide: Graph Updates

Use this guide to verify that your image uploads are correctly updating the Survivor Network graph in Spanner.

## General Diagnostics

### 1. Check Broadcast Processing (SQL)
To see if the system processed the image at all:
```sql
SELECT b.broadcast_id, b.title, b.processed, s.name as survivor
FROM Broadcasts b
LEFT JOIN Survivors s ON b.survivor_id = s.survivor_id
ORDER BY b.created_at DESC
LIMIT 5;
```

---

## Scenario 1: David Chen's Field Report
**Image:** `survivor_field_report_diary.png` (Handwritten note about Energy Crystal)

### Verify New Resource (SQL)
```sql
SELECT * FROM Resources 
WHERE name LIKE '%Crystal%' 
ORDER BY resource_id DESC;
```

### Verify Graph Connections (GQL)
**Query:** Did David find the crystal?
```sql
GRAPH SurvivorGraph
MATCH (s:Survivor {name: "David Chen"})-[f:FOUND]->(r:Resource)
RETURN s.name AS survivor, f.found_at, r.name AS resource, r.type
```

**Query:** Is David in the correct biome?
```sql
GRAPH SurvivorGraph
MATCH (s:Survivor {name: "David Chen"})-[i:IN_BIOME]->(b:Biome)
RETURN s.name AS survivor, b.name AS location
```

---

## Scenario 2: Yuki Tanaka's Log Entry
**Image:** `yuki_tanaka_volcanic_log.png` (Datapad log finding Geothermal Vent)

### Verify Resource Discovery (GQL)
**Query:** Did Yuki find the Geothermal resource?
```sql
GRAPH SurvivorGraph
MATCH (s:Survivor {name: "Captain Yuki Tanaka"})-[f:FOUND]->(r:Resource)
WHERE r.name LIKE "%Geothermal%"
RETURN s.name AS survivor, r.name AS resource, f.found_at
```

---

## Scenario 3: Elena Frost's Body Cam
**Image:** `elena_frost_cryo_bodycam.png` (Scanner view in Ice Cave)

### Verify Biome Update (GQL)
**Query:** Is Elena located in the Cryo biome?
```sql
GRAPH SurvivorGraph
MATCH (s:Survivor {name: "Dr. Elena Frost"})-[i:IN_BIOME]->(b:Biome)
WHERE b.name LIKE "%Cryo%"
RETURN s.name AS survivor, b.name AS location
```