CREATE FUNCTION tower_reader(the_name VARCHAR) RETURNS jsonb AS $$
  SELECT jdata FROM tower WHERE name = the_name;
$$ LANGUAGE SQL;
