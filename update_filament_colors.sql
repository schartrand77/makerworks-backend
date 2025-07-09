-- 🎨 Assign proper hex codes to filaments based on color_name

UPDATE filaments SET hex = '#000000' WHERE LOWER(color_name) = 'black';
UPDATE filaments SET hex = '#FF0000' WHERE LOWER(color_name) = 'red';
UPDATE filaments SET hex = '#0000FF' WHERE LOWER(color_name) = 'blue';
UPDATE filaments SET hex = '#00FF00' WHERE LOWER(color_name) = 'green';
UPDATE filaments SET hex = '#FFFF00' WHERE LOWER(color_name) = 'yellow';
UPDATE filaments SET hex = '#FFFFFF' WHERE LOWER(color_name) = 'white';
UPDATE filaments SET hex = '#808080' WHERE LOWER(color_name) = 'gray';
UPDATE filaments SET hex = '#00008B' WHERE LOWER(color_name) = 'dark blue';
UPDATE filaments SET hex = '#006400' WHERE LOWER(color_name) = 'dark green';
UPDATE filaments SET hex = '#8B0000' WHERE LOWER(color_name) = 'dark red';
UPDATE filaments SET hex = '#FF8C00' WHERE LOWER(color_name) = 'dark orange';
UPDATE filaments SET hex = '#CCCC00' WHERE LOWER(color_name) = 'dark yellow';
UPDATE filaments SET hex = '#654321' WHERE LOWER(color_name) = 'dark brown';
UPDATE filaments SET hex = '#1C1C1C' WHERE LOWER(color_name) = 'carbon black';
UPDATE filaments SET hex = '#F5F5F5' WHERE LOWER(color_name) = 'clear';

-- optionally set unknowns to a neutral gray
UPDATE filaments
SET hex = '#CCCCCC'
WHERE hex IS NULL OR hex = ''
  AND color_name IS NOT NULL;