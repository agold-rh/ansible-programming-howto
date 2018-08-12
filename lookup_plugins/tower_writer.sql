CREATE FUNCTION tower_writer(the_name VARCHAR, the_data jsonb) RETURNS void AS $$
  INSERT INTO 
    tower
  VALUES(the_name, the_data)
  ON CONFLICT (name)
  DO UPDATE 
  SET jdata = the_data;
$$ LANGUAGE SQL;
