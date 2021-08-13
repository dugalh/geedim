# geedim
Google Earth Engine image masking, compositing and download/export.
## Description
`geedim` provides a command line interface, and API, for downloading and exporting surface reflectance imagery from [Google Earth Engine](https://signup.earthengine.google.com) (GEE). 

Functionality:

- Filtering by date & region
- Filtering by region-limited validity and quality scores
- Basic cloud and shadow masking, and cloud-free compositing 
- Download, and export to Google Drive
- Populating image metadata

Supported imagery:

`geedim` Name | GEE Collection| Description
---------|-----------|------------
landsat7_c2_l2 | [LANDSAT/LE07/C02/T1_L2](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LE07_C02_T1_L2) | Landsat 7, collection 2, tier 1, level 2 surface reflectance 
landsat8_c2_l2 | [LANDSAT/LC08/C02/T1_L2](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2) | Landsat 8, collection 2, tier 1, level 2 surface reflectance 
sentinel2_toa | [COPERNICUS/S2](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2) | Sentinel-2, level 1C, top of atmosphere reflectance 
sentinel2_sr | [COPERNICUS/S2_SR](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR) | Sentinel-2, level 2A, surface reflectance
modis_nbar | [MODIS/006/MCD43A4](https://developers.google.com/earth-engine/datasets/catalog/MODIS_006_MCD43A4) | MODIS nadir BRDF adjusted reflectance


## Installation
### `conda`
1) Create a conda environment and install dependencies:
```shell
conda create -n <environment name> python=3.8 -c conda-forge 
conda activate <environment name> 
conda install -c conda-forge rasterio pandas click  earthengine-api
````
2) Clone the git repository and link into the conda environment:
``` shell
git clone https://github.com/dugalh/geedim.git
pip install -e geedim
```
3) Authenticate Earth Engine
``` shell
earthengine authenticate
```
### Requirements  
The following dependencies are installed in the process above.
  
  - python >= 3.8
  - rasterio >= 1.2
  - pandas >= 1.2
  - earthengine-api >= 0.1
 
## Usage
### Command line interface
```
geedim --help
```
```
Usage: geedim [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  download  Download image(s), with cloud and shadow masking
  export    Export image(s) to Google Drive, with cloud and shadow masking
  search    Search for images
```
### Search
```
geedim search --help
```
```
Usage: geedim search [OPTIONS]

  Search for images

Options:
  -c, --collection [landsat7_c2_l2|landsat8_c2_l2|sentinel2_toa|sentinel2_sr|modis_nbar]
                                  Earth Engine image collection to search.
                                  [required]

  -s, --start-date [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  Start date (UTC).  [required]
  -e, --end-date [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  End date (UTC).   [default: start_date + 1
                                  day]

  -b, --bbox FLOAT...             Region defined by bounding box co-ordinates
                                  in WGS84 (xmin, ymin, xmax, ymax).  [One of
                                  --bbox or --region is required.]

  -r, --region FILE               Region defined by geojson or raster file.
                                  [One of --bbox or --region is required.]

  -vp, --valid-portion FLOAT RANGE
                                  Lower limit of the portion of valid (cloud
                                  and shadow free) pixels (%).

  -o, --output FILE               Write results to this filename, file type
                                  inferred from extension: [.csv|.json]

  -rb, --region_buf FLOAT         If --region is a raster file, extend the
                                  region bounds by region_buf %  [default: 5]

  --help                          Show this message and exit.
```
#### Example
```
geedim search -c landsat8_c2_l2 -b 23.9 -33.6 24 -33.5 -s 2019-01-01 -e 2019-02-01
```

### Download
```
geedim download --help
```
```
Usage: geedim download [OPTIONS]

  Download image(s) (up to 10MB), with cloud and shadow masking

Options:
  -i, --id TEXT                   Earth engine image ID(s).  [required]
  -b, --bbox FLOAT...             Region defined by bounding box co-ordinates
                                  in WGS84 (xmin, ymin, xmax, ymax).  [One of
                                  --bbox or --region is required.]

  -r, --region FILE               Region defined by geojson or raster file.
                                  [One of --bbox or --region is required.]

  -dd, --download-dir DIRECTORY   Download image file(s) to this directory
                                  [default:
                                  C:\Data\Development\Projects\geedim]

  -c, --crs TEXT                  Reproject image(s) to this CRS (WKT or EPSG
                                  string).  [default: source CRS]

  -s, --scale FLOAT               Resample image bands to this pixel
                                  resolution (m).  [default: minimum of the
                                  source band resolutions]

  -m, --mask / -nm, --no-mask     Do/don't apply (cloud and shadow) nodata
                                  mask(s).  [default: no-mask]

  -sr, --scale-refl / -nsr, --no-scale-refl
                                  Scale reflectance bands from 0-10000.
                                  [default: scale-refl]

  -o, --overwrite                 Overwrite the destination file if it exists.
                                  [default: prompt the user for confirmation]

  --help                          Show this message and exit.
  ```
#### Example
```
geedim download -i LANDSAT/LC08/C02/T1_L2/LC08_172083_20190128 -b 23.9 -33.6 24 -33.5 --scale-refl --mask
```

### Export
```
geedim export --help
```
```
Usage: geedim export [OPTIONS]

  Export image(s) to Google Drive, with cloud and shadow masking

Options:
  -i, --id TEXT                   Earth engine image ID(s).  [required]
  -b, --bbox FLOAT...             Region defined by bounding box co-ordinates
                                  in WGS84 (xmin, ymin, xmax, ymax).  [One of
                                  --bbox or --region is required.]

  -r, --region FILE               Region defined by geojson or raster file.
                                  [One of --bbox or --region is required.]

  -df, --drive-folder TEXT        Export image(s) to this Google Drive folder.
                                  [default: root]

  -c, --crs TEXT                  Reproject image(s) to this CRS (WKT or EPSG
                                  string).  [default: source CRS]

  -s, --scale FLOAT               Resample image bands to this pixel
                                  resolution (m).  [default: minimum of the
                                  source band resolutions]

  -m, --mask / -nm, --no-mask     Do/don't apply (cloud and shadow) nodata
                                  mask(s).  [default: no-mask]

  -sr, --scale-refl / -nsr, --no-scale-refl
                                  Scale reflectance bands from 0-10000.
                                  [default: scale-refl]

  -w, --wait / -nw, --no-wait     Wait / don't wait for export to complete.
                                  [default: wait]

  --help                          Show this message and exit.
```
#### Example
```
geedim export -i LANDSAT/LC08/C02/T1_L2/LC08_172083_20190128 -b 23.9 -33.6 24 -33.5 -df geedim_test --scale-refl --mask
```
## Known limitations
- GEE limits image downloads to 10MB, images larger than this can exported to Google Drive.
- There is a [GEE bug exporting MODIS in its native CRS](https://issuetracker.google.com/issues/194561313), `geedim` works around this by re-projecting MODIS to spherical-mercator if no other CRS is specified.

## License
This project is licensed under the terms of the [Apache-2.0 License](LICENSE).

## Contributing
Constributions are welcome.  Please post bugs and questions with the [github issue tracker](https://github.com/dugalh/geedim/issues).

## Author
**Dugal Harris** - [dugalh@gmail.com](mailto:dugalh@gmail.com)

## Credits
- Portions of the compositing code were adapted from [gee_tools](https://github.com/gee-community/gee_tools) under the terms of the [MIT license](https://github.com/gee-community/gee_tools/blob/master/LICENSE).
- [landsatxplore](https://github.com/yannforget/landsatxplore) gave a starting point for the command line interface.  