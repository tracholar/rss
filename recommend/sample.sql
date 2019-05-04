INSERT INTO article_feat (id, y, site)
SELECT  json_extract(evt_attr, '$.article_id') as id,
        if(name='like', 1, -1) as y,
        b.link,
        b.title,
        b.body
FROM article_event a
JOIN article b
ON json_extract(a.evt_attr, '$.article_id')=b.id
WHERE a.name IN ('like', 'hate')
