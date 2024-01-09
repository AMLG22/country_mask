def get_geometries(country_name):
    """
    Get an iterable of Shapely geometries corrresponding to given country.

    """
    # Using the Natural Earth feature interface provided by cartopy.
    # You could use a different source, all you need is the geometries.
    shape_records = Reader(natural_earth(resolution='110m',
                                         category='cultural',
                                         name='admin_0_countries')).records()
    geoms = []
    for country in shape_records:
        if country.attributes['NAME_LONG'] == country_name:
            geoms.append(country.geometry)
    return geoms

def mask_geom(cube, geom):
    # Create a mask for the data
    mask = np.ones(cube.shape, dtype=bool)

    # Create a set of x,y points from the cube
    x, y = np.meshgrid(cube.coord(axis='X').points, cube.coord(axis='Y').points)
    lat_lon_points = np.vstack([x.flat, y.flat])
    points = MultiPoint(lat_lon_points.T)

    # Find all points within the region of interest (a Shapely geometry)
    indices = [i for i, p in enumerate(points.geoms) if geom.contains(p)]

    mask[np.unravel_index(indices, cube.shape)] = False
    #print(mask)

    # Then apply the mask
    if isinstance(cube.data, np.ma.MaskedArray):
        cube.data.mask &= mask
    else:
        cube.data = np.ma.masked_array(cube.data, mask)
    return cube

def mask_shape(cube, geom):
    cnames = [coord.name() for coord in cube.dim_coords]
    if 'grid_latitude' in cnames and 'grid_longitude' in cnames:
        latname = 'grid_latitude'
        lonname = 'grid_longitude'
    elif 'latitude' in cnames and 'longitude' in cnames:
        latname = 'latitude'
        lonname = 'longitude'
    else:
        raise ValueError('unable to find X and Y axis')

    print(latname, lonname)
    
    country_weights = geometry_area_weights(next(cube.slices(
        [latname, lonname])),
        geom, normalize=True)
    country_mask = np.where(country_weights > 0, False, True)
    
    if 'time' in cnames:
        country_mask = country_mask[np.newaxis,:,:]
        country_mask  = np.broadcast_to(country_mask, cube.data.shape)
    cube = mask_cube(cube, country_mask)
    return cube